import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Legal Document Summary Agent. Your job is to create a clear, plain-language summary of the legal document that a non-lawyer can understand.

Your summary must cover:
1. WHAT this document is (type of agreement)
2. WHO the parties involved are
3. WHAT the main purpose and scope is
4. KEY financial terms (payment, pricing)
5. DURATION and renewal terms
6. MOST IMPORTANT obligations for each party
7. HOW the agreement can be ended

Write in clear, simple language. Avoid legal jargon. The summary should be 3-5 paragraphs long.

Also identify the document type from: employment_agreement, service_agreement, nda, lease_agreement, partnership_agreement, loan_agreement, purchase_agreement, licensing_agreement, terms_of_service, privacy_policy, other

Return JSON with:
- "summary": the plain-language summary text
- "document_type": the identified type
- "parties": list of party names mentioned
- "effective_date": date if found, null otherwise
- "key_terms": list of 5-10 most important terms or concepts in this document"""


def generate_summary(document_text, context_chunks):
    # creates a readable summary of the legal document
    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, document_text[:4000])

    try:
        response = query_mistral(prompt, max_tokens=1500)
        return _parse_response(response, document_text)
    except Exception:
        return _fallback_summary(document_text)


def _parse_response(response, original_text):
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if "summary" in result:
                return result
    except json.JSONDecodeError:
        pass

    # if json parsing fails use the raw response as summary
    return {
        "summary": response[:1500] if response else _fallback_summary(original_text)["summary"],
        "document_type": "other",
        "parties": [],
        "effective_date": None,
        "key_terms": []
    }


def _fallback_summary(text):
    # basic extractive summary when llm is unavailable
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    # take first few sentences and some from the middle
    summary_parts = sentences[:3]
    if len(sentences) > 10:
        mid = len(sentences) // 2
        summary_parts.extend(sentences[mid:mid+2])

    summary = '. '.join(summary_parts)
    if summary and not summary.endswith('.'):
        summary += '.'

    # detect document type from keywords
    text_lower = text.lower()
    doc_type = "other"
    type_keywords = {
        "employment_agreement": ["employment", "employee", "employer", "salary", "wages"],
        "nda": ["non-disclosure", "confidential information", "nda", "proprietary information"],
        "service_agreement": ["service provider", "services shall", "scope of services"],
        "lease_agreement": ["landlord", "tenant", "lease", "rent", "premises"],
        "terms_of_service": ["terms of service", "terms of use", "user agreement"],
    }
    for dtype, keywords in type_keywords.items():
        if any(kw in text_lower for kw in keywords):
            doc_type = dtype
            break

    return {
        "summary": summary[:1500],
        "document_type": doc_type,
        "parties": [],
        "effective_date": None,
        "key_terms": []
    }
