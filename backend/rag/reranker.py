import os
import config

# singleton reranker model, loaded only if enabled
_reranker = None
USE_RERANKER = os.getenv("USE_RERANKER", "false").lower() == "true"


def get_reranker():
    global _reranker
    if _reranker is None:
        # imported here so torch isn't loaded unless the reranker is actually used
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(config.RERANKER_MODEL, max_length=512)
    return _reranker


def rerank(query, documents, top_k=5):
    # scores each document against the query and returns the best ones
    if not documents:
        return []

    # reranker is off by default to save memory on small servers
    if not USE_RERANKER:
        for doc in documents:
            doc.setdefault("rerank_score", 0.0)
        return documents[:top_k]

    reranker = get_reranker()
    pairs = [[query, doc["metadata"]["text"]] for doc in documents]
    scores = reranker.predict(pairs)

    for i, doc in enumerate(documents):
        doc["rerank_score"] = float(scores[i])

    ranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]