from rag.vector_store import VectorStore
from rag.bm25_index import BM25Index
from rag.embeddings import embed_query, embed_texts
from rag.reranker import rerank
from rag.chunker import legal_aware_chunk
import config


# reciprocal rank fusion to merge semantic + keyword results
def reciprocal_rank_fusion(semantic_results, bm25_results, k=60):
    score_map = {}

    for rank, result in enumerate(semantic_results):
        doc_key = result["metadata"]["text"][:100]
        if doc_key not in score_map:
            score_map[doc_key] = {"score": 0, "metadata": result["metadata"]}
        score_map[doc_key]["score"] += 1.0 / (k + rank + 1)

    for rank, result in enumerate(bm25_results):
        doc_key = result["metadata"]["text"][:100]
        if doc_key not in score_map:
            score_map[doc_key] = {"score": 0, "metadata": result["metadata"]}
        score_map[doc_key]["score"] += 1.0 / (k + rank + 1)

    fused = sorted(score_map.values(), key=lambda x: x["score"], reverse=True)
    return fused


class HybridRetriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.bm25_index = BM25Index()

    def index_document(self, text, embedder, doc_metadata=None):
        # chunks, embeds, and indexes a document into both stores
        chunks = legal_aware_chunk(text, embedder, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)

        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        chunk_records = []
        for i, chunk in enumerate(chunks):
            record = {
                "text": chunk["text"],
                "section": chunk.get("section", "Document"),
                "method": chunk.get("method", "unknown"),
                "chunk_index": i,
            }
            if doc_metadata:
                record.update(doc_metadata)
            if "context_prefix" in chunk:
                record["context_prefix"] = chunk["context_prefix"]
            chunk_records.append(record)

        self.vector_store.add(embeddings, chunk_records)
        self.bm25_index.add(texts, chunk_records)

        return len(chunks)

    def retrieve(self, query, top_k=None):
        # hybrid retrieval: semantic + bm25 + rrf + cross-encoder reranking
        retrieval_k = top_k or config.TOP_K_RETRIEVAL
        rerank_k = config.TOP_K_RERANKED

        query_embedding = embed_query(query)

        semantic_results = self.vector_store.search(query_embedding, top_k=retrieval_k)
        bm25_results = self.bm25_index.search(query, top_k=retrieval_k)

        fused = reciprocal_rank_fusion(semantic_results, bm25_results, k=config.RRF_K)

        if not fused:
            return []

        reranked = rerank(query, fused[:retrieval_k], top_k=rerank_k)

        return reranked

    def retrieve_for_document(self, document_text, queries):
        # runs multiple queries against the knowledge base for a single document
        all_results = {}
        for query_name, query_text in queries.items():
            results = self.retrieve(query_text)
            all_results[query_name] = results
        return all_results

    def save(self):
        self.vector_store.save()
        self.bm25_index.save()

    @property
    def stats(self):
        return {
            "vectors": self.vector_store.total_vectors,
            "bm25_docs": self.bm25_index.total_documents
        }
