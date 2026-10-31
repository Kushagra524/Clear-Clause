import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Green Flag Detector agent for legal documents. Your job is to identify clauses, terms, or provisions that are protective, fair, and favorable to the person reviewing this document.

Look for these specific green flag categories:
- MUTUAL TERMINATION: both parties have reasonable termination rights
- LIABILITY CAP: clear cap on liability exposure
- FAIR DISPUTE RESOLUTION: balanced dispute resolution mechanisms
- CLEAR PAYMENT TERMS: transparent pricing with no hidden fees
- DATA PROTECTION: strong data handling and privacy protections
- MUTUAL INDEMNIFICATION: balanced indemnification obligations
- REASONABLE NON-COMPETE: appropriately scoped restrictions
- NOTICE PERIODS: adequate advance notice before changes
- FORCE MAJEURE PROTECTION: balanced force majeure coverage
- IP PROTECTION: clear IP ownership with fair terms
- TERMINATION ASSISTANCE: transition support after contract ends
- AUDIT RIGHTS: right to audit compliance and billing
- SLA GUARANTEES: service level commitments with remedies
- LIMITATION OF DAMAGES: exclusion of consequential or indirect damages
- GOVERNING LAW NEUTRAL: fair jurisdiction choice

Return a JSON array of green flags found. Each item must have:
- "title": short descriptive name
- "detail": 2-3 sentence explanation of why this is protective
- "excerpt": the exact protective text from the document (if found)
- "category": one of the categories listed above
- "strength": "strong", "moderate", or "basic"

If no green flags are found, return an empty array: []"""


def detect_green_flags(document_text, context_chunks):
    # identifies protective and favorable clauses
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, document_text[:3000])

    try:
        response = query_mistral(prompt, max_tokens=2048)
        flags = _parse_response(response)
        return flags
    except Exception:
        return _fallback_detection(document_text)


def _parse_response(response):
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

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
    text_lower = text.lower()
    flags = []

    patterns = {
        "Mutual Termination Rights": {
            "keywords": ["either party may terminate", "mutual termination", "both parties may terminate"],
            "category": "MUTUAL TERMINATION",
            "strength": "strong",
            "detail": "Both parties have the right to terminate, providing balanced exit options and preventing lock-in.",
        },
        "Liability Cap Present": {
            "keywords": ["liability shall not exceed", "aggregate liability", "maximum liability", "cap on liability"],
            "category": "LIABILITY CAP",
            "strength": "strong",
            "detail": "A liability cap limits maximum financial exposure, protecting against disproportionate claims.",
        },
        "Notice Period Defined": {
            "keywords": ["days written notice", "days prior notice", "advance written notice", "notice period of"],
            "category": "NOTICE PERIODS",
            "strength": "moderate",
            "detail": "A defined notice period gives adequate time to prepare for changes or termination.",
        },
        "Confidentiality with Time Limit": {
            "keywords": ["confidentiality for a period of", "confidentiality obligations shall expire", "years from disclosure"],
            "category": "DATA PROTECTION",
            "strength": "moderate",
            "detail": "Confidentiality obligations have a reasonable time limit rather than persisting indefinitely.",
        },
        "Dispute Mediation First": {
            "keywords": ["attempt mediation", "good faith negotiation", "mediation before", "resolve through negotiation"],
            "category": "FAIR DISPUTE RESOLUTION",
            "strength": "moderate",
            "detail": "The contract encourages mediation or negotiation before escalation, saving time and legal costs.",
        },
        "Data Protection Clause": {
            "keywords": ["data protection", "gdpr compliance", "personal data shall", "privacy policy"],
            "category": "DATA PROTECTION",
            "strength": "strong",
            "detail": "Explicit data protection provisions safeguard personal information and ensure regulatory compliance.",
        },
    }

    for title, info in patterns.items():
        for keyword in info["keywords"]:
            if keyword in text_lower:
                idx = text_lower.index(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(keyword) + 100)
                excerpt = text[start:end].strip()

                flags.append({
                    "title": title,
                    "detail": info["detail"],
                    "excerpt": excerpt,
                    "category": info["category"],
                    "strength": info["strength"]
                })
                break

    return flags
