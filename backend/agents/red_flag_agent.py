import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Red Flag Detector agent for legal documents. Your job is to identify clauses, terms, or language that could be risky, unfavorable, or harmful to the person signing this document.

Look for these specific red flag categories:
- AUTO-RENEWAL TRAPS: clauses that lock parties into indefinite renewal cycles
- UNLIMITED LIABILITY: absence of liability caps or one-sided liability
- ONE-SIDED TERMINATION: only one party can terminate the agreement
- HIDDEN FEES: vague payment language that could introduce unexpected costs
- NON-COMPETE OVERREACH: excessively broad non-compete restrictions
- WAIVER OF RIGHTS: clauses forcing waiver of legal rights, class action, or jury trial
- INDEMNIFICATION TRAPS: one-sided indemnification without reciprocity
- DATA MISUSE: vague data handling that could allow misuse of personal information
- PENALTY CLAUSES: disproportionate penalties for minor breaches
- GOVERNING LAW DISADVANTAGE: jurisdiction chosen to disadvantage one party
- CONFIDENTIALITY OVERREACH: indefinite or overly broad confidentiality requirements
- INTELLECTUAL PROPERTY GRAB: transfer of IP rights without fair compensation
- FORCE MAJEURE ABUSE: one-sided force majeure definitions
- MISLEADING LANGUAGE: deliberately vague or confusing terms that obscure obligations

Return a JSON array of red flags found. Each item must have:
- "title": short descriptive name of the red flag
- "severity": "high", "medium", or "low"
- "detail": 2-3 sentence explanation of the risk
- "excerpt": the exact problematic text from the document (if found)
- "category": one of the categories listed above
- "recommendation": what the signer should ask for or negotiate

If no red flags are found, return an empty array: []"""


def detect_red_flags(document_text, context_chunks):
    # scans document for risky or unfavorable clauses using rag context
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, document_text[:3000])

    try:
        response = query_mistral(prompt, max_tokens=2048)
        flags = _parse_response(response)
        return flags
    except Exception as err:
        return _fallback_detection(document_text)


def _parse_response(response):
    # extracts json array from llm response
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    # try to find individual objects
    flags = []
    for match in re.finditer(r'\{[^{}]+\}', response):
        try:
            obj = json.loads(match.group())
            if "title" in obj:
                flags.append(obj)
        except json.JSONDecodeError:
            continue
    return flags


def _fallback_detection(text):
    # rule-based fallback when llm is unavailable
    text_lower = text.lower()
    flags = []

    patterns = {
        "Auto-Renewal Clause": {
            "keywords": ["automatically renew", "auto-renew", "shall renew", "renewed for successive"],
            "severity": "high",
            "category": "AUTO-RENEWAL TRAPS",
            "detail": "This contract contains auto-renewal language that may lock you into continued obligations without explicit consent for each renewal period.",
        },
        "Unlimited Liability Exposure": {
            "keywords": ["unlimited liability", "no cap on liability", "without limitation of liability"],
            "severity": "high",
            "category": "UNLIMITED LIABILITY",
            "detail": "No liability cap was detected. This means potential financial exposure is uncapped and could result in significant losses.",
        },
        "One-Sided Indemnification": {
            "keywords": ["shall indemnify", "hold harmless", "defend and indemnify"],
            "severity": "medium",
            "category": "INDEMNIFICATION TRAPS",
            "detail": "Indemnification language was found that may impose one-sided obligations. Check if indemnification is mutual or only applies to one party.",
        },
        "Non-Compete Restriction": {
            "keywords": ["non-compete", "non compete", "shall not compete", "competitive activity"],
            "severity": "medium",
            "category": "NON-COMPETE OVERREACH",
            "detail": "A non-compete clause was detected. Review the geographic scope, duration, and breadth to ensure it is reasonable.",
        },
        "Arbitration / Jury Waiver": {
            "keywords": ["binding arbitration", "waive jury", "waiver of jury", "dispute resolution through arbitration"],
            "severity": "medium",
            "category": "WAIVER OF RIGHTS",
            "detail": "This contract includes mandatory arbitration or jury trial waiver language, which limits your legal options in case of disputes.",
        },
        "Broad Confidentiality": {
            "keywords": ["perpetual confidentiality", "indefinite confidentiality", "survive termination indefinitely"],
            "severity": "low",
            "category": "CONFIDENTIALITY OVERREACH",
            "detail": "Confidentiality obligations appear to extend indefinitely or survive termination without a time limit.",
        },
        "IP Assignment Clause": {
            "keywords": ["assign all intellectual property", "transfer of ip", "work product shall belong", "all rights title and interest"],
            "severity": "high",
            "category": "INTELLECTUAL PROPERTY GRAB",
            "detail": "This clause transfers intellectual property rights, potentially including work created before the agreement. Ensure fair compensation and scope limits.",
        },
        "Penalty for Early Termination": {
            "keywords": ["early termination fee", "liquidated damages", "penalty for breach", "termination penalty"],
            "severity": "medium",
            "category": "PENALTY CLAUSES",
            "detail": "The contract includes penalty provisions for early termination or breach. Verify that penalties are proportionate to actual damages.",
        },
    }

    for title, info in patterns.items():
        for keyword in info["keywords"]:
            if keyword in text_lower:
                # extract surrounding text as excerpt
                idx = text_lower.index(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(keyword) + 100)
                excerpt = text[start:end].strip()

                flags.append({
                    "title": title,
                    "severity": info["severity"],
                    "detail": info["detail"],
                    "excerpt": excerpt,
                    "category": info["category"],
                    "recommendation": "Consult a legal professional about this clause."
                })
                break

    return flags
