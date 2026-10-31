import time
import traceback
from agents.red_flag_agent import detect_red_flags
from agents.green_flag_agent import detect_green_flags
from agents.summary_agent import generate_summary
from agents.obligation_agent import extract_obligations
from agents.comparison_agent import compare_against_standards
from agents.risk_scoring_agent import score_risks
from agents.negotiation_agent import suggest_negotiations
from rag.retriever import HybridRetriever
from rag.embeddings import get_model


# the react orchestrator reasons about which agents to invoke and in what order
class AgentOrchestrator:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.execution_log = []

    def _log_step(self, agent_name, action, result_summary, duration):
        self.execution_log.append({
            "agent": agent_name,
            "action": action,
            "result": result_summary,
            "duration_ms": round(duration * 1000),
            "timestamp": time.time()
        })

    def _reason(self, step, context):
        # react reasoning: decide what to do next based on current state
        reasoning = {
            "thought": f"Step {step}: {context}",
            "action": None,
            "observation": None
        }
        return reasoning

    def analyze_document(self, document_text, filename="document"):
        # full react loop: reason -> act -> observe -> repeat for each agent
        self.execution_log = []
        results = {
            "filename": filename,
            "status": "processing",
            "agents_completed": [],
            "agents_failed": [],
        }

        # step 1: reason about what context we need
        self._reason(1, "Need to retrieve relevant legal knowledge for this document type")

        # retrieve legal knowledge for different aspects
        queries = {
            "red_flags": f"risky unfavorable clauses in {filename} contract agreement",
            "green_flags": f"protective favorable clauses in {filename} contract agreement",
            "obligations": f"obligations duties deadlines payment terms in legal contract",
            "standards": f"standard contract clauses best practices legal agreement template",
            "negotiation": f"contract negotiation strategies counter-terms alternative language"
        }

        start = time.time()
        retrieved_context = self.retriever.retrieve_for_document(document_text, queries)
        self._log_step("retriever", "hybrid_retrieval", f"Retrieved context for {len(queries)} queries", time.time() - start)

        # step 2: run summary agent first to understand what we're dealing with
        self._reason(2, "Generate plain-language summary to understand document type and scope")
        try:
            start = time.time()
            summary_result = generate_summary(
                document_text,
                retrieved_context.get("standards", [])
            )
            results["summary"] = summary_result
            results["agents_completed"].append("summary")
            self._log_step("summary_agent", "generate_summary", "Summary generated", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "summary", "error": str(err)})
            results["summary"] = {"summary": "Summary generation failed. Please review the document manually.", "document_type": "other", "parties": [], "key_terms": []}

        # step 3: detect red flags (critical path)
        self._reason(3, "Scan for risky and unfavorable clauses — this is the most critical analysis")
        try:
            start = time.time()
            red_flags = detect_red_flags(
                document_text,
                retrieved_context.get("red_flags", [])
            )
            results["red_flags"] = red_flags
            results["agents_completed"].append("red_flags")
            self._log_step("red_flag_agent", "detect_red_flags", f"Found {len(red_flags)} red flags", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "red_flags", "error": str(err)})
            red_flags = []
            results["red_flags"] = []

        # step 4: detect green flags
        self._reason(4, "Identify protective and favorable clauses to balance the risk view")
        try:
            start = time.time()
            green_flags = detect_green_flags(
                document_text,
                retrieved_context.get("green_flags", [])
            )
            results["green_flags"] = green_flags
            results["agents_completed"].append("green_flags")
            self._log_step("green_flag_agent", "detect_green_flags", f"Found {len(green_flags)} green flags", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "green_flags", "error": str(err)})
            green_flags = []
            results["green_flags"] = []

        # step 5: extract obligations
        self._reason(5, "Extract duties, deadlines, and payment terms from the document")
        try:
            start = time.time()
            obligations = extract_obligations(
                document_text,
                retrieved_context.get("obligations", [])
            )
            results["obligations"] = obligations
            results["agents_completed"].append("obligations")
            self._log_step("obligation_agent", "extract_obligations", f"Found {len(obligations)} obligations", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "obligations", "error": str(err)})
            results["obligations"] = []

        # step 6: compare against standards
        self._reason(6, "Compare document against standard contract templates and best practices")
        try:
            start = time.time()
            comparisons = compare_against_standards(
                document_text,
                retrieved_context.get("standards", [])
            )
            results["comparisons"] = comparisons
            results["agents_completed"].append("comparisons")
            self._log_step("comparison_agent", "compare_standards", f"Compared {len(comparisons)} clause types", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "comparisons", "error": str(err)})
            results["comparisons"] = []

        # step 7: score risks using accumulated data from previous agents
        self._reason(7, "Calculate risk scores using red flags, green flags, and comparison data")
        try:
            start = time.time()
            risk_scores = score_risks(
                document_text,
                retrieved_context.get("red_flags", []),
                red_flags=red_flags,
                green_flags=green_flags
            )
            results["risk_scores"] = risk_scores
            results["agents_completed"].append("risk_scoring")
            self._log_step("risk_scoring_agent", "score_risks", f"Overall score: {risk_scores.get('overall_score', 'N/A')}", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "risk_scoring", "error": str(err)})
            results["risk_scores"] = {"overall_score": 50, "risk_level": "medium", "dimensions": [], "score_explanation": "Scoring failed, defaulting to medium risk."}

        # step 8: generate negotiation advice based on red flags
        self._reason(8, "Generate negotiation suggestions for each identified red flag")
        try:
            start = time.time()
            negotiations = suggest_negotiations(
                document_text,
                retrieved_context.get("negotiation", []),
                red_flags=red_flags
            )
            results["negotiations"] = negotiations
            results["agents_completed"].append("negotiations")
            self._log_step("negotiation_agent", "suggest_negotiations", f"Generated {len(negotiations)} suggestions", time.time() - start)
        except Exception as err:
            results["agents_failed"].append({"agent": "negotiations", "error": str(err)})
            results["negotiations"] = []

        # final reasoning step
        self._reason(9, f"Analysis complete. {len(results['agents_completed'])}/7 agents succeeded.")

        # determine overall risk level from scoring
        risk_level = results.get("risk_scores", {}).get("risk_level", "medium")
        overall_score = results.get("risk_scores", {}).get("overall_score", 50)

        results["status"] = "completed"
        results["risk_level"] = risk_level
        results["overall_score"] = overall_score
        results["execution_log"] = self.execution_log
        results["document_type"] = results.get("summary", {}).get("document_type", "other")
        results["key_terms"] = results.get("summary", {}).get("key_terms", [])

        return results
