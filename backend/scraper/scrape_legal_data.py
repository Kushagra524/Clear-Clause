import requests
import time
import re
import os
import json
from bs4 import BeautifulSoup

# legal knowledge sources to scrape
LEGAL_SOURCES = [
    # indian contract act
    {"url": "https://www.indiacode.nic.in/bitstream/123456789/2187/1/AAA1872___09.pdf", "type": "pdf", "source": "Indian Contract Act 1872", "jurisdiction": "India"},
    {"url": "https://legislative.gov.in/sites/default/files/A1872-09.pdf", "type": "pdf", "source": "Indian Contract Act 1872", "jurisdiction": "India"},
    # plain text fallback sources
    {"url": "https://www.lawinsider.com/clause/indemnification", "type": "html", "source": "LawInsider - Indemnification", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/limitation-of-liability", "type": "html", "source": "LawInsider - Limitation of Liability", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/termination", "type": "html", "source": "LawInsider - Termination", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/non-compete", "type": "html", "source": "LawInsider - Non-Compete", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/confidentiality", "type": "html", "source": "LawInsider - Confidentiality", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/governing-law", "type": "html", "source": "LawInsider - Governing Law", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/force-majeure", "type": "html", "source": "LawInsider - Force Majeure", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/arbitration", "type": "html", "source": "LawInsider - Arbitration", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/intellectual-property", "type": "html", "source": "LawInsider - IP", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/auto-renewal", "type": "html", "source": "LawInsider - Auto Renewal", "jurisdiction": "US"},
    {"url": "https://www.lawinsider.com/clause/data-protection", "type": "html", "source": "LawInsider - Data Protection", "jurisdiction": "GDPR/US"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def scrape_html(url, source_name, jurisdiction, timeout=30):
    # fetches and cleans html content from a legal resource
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # remove navigation, ads, scripts, styles
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()

        # try content-specific selectors first
        content = (
            soup.find("article") or
            soup.find("main") or
            soup.find(class_=re.compile(r"content|article|main|clause|legal", re.I)) or
            soup.find("body")
        )

        if not content:
            return None

        text = content.get_text(separator="\n")
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        if len(text) < 200:
            return None

        return {
            "text": text[:50000],
            "source": source_name,
            "jurisdiction": jurisdiction,
            "url": url,
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

    except Exception as err:
        print(f"  Failed to scrape {url}: {err}")
        return None


def get_builtin_legal_knowledge():
    # comprehensive built-in legal knowledge when scraping fails
    knowledge = [
        {
            "source": "Contract Law - General Principles",
            "jurisdiction": "Universal",
            "text": """STANDARD CONTRACT PRINCIPLES AND RED FLAG DETECTION

AUTOMATIC RENEWAL CLAUSES (RED FLAG - HIGH RISK):
Automatic renewal clauses that renew a contract for successive periods without explicit consent are considered traps. Standard practice: contracts should require affirmative written notice to renew. Red flag language includes: "shall automatically renew", "automatically renew for successive periods", "renewed unless terminated with X days notice". Counter: require mutual written consent for each renewal period.

UNLIMITED LIABILITY (RED FLAG - HIGH RISK):
Contracts lacking liability caps expose parties to unlimited financial risk. Standard practice: mutual liability cap equal to 12 months of fees paid. Red flag: absence of any liability limitation, or "notwithstanding anything to the contrary" language overriding caps. Counter: add "In no event shall either party's aggregate liability exceed the total fees paid in the preceding 12 months."

ONE-SIDED INDEMNIFICATION (RED FLAG - HIGH RISK):
Indemnification provisions requiring one party to defend and hold harmless without reciprocity are unfavorable. Standard: mutual indemnification for each party's negligence or willful misconduct. Red flag: "shall indemnify, defend and hold harmless" without corresponding obligation on the other party. Counter: make indemnification mutual and limit to claims arising from the indemnifying party's negligence.

NON-COMPETE OVERREACH (RED FLAG - MEDIUM RISK):
Non-compete clauses that are excessively broad in scope, duration, or geography may be unenforceable and harm career/business prospects. Standard: maximum 12 months, limited geographic scope, narrow definition of competitive activity. Red flag: "shall not engage in any competitive activity anywhere in the world" or durations exceeding 2 years. Many jurisdictions (California, India) limit enforceability of non-competes.

ARBITRATION AND JURY WAIVER (RED FLAG - MEDIUM RISK):
Mandatory arbitration clauses that waive jury trial rights limit legal remedies. Standard: mutual agreement to arbitration with neutral arbitrator selection through recognized body (AAA, JAMS, ICC). Red flag: "waives right to jury trial", "binding arbitration in [inconvenient location]", class action waivers. Counter: ensure mutual arbitration with shared costs and neutral venue.

INTELLECTUAL PROPERTY ASSIGNMENT (RED FLAG - HIGH RISK):
Broad IP assignment clauses that capture pre-existing IP or work beyond the contract scope are dangerous. Standard: IP assignment limited to work specifically created under this agreement, with carve-outs for pre-existing IP. Red flag: "all intellectual property developed by employee/contractor belongs to company", "irrevocably assigns all rights title and interest". Counter: limit assignment to work product created specifically for this engagement.

PENALTY CLAUSES (RED FLAG - MEDIUM RISK):
Disproportionate liquidated damages or penalties that don't reflect actual losses may be unenforceable but still cause disputes. Standard: liquidated damages should represent a genuine pre-estimate of loss. Red flag: "shall pay $X per day" without relationship to actual damages. Counter: negotiate for cure periods and caps on accumulated penalties.

DATA PRIVACY VIOLATIONS (RED FLAG - HIGH RISK):
Vague data handling provisions that allow broad use or sharing of personal data without consent are risky. Standard: explicit data use limitations, GDPR/PDPA compliance, data deletion on request. Red flag: "may share data with third parties", "data may be used for any purpose", no deletion provisions.

MISLEADING LANGUAGE PATTERNS (RED FLAG):
Watch for: "notwithstanding" used to override favorable provisions, "at our sole discretion" without limits, "reasonable" without definition, "may" versus "shall" (permissive vs mandatory), "best efforts" without objective standard, "market rate" without definition mechanism."""
        },
        {
            "source": "Indian Contract Act 1872 - Key Provisions",
            "jurisdiction": "India",
            "text": """INDIAN CONTRACT ACT 1872 - RELEVANT SECTIONS

Section 10 - Essentials of Valid Contract:
All agreements are contracts if made by free consent of parties competent to contract, for lawful consideration and with lawful object. Key requirements: competency, free consent, lawful consideration, lawful object.

Section 13-22 - Free Consent:
Consent is free when not caused by coercion (Section 15), undue influence (Section 16), fraud (Section 17), misrepresentation (Section 18), or mistake (Sections 20-22). Contracts formed under these conditions are voidable at the option of the aggrieved party.

Section 16 - Undue Influence:
A contract is said to be induced by undue influence where one party is in a position to dominate the will of another. Hidden fees, misleading terms, and deliberately confusing language can constitute undue influence.

Section 17 - Fraud:
Fraud includes: suggestion of fact known to be false, active concealment of facts, promises without intention to perform, and any act fitted to deceive. One-sided contracts with hidden obligations may constitute fraud.

Section 23 - Unlawful Consideration:
Consideration or object is unlawful if it is forbidden by law, defeats provisions of any law, fraudulent, involves injury to person or property, or against public policy. Overly broad non-competes may be void under this section.

Section 27 - Agreements in Restraint of Trade:
Every agreement by which any person is restrained from exercising a lawful profession, trade or business is void. Non-compete clauses in India are generally unenforceable except for sellers of goodwill. Employment non-competes post-termination are largely void in India.

Section 74 - Compensation for Breach with Penalty:
When a contract has a penalty for breach, the party complaining is entitled to receive reasonable compensation not exceeding the penalty amount. Courts will strike down disproportionate penalties.

Section 124-125 - Contract of Indemnity:
Indemnifier is liable for all damages, costs, and sums paid in compromise of suit. One-sided indemnification should be reviewed carefully under these provisions."""
        },
        {
            "source": "GDPR and Data Protection Clauses",
            "jurisdiction": "EU/UK/India",
            "text": """DATA PROTECTION CLAUSES - BEST PRACTICES AND RED FLAGS

GDPR ARTICLE 5 - DATA PROCESSING PRINCIPLES:
Personal data must be: processed lawfully and transparently, collected for specified explicit purposes only, adequate and limited to what is necessary (data minimization), accurate and kept up to date, kept no longer than necessary (storage limitation), processed with appropriate security.

GREEN FLAG - STRONG DATA PROTECTION CLAUSE:
"The Processor shall process Personal Data only on documented instructions from the Controller, ensure persons authorized to process data are under confidentiality, implement appropriate technical and organizational security measures, delete or return all Personal Data upon termination."

RED FLAG - WEAK DATA PROTECTION:
"We may collect, use, store and transfer different kinds of personal data about you. We may share data with third parties for business purposes." - This is a red flag for indefinite, broad data use without user control.

INDIA PDPB (Personal Data Protection):
Organizations processing personal data of Indian citizens must: obtain clear consent, explain purpose, allow data principals to withdraw consent, ensure data localization for sensitive categories, appoint Data Protection Officer.

STANDARD DATA PROTECTION CLAUSE:
Processor shall: process data only as instructed, maintain confidentiality, implement security measures, not engage sub-processors without consent, assist with data subject requests, delete data after termination, allow audits."""
        },
        {
            "source": "Employment Contract Red Flags",
            "jurisdiction": "India/US/UK",
            "text": """EMPLOYMENT CONTRACT ANALYSIS - RED AND GREEN FLAGS

RED FLAGS IN EMPLOYMENT CONTRACTS:

At-Will Employment Overreach: "Employment may be terminated at any time for any reason" without notice period or severance is favorable to employer. Standard: 30-90 days notice or pay in lieu.

Broad IP Assignment: "All inventions, discoveries, and works created during employment belong to the company" including personal projects created on personal time is overreaching. Standard: limit to work related to company's business created using company resources.

Excessive Non-Solicitation: Prohibiting all contact with former colleagues or clients for years post-employment. Standard: 6-12 months, limited to active clients you personally worked with.

Variable Pay Without Formula: "Bonus at company's sole discretion" with no formula or minimum. Standard: defined bonus formula tied to measurable KPIs.

Unilateral Policy Changes: "Company may change policies, benefits, or terms at any time without notice" effectively allows contract modification without consent.

GREEN FLAGS IN EMPLOYMENT CONTRACTS:
- Defined notice periods (both directions)
- Fixed and variable compensation clearly stated
- Defined working hours with overtime provisions
- Clear expense reimbursement policy
- IP carve-out for personal projects
- Defined grievance procedure
- Specific termination grounds (for cause definition)"""
        },
        {
            "source": "Real Estate and Lease Agreement Standards",
            "jurisdiction": "India/US/UK",
            "text": """LEASE AND REAL ESTATE CONTRACT ANALYSIS

RED FLAGS IN LEASE AGREEMENTS:
Excessive Security Deposit: Deposits beyond 2-3 months rent (or statutory limit) with vague return conditions. Standard: security deposit with itemized deductions and defined return timeline.

Landlord Entry Without Notice: "Landlord may enter premises at any time" without notice requirement. Standard: 24-48 hours written notice except in emergencies.

Unilateral Rent Increase: "Landlord may increase rent at any time" without limitation. Standard: rent increase with minimum 3 months notice, tied to CPI or capped percentage.

Broad Repair Obligations: Tenant responsible for all repairs including structural issues. Standard: landlord responsible for structural/major repairs, tenant for minor maintenance.

Unclear Move-Out Conditions: Vague cleanliness/condition standards at termination creating dispute opportunities. Standard: documented move-in checklist with photographs.

GREEN FLAGS IN LEASE AGREEMENTS:
- Defined maintenance responsibilities for each party
- Clear security deposit return timeline with interest
- Renewal option with defined terms
- Subletting rights (even if restricted)
- Force majeure provisions
- Dispute resolution mechanism"""
        },
        {
            "source": "Service Agreement Best Practices",
            "jurisdiction": "Universal",
            "text": """SERVICE AGREEMENT ANALYSIS - STANDARDS AND RED FLAGS

SERVICE LEVEL AGREEMENT (SLA) PROVISIONS:
Standard service agreements should define: uptime guarantees, response times, resolution times, measurement methodology, credit mechanisms for SLA failures. Red flag: no SLA provisions in technology service contracts.

SCOPE CREEP PROTECTION:
Green flag: clearly defined scope of services with change order process for additions. Red flag: "such other services as reasonably required" without limit or pricing mechanism.

PAYMENT TERMS ANALYSIS:
Standard: Net 30 payment terms with late payment interest at statutory rate. Red flag: "payment immediately upon invoice", excessive late fees exceeding statutory limits, right to suspend services for disputed invoices.

TERMINATION FOR CONVENIENCE:
Standard: either party may terminate with 30-90 days written notice. Red flag: only one party has termination rights, or excessive termination fees equivalent to remaining contract value.

WARRANTIES AND DISCLAIMERS:
Standard: representations that services will be performed professionally and in conformity with specifications. Red flag: complete disclaimer of all warranties including fitness for purpose, or warranty period under 90 days.

LIMITATION OF LIABILITY:
Standard: cap at 12 months fees with mutual application. Exceptions for: gross negligence, willful misconduct, confidentiality breach, IP infringement. Red flag: no cap, or cap applies asymmetrically only to service provider."""
        },
        {
            "source": "Hidden Policies and Misleading Contract Terms",
            "jurisdiction": "Universal",
            "text": """HIDDEN POLICIES AND MISLEADING CONTRACT LANGUAGE DETECTION

COMMON DECEPTIVE DRAFTING TECHNIQUES:

1. BURIED PROVISIONS: Important limitations hidden in definitions sections or schedules rather than main body. Look for: definitions that create substantive obligations, schedules modifying main terms.

2. DOUBLE NEGATIVES: "shall not be unreasonable to withhold consent" = can withhold consent for any reason. "Not without limitation" language expanding scope.

3. SOLE DISCRETION LANGUAGE: "at our sole and absolute discretion", "as we see fit", "without liability" combined with broad powers. This removes accountability entirely.

4. EVERGREEN OBLIGATIONS: Obligations that survive termination without time limit: "confidentiality obligations shall survive indefinitely", "non-compete shall survive for 5 years" while other provisions expire at termination.

5. ASYMMETRIC NOTICE REQUIREMENTS: Company needs no notice to change terms, but user must give 90 days notice to cancel. Standard: same notice periods for both parties.

6. DEEMED CONSENT: "Continued use of service constitutes acceptance of changes" for material contract modifications. Standard: explicit written acceptance required for material changes.

7. UNILATERAL MODIFICATION: "We reserve the right to modify these terms at any time" with only email notice. Standard: material changes require affirmative consent.

8. BROAD ASSIGNMENT: Company can assign contract to any entity including competitors; you cannot assign without consent. Standard: mutual restriction on assignment or right of first refusal.

9. INDEMNIFICATION FOR NEGLIGENCE: Requiring indemnification even for the indemnitee's own negligence. Courts often limit this but it causes disputes.

10. CLASS ACTION WAIVERS: "You waive the right to participate in any class action lawsuit" - limits collective legal remedies. Often combined with mandatory arbitration."""
        }
    ]
    return knowledge


def scrape_all_sources(output_dir, max_sources=8):
    # scrapes legal sources and combines with built-in knowledge
    os.makedirs(output_dir, exist_ok=True)
    all_docs = []

    print("Loading built-in legal knowledge base...")
    builtin = get_builtin_legal_knowledge()
    all_docs.extend(builtin)
    print(f"  Loaded {len(builtin)} built-in knowledge documents")

    print("\nAttempting to scrape additional legal sources...")
    scraped_count = 0

    for source in LEGAL_SOURCES[:max_sources]:
        if scraped_count >= max_sources:
            break

        print(f"  Scraping: {source['source']}...")
        time.sleep(1.5)  # polite rate limiting

        if source.get("type") == "html":
            result = scrape_html(source["url"], source["source"], source["jurisdiction"])
            if result:
                all_docs.append(result)
                scraped_count += 1
                print(f"    OK — {len(result['text'])} chars")
            else:
                print(f"    Skipped")

    # save all collected documents
    output_file = os.path.join(output_dir, "legal_corpus.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    print(f"\nKnowledge base: {len(all_docs)} documents saved to {output_file}")
    return all_docs
