import os
import sys
import uuid
import json
import tempfile
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from parsers.document_parser import extract_text, extract_text_from_content, clean_extracted_text
from agents.orchestrator import AgentOrchestrator

app = Flask(__name__)
allowed_origins = list(dict.fromkeys([
    *config.CORS_ORIGINS,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]))
CORS(app, origins=allowed_origins)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

# in-memory document store (replace with postgres in production)
document_store = {}

# initialize orchestrator once at startup
orchestrator = AgentOrchestrator()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def map_risk_level(score_or_level):
    # normalize risk level to low/medium/high for frontend compatibility
    if isinstance(score_or_level, str):
        level = score_or_level.lower()
        if level in ("critical",):
            return "high"
        return level if level in ("low", "medium", "high") else "medium"
    score = int(score_or_level)
    if score <= 35:
        return "low"
    elif score <= 65:
        return "medium"
    return "high"


def build_document_response(doc_id, filename, size, analysis_result):
    # shapes the analysis into the api response format the frontend expects
    summary_data = analysis_result.get("summary", {})
    risk_scores = analysis_result.get("risk_scores", {})
    red_flags = analysis_result.get("red_flags", [])
    green_flags = analysis_result.get("green_flags", [])
    obligations = analysis_result.get("obligations", [])
    comparisons = analysis_result.get("comparisons", [])
    negotiations = analysis_result.get("negotiations", [])

    overall_score = risk_scores.get("overall_score", 50)
    risk_level = map_risk_level(analysis_result.get("risk_level", "medium"))

    # merge red flags, green flags and dimension scores into unified risks list for frontend
    risks = []
    for rf in red_flags:
        risks.append({
            "title": rf.get("title", "Risk Detected"),
            "severity": rf.get("severity", "medium"),
            "detail": rf.get("detail", ""),
            "excerpt": rf.get("excerpt", ""),
            "category": rf.get("category", ""),
            "recommendation": rf.get("recommendation", ""),
            "type": "red_flag"
        })
    for gf in green_flags:
        risks.append({
            "title": gf.get("title", "Protective Clause"),
            "severity": "low",
            "detail": gf.get("detail", ""),
            "excerpt": gf.get("excerpt", ""),
            "category": gf.get("category", ""),
            "strength": gf.get("strength", "moderate"),
            "type": "green_flag"
        })

    return {
        "id": doc_id,
        "filename": filename,
        "size": size,
        "documentType": summary_data.get("document_type", "other"),
        "summary": summary_data.get("summary", ""),
        "riskLevel": risk_level,
        "overallScore": overall_score,
        "riskScores": {
            "dimensions": risk_scores.get("dimensions", []),
            "explanation": risk_scores.get("score_explanation", ""),
            "criticalFindings": risk_scores.get("critical_findings", [])
        },
        "risks": risks,
        "redFlags": red_flags,
        "greenFlags": green_flags,
        "obligations": [
            {
                "party": o.get("party", "Party"),
                "action": o.get("action", ""),
                "timing": o.get("timing", ""),
                "status": o.get("status", "defined"),
                "consequence": o.get("consequence", ""),
                "section": o.get("section", "")
            }
            for o in obligations
        ],
        "comparisons": comparisons,
        "negotiations": negotiations,
        "keyTerms": summary_data.get("key_terms", []),
        "parties": summary_data.get("parties", []),
        "agentsCompleted": analysis_result.get("agents_completed", []),
        "executionLog": analysis_result.get("execution_log", []),
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.route("/api/healthz", methods=["GET"])
def health():
    stats = orchestrator.retriever.stats
    return jsonify({
        "status": "ok",
        "knowledge_base": stats,
        "models": {
            "embedding": config.EMBEDDING_MODEL,
            "llm": config.LLM_MODEL,
            "reranker": config.RERANKER_MODEL
        }
    })


@app.route("/api/documents", methods=["GET"])
def list_documents():
    docs = list(document_store.values())
    # return most recent first
    docs.sort(key=lambda d: d.get("createdAt", ""), reverse=True)
    return jsonify(docs)


@app.route("/api/documents/summary", methods=["GET"])
def document_summary():
    docs = list(document_store.values())
    total = len(docs)
    high_risk = sum(1 for d in docs if d.get("riskLevel") == "high")

    from datetime import datetime, timedelta
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    this_week = sum(1 for d in docs if d.get("createdAt", "") >= week_ago.strftime("%Y-%m-%d"))

    total_chars = sum(d.get("size", 0) for d in docs)
    avg_chars = total_chars / total if total > 0 else 0
    avg_read_time = max(1, round(avg_chars / 1200))

    return jsonify({
        "total": total,
        "highRisk": high_risk,
        "thisWeek": this_week,
        "averageReadTime": avg_read_time
    })


@app.route("/api/documents", methods=["POST"])
def analyze_document():
    # handles both file upload and text content submission
    text = None
    filename = "document.txt"
    size = 0

    if request.content_type and "multipart/form-data" in request.content_type:
        # file upload path
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"}), 400

        filename = file.filename
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            text = extract_text(tmp_path)
            size = os.path.getsize(tmp_path)
        finally:
            os.unlink(tmp_path)

    else:
        # json body path (matches existing frontend api shape)
        body = request.get_json(silent=True) or {}
        content = body.get("content", "")
        filename = body.get("filename", "document.txt")
        size = body.get("size", len(content.encode("utf-8")))

        if not content:
            return jsonify({"error": "No document content provided"}), 400

        text = extract_text_from_content(content, filename)

    if not text or len(text.strip()) < 20:
        return jsonify({"error": "Could not extract readable text from document"}), 422

    text = clean_extracted_text(text)

    # run agentic rag pipeline
    try:
        analysis = orchestrator.analyze_document(text, filename)
    except Exception as err:
        return jsonify({"error": f"Analysis failed: {str(err)}"}), 500

    doc_id = str(uuid.uuid4())
    response = build_document_response(doc_id, filename, size, analysis)
    document_store[doc_id] = response

    return jsonify(response), 201


@app.route("/api/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    doc = document_store.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(doc)


@app.route("/api/documents/<doc_id>/reanalyze", methods=["POST"])
def reanalyze_document(doc_id):
    # re-runs analysis on an already-stored document
    doc = document_store.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"message": "Reanalysis would require the original document text."}), 400


if __name__ == "__main__":
    # auto-build knowledge base if it doesn't exist yet
    if not os.path.exists(os.path.join(config.FAISS_INDEX_PATH, "index.faiss")):
        print("Knowledge base not found. Building now...")
        try:
            from scraper.build_knowledge_base import build
            build()
        except Exception as err:
            print(f"Warning: Could not build knowledge base: {err}")
            print("The app will still work with reduced context quality.")

    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
