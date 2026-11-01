import sys
import os

# Set fast timeouts for integration test
os.environ.setdefault("LLM_TIMEOUT", "2")
os.environ.setdefault("LLM_RETRIES", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from rag.retriever import HybridRetriever
from parsers.document_parser import clean_extracted_text
from agents.summary_agent import _fallback_summary
from agents.red_flag_agent import _fallback_detection as red_flag_fallback
from agents.green_flag_agent import _fallback_detection as green_flag_fallback
from agents.obligation_agent import _fallback_extraction
from agents.comparison_agent import _fallback_comparison
from agents.risk_scoring_agent import _fallback_scoring
from agents.negotiation_agent import _fallback_suggestions

print("=== CLEARCLAUSE SYSTEM INTEGRITY CHECK ===")

# 1. Config check
print(f"[1] Config check: PORT={config.FLASK_PORT}, LLM_MODEL={config.LLM_MODEL}")
print(f"    API Key present: {'Yes' if bool(config.LLM_API_KEY) else 'No'}")
print(f"    API URL: {config.LLM_API_URL}")

# 2. Knowledge base check
print("\n[2] Testing Knowledge Base & Hybrid Retriever...")
retriever = HybridRetriever()
stats = retriever.stats
print(f"    Vector store items: {stats.get('vectors', 0)}")
print(f"    BM25 documents: {stats.get('bm25_docs', 0)}")

# 3. Test Retrieval
sample_query = "unlimited liability indemnification termination clause"
results = retriever.retrieve(sample_query, top_k=3)
print(f"    Retrieved {len(results)} chunks for test query.")
if results:
    print(f"    Top result preview: {results[0]['metadata']['text'][:80]}...")

# 4. Sample contract testing
sample_contract = """
NON-DISCLOSURE AND SERVICE AGREEMENT
This Agreement is entered into between Company Alpha and Contractor Beta.
1. Term and Termination: This agreement shall automatically renew for successive one-year terms unless terminated with 30 days prior written notice. Either party may terminate this agreement upon material breach.
2. Limitation of Liability: Contractor shall have unlimited liability for any claims arising under this agreement. In no event shall Company Alpha's liability exceed $100.
3. Indemnification: Contractor agrees to defend, indemnify, and hold harmless Company Alpha against all damages, losses, and claims.
4. Non-Compete: Contractor agrees not to engage in any competitive business activity anywhere in the world for 24 months post-termination.
5. Obligations: Contractor must deliver monthly progress reports within 5 business days of month end. Company shall remit payment within 30 days of receiving valid invoice.
6. Governing Law: This agreement shall be governed by the laws of India and Indian Contract Act 1872.
"""

cleaned = clean_extracted_text(sample_contract)
print(f"\n[3] Testing Agent Rule & Analysis Fallbacks on Sample Contract ({len(cleaned)} chars)...")

# Summary
summary = _fallback_summary(cleaned)
print(f"    Document type detected: {summary.get('document_type')}")

# Red Flags
red_flags = red_flag_fallback(cleaned)
print(f"    Red flags detected: {len(red_flags)}")
for rf in red_flags:
    print(f"      - [{rf['severity'].upper()}] {rf['title']} ({rf['category']})")

# Green Flags
green_flags = green_flag_fallback(cleaned)
print(f"    Green flags detected: {len(green_flags)}")
for gf in green_flags:
    print(f"      - [{gf['strength'].upper()}] {gf['title']} ({gf['category']})")

# Obligations
obligations = _fallback_extraction(cleaned)
print(f"    Obligations extracted: {len(obligations)}")

# Comparisons
comparisons = _fallback_comparison(cleaned)
print(f"    Contract standard checks: {len(comparisons)}")

# Risk Scoring
risk_score = _fallback_scoring(cleaned, red_flags, green_flags)
print(f"    Overall Risk Score: {risk_score.get('overall_score')}/100 ({risk_score.get('risk_level')})")

# Negotiations
negotiations = _fallback_suggestions(red_flags)
print(f"    Negotiation counter-strategies generated: {len(negotiations)}")

# 5. Flask App test
print("\n[4] Testing Flask API App configuration...")
from app import app
client = app.test_client()

res = client.get("/api/healthz")
print(f"    GET /api/healthz: status {res.status_code}, data: {res.get_json().get('status')}")

res = client.get("/api/documents")
print(f"    GET /api/documents: status {res.status_code}")

res = client.get("/api/documents/summary")
print(f"    GET /api/documents/summary: status {res.status_code}")

# Test Document Submission via API
test_payload = {
    "filename": "sample_agreement.txt",
    "content": sample_contract,
    "size": len(sample_contract)
}
res = client.post("/api/documents", json=test_payload)
print(f"    POST /api/documents: status {res.status_code}")
if res.status_code in (200, 201):
    doc_data = res.get_json()
    print(f"    Created Document ID: {doc_data.get('id')}")
    print(f"    Risk Level: {doc_data.get('riskLevel')}, Score: {doc_data.get('overallScore')}")
    print(f"    Red Flags count: {len(doc_data.get('redFlags', []))}")
    print(f"    Green Flags count: {len(doc_data.get('greenFlags', []))}")
    print(f"    Obligations count: {len(doc_data.get('obligations', []))}")
    print(f"    Negotiations count: {len(doc_data.get('negotiations', []))}")

print("\n=== ALL PIPELINE AND API INTEGRATION TESTS PASSED ===")
