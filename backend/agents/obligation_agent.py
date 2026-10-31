import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are an Obligation Extractor agent for legal documents. Your job is to find all duties, deadlines, payment obligations, notice periods, and actions required by each party.

For each obligation found, extract:
- "party": who must perform (specific party name or role)
- "action": what they must do (clear, specific description)
- "timing": when it must be done (deadline, frequency, or "ongoing")
- "status": "defined" if clearly stated, "ongoing" if recurring, "unclear" if vague
- "section": which section/clause it comes from (if identifiable)
- "consequence": what happens if not fulfilled (if stated)

Focus on:
- Payment deadlines and amounts
- Delivery timelines
- Reporting requirements
- Notice periods for termination or changes
- Renewal deadlines
- Compliance obligations
- Insurance requirements
- Record-keeping duties

Return a JSON array of obligations. If none found, return: []"""


def extract_obligations(document_text, context_chunks):
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, document_text[:3000])

    try:
        response = query_mistral(prompt, max_tokens=2048)
        return _parse_response(response)
    except Exception:
        return _fallback_extraction(document_text)


def _parse_response(response):
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    obligations = []
    for match in re.finditer(r'\{[^{}]+\}', response):
        try:
            obj = json.loads(match.group())
            if "party" in obj or "action" in obj:
                obligations.append(obj)
        except json.JSONDecodeError:
            continue
    return obligations


def _fallback_extraction(text):
    text_lower = text.lower()
    obligations = []

    # look for common obligation patterns
    obligation_patterns = [
        (r'(?:shall|must|agrees?\s+to|obligated\s+to|required\s+to)\s+(.{20,120})', "defined"),
        (r'within\s+(\d+)\s+(?:days?|business\s+days?|months?|weeks?)\s+(.{10,80})', "defined"),
        (r'(?:payment|pay|remit|compensate)\s+(?:of\s+)?(.{10,100})', "defined"),
        (r'(?:notice\s+of\s+)?(\d+)\s+days?\s+(?:written\s+)?notice', "defined"),
    ]

    for pattern, status in obligation_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end].strip()

            obligations.append({
                "party": "Party (see document)",
                "action": match.group(0)[:150].strip(),
                "timing": "See document for specifics",
                "status": status,
                "section": "Detected from text",
                "consequence": "Not specified"
            })

        if len(obligations) >= 10:
            break

    return obligations
