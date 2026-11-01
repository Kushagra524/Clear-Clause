import os
import time
from concurrent.futures import ThreadPoolExecutor
from agents.red_flag_agent import detect_red_flags
from agents.green_flag_agent import detect_green_flags
from agents.summary_agent import generate_summary
from agents.obligation_agent import extract_obligations
from agents.comparison_agent import compare_against_standards
from agents.risk_scoring_agent import score_risks
from agents.negotiation_agent import suggest_negotiations
from rag.retriever import HybridRetriever

# how many agents may call the llm at the same time (lower this if you see rate-limit errors)
AGENT_WORKERS = int(os.getenv("AGENT_WORKERS", "4"))


def _timed(fn):
    # runs one agent and returns (value, error, seconds)
    start = time.time()
    try:
        return fn(), None, time.time() - start
    except Exception as err:
        return None, err, time.time() - start


class AgentOrchestrator:
    def __init__(self):
        self.retriever = HybridRetriever()

    def _run_stage(self, steps, results, log):
        # runs a group of independent agents in parallel and records their results
        with ThreadPoolExecutor(max_workers=AGENT_WORKERS) as pool:
            futures = [(step, pool.submit(_timed, step["fn"])) for step in steps]
            for step, future in futures:
                value, err, seconds = future.result()
                if err is None:
                    results[step["key"]] = value
                    results["agents_completed"].append(step["name"])
                    summary = step["describe"](value)
                else:
                    print(f"[AGENT ERROR] {step['name']}: {err}", flush=True)
                    results[step["key"]] = step["fallback"]
                    results["agents_failed"].append({"agent": step["name"], "error": str(err)})
                    summary = f"Failed: {err}"
                log.append({
                    "agent": step["agent"],
                    "action": step["action"],
                    "result": summary,
                    "duration_ms": round(seconds * 1000),
                    "timestamp": time.time(),
                })

    def analyze_document(self, document_text, filename="document"):
        log = []
        results = {
            "filename": filename,
            "status": "processing",
            "agents_completed": [],
            "agents_failed": [],
        }

        # retrieve legal knowledge for the different
        # retrieve legal knowledge for the different analysis aspects
        
        queries = {
            "red_flags": f"risky unfavorable clauses in {filename} contract agreement",
            "green_flags": f"protective favorable clauses in {filename} contract agreement",
            "obligations": "obligations duties deadlines payment terms in legal contract",
            "standards": "standard contract clauses best practices legal agreement template",
            "negotiation": "contract negotiation strategies counter-terms alternative language",
        }
        start = time.time()
        ctx = self.retriever.retrieve_for_document(document_text, queries)
        log.append({
            "agent": "retriever",
            "action": "hybrid_retrieval",
            "result": f"Retrieved context for {len(queries)} queries",
            "duration_ms": round((time.time() - start) * 1000),
            "timestamp": time.time(),
        })

        # stage 1: agents that only need the document and retrieved context
        stage1 = [
            {"key": "summary", "name": "summary", "agent": "summary_agent", "action": "generate_summary",
             "fn": lambda: generate_summary(document_text, ctx.get("standards", [])),
             "describe": lambda v: "Summary generated",
             "fallback": {"summary": "Summary generation failed. Please review the document manually.",
                          "document_type": "other", "parties": [], "key_terms": []}},
            {"key": "red_flags", "name": "red_flags", "agent": "red_flag_agent", "action": "detect_red_flags",
             "fn": lambda: detect_red_flags(document_text, ctx.get("red_flags", [])),
             "describe": lambda v: f"Found {len(v)} red flags", "fallback": []},
            {"key": "green_flags", "name": "green_flags", "agent": "green_flag_agent", "action": "detect_green_flags",
             "fn": lambda: detect_green_flags(document_text, ctx.get("green_flags", [])),
             "describe": lambda v: f"Found {len(v)} green flags", "fallback": []},
            {"key": "obligations", "name": "obligations", "agent": "obligation_agent", "action": "extract_obligations",
             "fn": lambda: extract_obligations(document_text, ctx.get("obligations", [])),
             "describe": lambda v: f"Found {len(v)} obligations", "fallback": []},
            {"key": "comparisons", "name": "comparisons", "agent": "comparison_agent", "action": "compare_standards",
             "fn": lambda: compare_against_standards(document_text, ctx.get("standards", [])),
             "describe": lambda v: f"Compared {len(v)} clause types", "fallback": []},
        ]
        self._run_stage(stage1, results, log)

        red_flags = results.get("red_flags", [])
        green_flags = results.get("green_flags", [])

        # stage 2: agents that build on the red and green flags
        stage2 = [
            {"key": "risk_scores", "name": "risk_scoring", "agent": "risk_scoring_agent", "action": "score_risks",
             "fn": lambda: score_risks(document_text, ctx.get("red_flags", []),
                                       red_flags=red_flags, green_flags=green_flags),
             "describe": lambda v: f"Overall score: {v.get('overall_score', 'N/A')}",
             "fallback": {"overall_score": 50, "risk_level": "medium", "dimensions": [],
                          "score_explanation": "Scoring failed, defaulting to medium risk."}},
            {"key": "negotiations", "name": "negotiations", "agent": "negotiation_agent", "action": "suggest_negotiations",
             "fn": lambda: suggest_negotiations(document_text, ctx.get("negotiation", []), red_flags=red_flags),
             "describe": lambda v: f"Generated {len(v)} suggestions", "fallback": []},
        ]
        self._run_stage(stage2, results, log)

        risk_scores = results.get("risk_scores", {})
        results["status"] = "completed"
        results["risk_level"] = risk_scores.get("risk_level", "medium")
        results["overall_score"] = risk_scores.get("overall_score", 50)
        results["execution_log"] = log
        results["document_type"] = results.get("summary", {}).get("document_type", "other")
        results["key_terms"] = results.get("summary", {}).get("key_terms", [])
        return results