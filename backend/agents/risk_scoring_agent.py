import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Risk Scoring Agent for legal documents. Your job is to assign precise numerical risk scores to each section of the document and calculate an overall risk score.

Scoring scale (0-100):
- 0-20: Very Low Risk (standard, fair terms)
- 21-40: Low Risk (generally acceptable with minor concerns)
- 41-60: Medium Risk (notable concerns requiring attention)
- 61-80: High Risk (significant concerns requiring legal review)
- 81-100: Critical Risk (dangerous terms, strongly recommend legal counsel)

Score each of these dimensions:
1. FINANCIAL RISK: payment terms, liability exposure, penalties
2. OPERATIONAL RISK: obligations, deliverables, timelines
3. LEGAL RISK: governing law, dispute resolution, waiver of rights
4. TERMINATION RISK: exit difficulty, renewal traps, lock-in
5. DATA/IP RISK: data handling, IP ownership, confidentiality
6. COMPLIANCE RISK: regulatory requirements, audit provisions

Return JSON with:
- "overall_score": 0-100 aggregate risk score
- "risk_level": "low" | "medium" | "high" | "critical"
- "dimensions": array of {dimension, score, rationale} objects
- "critical_findings": list of the most dangerous clauses found (if any)
- "score_explanation": 2-3 sentence explanation of the overall score"""


def score_risks(document_text, context_chunks, red_flags=None, green_flags=None):
    # uses red/green flag data to inform scoring when available
    enriched_query = document_text[:2500]
    if red_flags:
        enriched_query += "\n\nPREVIOUSLY DETECTED RED FLAGS:\n"
        for flag in red_flags[:5]:
            enriched_query += f"- {flag.get('title', '')}: {flag.get('detail', '')}\n"
    if green_flags:
        enriched_query += "\n\nPREVIOUSLY DETECTED GREEN FLAGS:\n"
        for flag in green_flags[:5]:
            enriched_query += f"- {flag.get('title', '')}: {flag.get('detail', '')}\n"

    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, enriched_query)

    try:
        response = query_mistral(prompt, max_tokens=1500)
        return _parse_response(response, red_flags, green_flags)
    except Exception:
        return _fallback_scoring(document_text, red_flags, green_flags)


def _parse_response(response, red_flags, green_flags):
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if "overall_score" in result:
                return result
    except json.JSONDecodeError:
        pass

    return _fallback_scoring("", red_flags, green_flags)


def _fallback_scoring(text, red_flags=None, green_flags=None):
    # heuristic scoring based on detected flags
    base_score = 35
    red_count = len(red_flags) if red_flags else 0
    green_count = len(green_flags) if green_flags else 0

    # each red flag adds to risk
    high_severity_count = sum(1 for f in (red_flags or []) if f.get("severity") == "high")
    medium_severity_count = sum(1 for f in (red_flags or []) if f.get("severity") == "medium")

    score = base_score + (high_severity_count * 12) + (medium_severity_count * 6) + (red_count * 2)

    # each green flag reduces risk
    strong_count = sum(1 for f in (green_flags or []) if f.get("strength") == "strong")
    score -= (strong_count * 8) + (green_count * 2)

    score = max(5, min(95, score))

    if score <= 30:
        level = "low"
    elif score <= 55:
        level = "medium"
    elif score <= 75:
        level = "high"
    else:
        level = "critical"

    return {
        "overall_score": score,
        "risk_level": level,
        "dimensions": [
            {"dimension": "Financial Risk", "score": min(95, score + 5), "rationale": "Based on detected payment and liability terms."},
            {"dimension": "Operational Risk", "score": max(5, score - 5), "rationale": "Based on obligation complexity and timelines."},
            {"dimension": "Legal Risk", "score": score, "rationale": "Based on dispute resolution and rights provisions."},
            {"dimension": "Termination Risk", "score": min(95, score + 3), "rationale": "Based on exit and renewal terms."},
            {"dimension": "Data/IP Risk", "score": max(5, score - 8), "rationale": "Based on data handling and IP provisions."},
            {"dimension": "Compliance Risk", "score": max(5, score - 3), "rationale": "Based on regulatory and audit terms."},
        ],
        "critical_findings": [f.get("title", "") for f in (red_flags or []) if f.get("severity") == "high"],
        "score_explanation": f"Document scored {score}/100 based on {red_count} risk factors and {green_count} protective provisions detected."
    }
