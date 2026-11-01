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