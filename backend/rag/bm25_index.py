import pickle
import os
import re
from rank_bm25 import BM25Okapi
import config


class BM25Index:
    def __init__(self, index_path=None):
        self.index_path = index_path or config.BM25_INDEX_PATH
        self.bm25 = None
        self.documents = []
        self.metadata = []
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.documents = data["documents"]
                self.metadata = data["metadata"]

    def _tokenize(self, text):
        # simple whitespace + punctuation tokenizer for legal text
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return tokens

    def build(self, texts, chunks_metadata):
        # builds bm25 index from a list of text chunks
        self.documents = texts
        self.metadata = chunks_metadata
        tokenized = [self._tokenize(doc) for doc in texts]
        self.bm25 = BM25Okapi(tokenized)

    def add(self, texts, chunks_metadata):
        # appends new documents and rebuilds the index
        self.documents.extend(texts)
        self.metadata.extend(chunks_metadata)
        tokenized = [self._tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, top_k=10):
        # returns top_k keyword-matched documents
        if self.bm25 is None or len(self.documents) == 0:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "score": float(scores[idx]),
                    "metadata": self.metadata[idx]
                })

        return results

    def save(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "documents": self.documents,
                "metadata": self.metadata
            }, f)

    @property
    def total_documents(self):
        return len(self.documents)
