from sentence_transformers import CrossEncoder
import config

# singleton reranker model
_reranker = None


def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(config.RERANKER_MODEL, max_length=512)
    return _reranker


def rerank(query, documents, top_k=5):
    # scores each document against the query and returns the best ones
    if not documents:
        return []

    reranker = get_reranker()
    pairs = [[query, doc["metadata"]["text"]] for doc in documents]
    scores = reranker.predict(pairs)

    for i, doc in enumerate(documents):
        doc["rerank_score"] = float(scores[i])

    ranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]
