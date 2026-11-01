import os
import config

# singleton reranker model, loaded only if enabled
_reranker = None
USE_RERANKER = os.getenv("USE_RERANKER", "false").lower() == "true"


def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(config.RERANKER_MODEL, max_length=512)
        except Exception as err:
            print(f"[RERANKER WARNING] Could not load CrossEncoder: {err}. Falling back to RRF rankings.", flush=True)
            _reranker = False
    return _reranker if _reranker is not False else None


def rerank(query, documents, top_k=5):
    # scores each document against the query and returns the best ones
    if not documents:
        return []

    # reranker is off by default to save memory and CPU on free-tier servers
    if not USE_RERANKER:
        for doc in documents:
            doc.setdefault("rerank_score", 0.0)
        return documents[:top_k]

    reranker = get_reranker()
    if not reranker:
        for doc in documents:
            doc.setdefault("rerank_score", 0.0)
        return documents[:top_k]

    try:
        pairs = [[query, doc["metadata"]["text"]] for doc in documents]
        scores = reranker.predict(pairs)
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])
        ranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_k]
    except Exception as err:
        print(f"[RERANKER ERROR] Prediction failed: {err}", flush=True)
        return documents[:top_k]
