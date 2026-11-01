import os
import sys
import json
import time

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import config
from parsers.document_parser import extract_text, clean_extracted_text
from agents.orchestrator import AgentOrchestrator

import gradio as gr

# Initialize orchestrator once on boot
orchestrator = AgentOrchestrator()

SAMPLE_CONTRACT = """NON-DISCLOSURE AND SERVICE AGREEMENT
This Agreement is entered into between Company Alpha ("Client") and Contractor Beta ("Provider").

1. TERM AND AUTOMATIC RENEWAL:
This Agreement commences on November 1, 2026 and shall automatically renew for successive one-year terms indefinitely unless terminated by Client with at least 90 days prior written notice before the expiration of the current term.

2. UNLIMITED LIABILITY AND INDEMNIFICATION:
Provider shall have unlimited aggregate liability for any and all claims, damages, or disputes arising out of this Agreement. In no event shall Client's liability exceed the total amount of $100. Provider agrees to indemnify, defend, and hold harmless Client against all third-party claims without limitation.

3. NON-COMPETE RESTRICTIONS:
During the term of this Agreement and for a period of 36 months following termination, Provider shall not engage in any competitive business activity, directly or indirectly, anywhere globally.

4. PAYMENT AND DELIVERABLES:
Provider must deliver comprehensive milestone reports within 5 business days of each month-end. Client shall remit payment within 45 days of receiving verified invoices.

5. TERMINATION FOR CAUSE:
Either party may terminate this Agreement immediately upon written notice if the other party commits a material breach.

6. GOVERNING LAW AND ARBITRATION:
This Agreement shall be governed by the laws of India, including the Indian Contract Act 1872. All disputes shall be settled through binding arbitration in Mumbai."""


def analyze_contract(file_obj, raw_text, progress=gr.Progress()):
    filename = "pasted_contract.txt"
    text = ""

    if file_obj is not None:
        file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        filename = os.path.basename(file_path)
        progress(0.1, desc="Extracting text from document...")
        try:
            text = extract_text(file_path)
        except Exception as err:
            return (
                f"### Error reading file\n\n{err}",
                "", "", "", "", "", "", "", "{}"
            )
    elif raw_text and len(raw_text.strip()) > 20:
        filename = "pasted_contract.txt"
        text = raw_text.strip()
    else:
        return (
            "### Please upload a document or paste contract text to analyze.",
            "", "", "", "", "", "", "", "{}"
        )

    text = clean_extracted_text(text)
    if len(text) < 20:
        return (
            "### Extracted text is too short to analyze. If uploading a scanned PDF, please provide one with selectable text.",
            "", "", "", "", "", "", "", "{}"
        )

    progress(0.3, desc="Retrieving legal context & running 7 AI agents in parallel...")
    try:
        results = orchestrator.analyze_document(text, filename)
    except Exception as err:
        return (
            f"### Analysis pipeline error\n\n{err}",
            "", "", "", "", "", "", "", "{}"
        )

    progress(0.9, desc="Formatting report...")

    summary_data = results.get("summary", {})
    risk_scores = results.get("risk_scores", {})
    red_flags = results.get("red_flags", [])
    green_flags = results.get("green_flags", [])
    obligations = results.get("obligations", [])
    comparisons = results.get("comparisons", [])
    negotiations = results.get("negotiations", [])

    score = risk_scores.get("overall_score", results.get("overall_score", 50))
    risk_level = results.get("risk_level", "medium").upper()
    doc_type = results.get("document_type", "Legal Agreement").replace("_", " ").title()

    # 1. Overview Markdown
    score_color = "#286a59" if score <= 35 else "#9a651d" if score <= 65 else "#983d35"
    overview_md = f"""## Executive Summary

**Document Type:** `{doc_type}` | **Overall Risk Score:** <span style="color:{score_color}; font-weight:bold; font-size:1.2em;">{score}/100 ({risk_level} RISK)</span>

{summary_data.get('summary', 'No summary available.')}

---
### Key Metadata
- **Parties Identified:** {', '.join(summary_data.get('parties', [])) or 'Not explicitly identified'}
- **Key Legal Concepts:** {', '.join(summary_data.get('key_terms', [])) or 'Standard contractual terms'}
- **Agents Completed:** {len(results.get('agents_completed', []))}/7 agents
"""

    # 2. Red Flags Table
    rf_data = []
    for rf in red_flags:
        rf_data.append([
            rf.get("severity", "medium").upper(),
            rf.get("title", "Risk"),
            rf.get("category", "General"),
            rf.get("detail", ""),
            rf.get("excerpt", ""),
            rf.get("recommendation", "")
        ])

    # 3. Green Flags Table
    gf_data = []
    for gf in green_flags:
        gf_data.append([
            gf.get("strength", "moderate").upper(),
            gf.get("title", "Protective Term"),
            gf.get("category", "General"),
            gf.get("detail", ""),
            gf.get("excerpt", "")
        ])

    # 4. Obligations Table
    ob_data = []
    for ob in obligations:
        ob_data.append([
            ob.get("party", "Party"),
            ob.get("action", ""),
            ob.get("timing", "Ongoing"),
            ob.get("status", "Defined")
        ])

    # 5. Comparisons Table
    comp_data = []
    for cp in comparisons:
        comp_data.append([
            cp.get("clause_type", "Standard Clause"),
            cp.get("status", "present").replace("_", " ").title(),
            cp.get("finding", ""),
            cp.get("standard_practice", ""),
            cp.get("deviation_level", "none").upper()
        ])

    # 6. Risk Dimensions HTML
    dims_html = f"""<div style="padding:15px; border-radius:12px; background:rgba(0,0,0,0.02); border:1px solid #ddd;">
        <h3 style="margin-top:0;">Risk Dimension Breakdown (Score: {score}/100)</h3>
        <p><em>{risk_scores.get('score_explanation', '')}</em></p>
    """
    for dim in risk_scores.get("dimensions", []):
        d_score = dim.get("score", 50)
        d_color = "#286a59" if d_score <= 35 else "#9a651d" if d_score <= 65 else "#983d35"
        dims_html += f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; font-size:0.9em; margin-bottom:3px;">
                <strong>{dim.get('dimension', 'Risk')}</strong>
                <span style="font-weight:bold; color:{d_color};">{d_score}/100</span>
            </div>
            <div style="height:8px; width:100%; background:#e0e0e0; border-radius:4px; overflow:hidden;">
                <div style="height:100%; width:{d_score}%; background:{d_color}; border-radius:4px;"></div>
            </div>
            <div style="font-size:0.8em; color:#666; margin-top:2px;">{dim.get('rationale', '')}</div>
        </div>
        """
    dims_html += "</div>"

    # 7. Negotiations Table
    neg_data = []
    for neg in negotiations:
        neg_data.append([
            neg.get("priority", "should_negotiate").replace("_", " ").upper(),
            neg.get("original_issue", ""),
            neg.get("suggested_change", ""),
            neg.get("negotiation_strategy", ""),
            neg.get("fallback_position", "")
        ])

    # 8. Full JSON
    json_out = json.dumps(results, indent=2)

    progress(1.0, desc="Complete!")
    return (
        overview_md,
        rf_data,
        gf_data,
        ob_data,
        comp_data,
        dims_html,
        neg_data,
        json_out
    )


def load_sample():
    return None, SAMPLE_CONTRACT


custom_css = """
.gradio-container { max-width: 1280px !important; margin: 0 auto; }
.header-box { text-align: center; padding: 20px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px; }
"""

with gr.Blocks(title="ClearClause — AI Legal Document Analyzer", css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div class="header-box">
        <h1 style="font-size: 2.2em; margin-bottom: 4px;">⚖️ ClearClause — AI Legal Document Analyzer</h1>
        <p style="font-size: 1.05em; color: #555;">Agentic RAG Contract Intelligence powered by 7 Specialized AI Agents</p>
        <p style="font-size: 0.85em; color: #777;">Platform creators: <strong>Kirti Kumari</strong> & <strong>Kushagra Srivastava</strong></p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=4):
            input_file = gr.File(
                label="Upload Contract (PDF, DOCX, TXT)",
                file_types=[".pdf", ".docx", ".doc", ".txt"],
                type="filepath"
            )
            input_text = gr.Textbox(
                label="Or Paste Contract Text Directly",
                placeholder="Paste legal contract or agreement clauses here...",
                lines=8
            )
            with gr.Row():
                btn_sample = gr.Button("📄 Load Sample Contract", variant="secondary")
                btn_analyze = gr.Button("🚀 Analyze with 7 Agents", variant="primary")

        with gr.Column(scale=6):
            output_overview = gr.Markdown("### Upload a document and click 'Analyze with 7 Agents' to begin.")

    with gr.Tabs():
        with gr.TabItem("🚨 Red Flags"):
            output_red_flags = gr.Dataframe(
                headers=["Severity", "Title", "Category", "Risk Detail", "Problematic Clause Excerpt", "Recommended Counter-Action"],
                datatype=["str", "str", "str", "str", "str", "str"],
                wrap=True,
                label="Detected Unfavorable Clauses & Traps"
            )

        with gr.TabItem("🛡️ Green Flags"):
            output_green_flags = gr.Dataframe(
                headers=["Strength", "Title", "Category", "Protective Detail", "Clause Excerpt"],
                datatype=["str", "str", "str", "str", "str"],
                wrap=True,
                label="Protective & Balanced Provisions"
            )

        with gr.TabItem("📝 Commitments & Obligations"):
            output_obligations = gr.Dataframe(
                headers=["Party", "Action Required", "Timing / Deadline", "Status"],
                datatype=["str", "str", "str", "str"],
                wrap=True,
                label="Party Obligations & Critical Deadlines"
            )

        with gr.TabItem("⚖️ Standard Comparisons"):
            output_comparisons = gr.Dataframe(
                headers=["Clause Type", "Status", "Finding", "Standard Practice", "Deviation Level"],
                datatype=["str", "str", "str", "str", "str"],
                wrap=True,
                label="Benchmark vs. Standard Contract Templates"
            )

        with gr.TabItem("📊 Multi-Dimensional Risk Score"):
            output_dimensions = gr.HTML(label="Risk Breakdown")

        with gr.TabItem("💬 Negotiation Playbook"):
            output_negotiations = gr.Dataframe(
                headers=["Priority", "Issue", "Suggested Alternative Clause", "Negotiation Tactics", "Fallback Position"],
                datatype=["str", "str", "str", "str", "str"],
                wrap=True,
                label="Actionable Counter-Proposals"
            )

        with gr.TabItem("📄 Full JSON Output"):
            output_json = gr.Code(language="json", label="Complete Analysis Payload")

    btn_sample.click(
        fn=load_sample,
        inputs=[],
        outputs=[input_file, input_text]
    )

    btn_analyze.click(
        fn=analyze_contract,
        inputs=[input_file, input_text],
        outputs=[
            output_overview,
            output_red_flags,
            output_green_flags,
            output_obligations,
            output_comparisons,
            output_dimensions,
            output_negotiations,
            output_json
        ]
    )

    gr.HTML("""
    <div style="text-align: center; margin-top: 30px; font-size: 0.8em; color: #888;">
        ClearClause provides informational contract analysis only. It does not constitute formal legal advice.
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

