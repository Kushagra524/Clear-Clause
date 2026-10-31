import os
import numpy as np
import config

# singleton so the model loads once, on first use
_model = None


def _get_fastembed():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(
            model_name=config.EMBEDDING_MODEL,
            cache_dir=os.path.join(config.KNOWLEDGE_BASE_DIR, "model_cache"),
        )
    return _model


def _normalize(vectors):
    vectors = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


def embed_texts(texts):
    # encodes a list of strings into dense vectors
    return _normalize(list(_get_fastembed().embed(list(texts))))


def embed_query(query):
    # single query embedding for retrieval
    return _normalize(list(_get_fastembed().embed([query])))


class _Encoder:
    # adapter so code written for sentence-transformers (chunker) keeps working
    def encode(self, texts, show_progress_bar=False, **kwargs):
        return embed_texts(texts)


def get_model():
    return _Encoder()