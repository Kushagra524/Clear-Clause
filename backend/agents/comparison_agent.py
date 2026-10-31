import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Contract Comparison Agent. Your job is to compare the uploaded contract against standard legal templates and best practices from the legal knowledge base.

Compare the document against standard practices for:
1. Whether common protective clauses are PRESENT or MISSING
2. Whether clause language is STANDARD or UNUSUAL compared to typical contracts
3. Whether any terms deviate significantly from industry norms

For each comparison point, provide:
- "clause_type": what type of clause is being compared
- "status": "present_standard" | "present_unusual" | "missing" | "exceeds_standard"
- "finding": short description of what you found
- "standard_practice": what the standard or best practice would be
- "deviation_level": "none" | "minor" | "significant" | "critical"

Check for these standard clauses:
- Limitation of liability
- Indemnification (mutual)
- Termination provisions
- Force majeure
- Dispute resolution
- Confidentiality with time limit
- Data protection / GDPR
- Governing law
- Assignment restrictions
- Amendment process
- Severability
- Entire agreement
- Waiver provisions
- Notice requirements

Return a JSON array. If comparison cannot be performed, return: []"""


def compare_against_standards(document_text, context_chunks):
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, document_text[:3000])

    try:
        response = query_mistral(prompt, max_tokens=2048)
        return _parse_response(response)
    except Exception:
        return _fallback_comparison(document_text)


def _parse_response(response):
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    items = []
    for match in re.finditer(r'\{[^{}]+\}', response):
        try:
            obj = json.loads(match.group())
            if "clause_type" in obj or "finding" in obj:
                items.append(obj)
        except json.JSONDecodeError:
            continue
    return items


def _fallback_comparison(text):
    text_lower = text.lower()

    # standard clauses every contract should have
    standard_clauses = {
        "Limitation of Liability": ["limitation of liability", "liability shall not exceed", "aggregate liability"],
        "Indemnification": ["indemnif", "hold harmless", "defend and indemnify"],
        "Termination": ["terminat", "right to terminate", "termination for cause"],
        "Force Majeure": ["force majeure", "act of god", "beyond reasonable control"],
        "Dispute Resolution": ["dispute resolution", "arbitration", "mediation", "governing law"],
        "Confidentiality": ["confidential", "non-disclosure", "proprietary information"],
        "Data Protection": ["data protection", "personal data", "gdpr", "privacy"],
        "Governing Law": ["governing law", "governed by the laws", "jurisdiction"],
        "Assignment": ["assignment", "shall not assign", "may not assign"],
        "Severability": ["severab", "invalid provision", "unenforceable provision"],
        "Entire Agreement": ["entire agreement", "whole agreement", "supersedes all"],
        "Notice Requirements": ["notice shall be", "written notice", "notice to"],
    }

    comparisons = []
    for clause_name, keywords in standard_clauses.items():
        found = any(kw in text_lower for kw in keywords)
        comparisons.append({
            "clause_type": clause_name,
            "status": "present_standard" if found else "missing",
            "finding": f"{clause_name} clause {'found' if found else 'not found'} in the document.",
            "standard_practice": f"Standard contracts typically include a {clause_name.lower()} clause.",
            "deviation_level": "none" if found else "significant"
        })

    return comparisons
