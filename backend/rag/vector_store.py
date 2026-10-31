import faiss
import numpy as np
import os
import json
import config


class VectorStore:
    def __init__(self, index_path=None):
        self.dimension = config.EMBEDDING_DIMENSION
        self.index_path = index_path or config.FAISS_INDEX_PATH
        self.index = None
        self.metadata = []
        self._load_or_create()

    def _load_or_create(self):
        # loads existing index or creates a new one
        index_file = os.path.join(self.index_path, "index.faiss")
        meta_file = os.path.join(self.index_path, "metadata.json")

        if os.path.exists(index_file) and os.path.exists(meta_file):
            self.index = faiss.read_index(index_file)
            with open(meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []

    def add(self, embeddings, chunks_metadata):
        # adds vectors and their associated metadata to the store
        if len(embeddings) == 0:
            return
        self.index.add(embeddings)
        self.metadata.extend(chunks_metadata)

    def search(self, query_embedding, top_k=10):
        # returns top_k most similar chunks with scores
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            results.append({
                "score": float(score),
                "metadata": self.metadata[idx]
            })

        return results

    def save(self):
        # persists index and metadata to disk
        os.makedirs(self.index_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.index_path, "index.faiss"))
        with open(os.path.join(self.index_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)

    @property
    def total_vectors(self):
        return self.index.ntotal if self.index else 0
