import json
import re
from llm.mistral_client import query_mistral, build_prompt


SYSTEM_PROMPT = """You are a Negotiation Advisor agent for legal documents. Given the red flags identified in a contract, suggest specific counter-terms, alternative language, and negotiation strategies.

For each red flag, provide:
- "original_issue": the red flag title being addressed
- "suggested_change": specific alternative clause language to propose
- "negotiation_strategy": how to approach the negotiation tactically
- "priority": "must_negotiate" | "should_negotiate" | "nice_to_have"
- "fallback_position": minimum acceptable alternative if primary suggestion is rejected
- "legal_basis": relevant legal principle supporting the change (if applicable)

Focus on practical, actionable suggestions that a non-lawyer could bring to a negotiation. Reference standard industry practices where possible.

Return a JSON array of negotiation suggestions. If no suggestions needed, return: []"""


def suggest_negotiations(document_text, context_chunks, red_flags=None):
    # generates negotiation advice based on detected red flags
    enriched_query = document_text[:2000]
    if red_flags:
        enriched_query += "\n\nRED FLAGS TO ADDRESS:\n"
        for flag in red_flags:
            enriched_query += f"- {flag.get('title', '')}: {flag.get('detail', '')}\n"
            if flag.get('excerpt'):
                enriched_query += f"  Excerpt: \"{flag['excerpt'][:200]}\"\n"

    prompt = build_prompt(SYSTEM_PROMPT, context_chunks, enriched_query)

    try:
        response = query_mistral(prompt, max_tokens=2048)
        return _parse_response(response, red_flags)
    except Exception:
        return _fallback_suggestions(red_flags)


def _parse_response(response, red_flags):
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
            if "suggested_change" in obj or "original_issue" in obj:
                items.append(obj)
        except json.JSONDecodeError:
            continue

    if not items and red_flags:
        return _fallback_suggestions(red_flags)
    return items


def _fallback_suggestions(red_flags):
    if not red_flags:
        return []

    # standard negotiation templates for common red flag categories
    templates = {
        "AUTO-RENEWAL TRAPS": {
            "suggested_change": "Replace auto-renewal with a requirement for mutual written consent at least 30 days before the renewal date.",
            "negotiation_strategy": "Frame this as beneficial for both parties — it ensures active engagement rather than passive continuation.",
            "priority": "must_negotiate",
            "fallback_position": "Accept auto-renewal but add a simple opt-out mechanism with 30 days written notice before renewal.",
        },
        "UNLIMITED LIABILITY": {
            "suggested_change": "Add a mutual liability cap equal to the total fees paid under the agreement in the preceding 12 months.",
            "negotiation_strategy": "Present industry data showing liability caps are standard practice. Propose a cap tied to contract value.",
            "priority": "must_negotiate",
            "fallback_position": "Cap liability at 2x the annual contract value for direct damages only.",
        },
        "INDEMNIFICATION TRAPS": {
            "suggested_change": "Make indemnification mutual and limited to third-party claims arising from each party's negligence or breach.",
            "negotiation_strategy": "Emphasize fairness — both parties should bear responsibility for their own actions.",
            "priority": "should_negotiate",
            "fallback_position": "Accept broader indemnification but add a cap matching the liability cap.",
        },
        "NON-COMPETE OVERREACH": {
            "suggested_change": "Limit non-compete to 12 months, specific geographic regions where you actually operate, and only direct competitors.",
            "negotiation_strategy": "Many jurisdictions limit enforceability of broad non-competes. Reference local law as leverage.",
            "priority": "must_negotiate",
            "fallback_position": "Accept non-compete but limit duration to 6 months and scope to direct competitive activities.",
        },
        "WAIVER OF RIGHTS": {
            "suggested_change": "Remove the jury trial waiver. If arbitration is preferred, ensure it allows for neutral arbitrator selection.",
            "negotiation_strategy": "Propose arbitration with a reputable body like AAA or JAMS with shared costs.",
            "priority": "should_negotiate",
            "fallback_position": "Accept arbitration but ensure the arbitration venue is mutually convenient.",
        },
        "INTELLECTUAL PROPERTY GRAB": {
            "suggested_change": "Limit IP assignment to work specifically created for this engagement. Pre-existing IP remains with original owner.",
            "negotiation_strategy": "Clearly distinguish between pre-existing IP, project-specific IP, and improvements. Propose licensing instead of transfer.",
            "priority": "must_negotiate",
            "fallback_position": "Grant a license for project-specific use instead of full ownership transfer.",
        },
        "PENALTY CLAUSES": {
            "suggested_change": "Replace penalties with liquidated damages that reflect actual estimated losses, not punitive amounts.",
            "negotiation_strategy": "Courts often strike down penalties that are disproportionate. Frame your request as making the clause enforceable.",
            "priority": "should_negotiate",
            "fallback_position": "Accept the penalty structure but add a cure period (14-30 days) before penalties apply.",
        },
    }

    suggestions = []
    for flag in red_flags:
        category = flag.get("category", "")
        template = templates.get(category, {
            "suggested_change": "Review this clause with legal counsel and propose balanced alternative language.",
            "negotiation_strategy": "Present comparable contracts from the same industry as reference points.",
            "priority": "should_negotiate",
            "fallback_position": "Request a mutual version of this clause as minimum.",
        })

        suggestions.append({
            "original_issue": flag.get("title", "Unknown Issue"),
            "suggested_change": template["suggested_change"],
            "negotiation_strategy": template["negotiation_strategy"],
            "priority": template["priority"],
            "fallback_position": template["fallback_position"],
            "legal_basis": "Consult local contract law for enforceability of this clause."
        })

    return suggestions
