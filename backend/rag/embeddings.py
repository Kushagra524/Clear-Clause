import os
import hashlib
import numpy as np
import config

_embedder = None
_embedder_type = None


def _get_embedder():
    global _embedder, _embedder_type
    if _embedder is not None:
        return _embedder, _embedder_type

    # 1. Try FastEmbed (ONNX runtime, fastest & lightest on CPU)
    try:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(
            model_name=config.EMBEDDING_MODEL,
            cache_dir=os.path.join(config.KNOWLEDGE_BASE_DIR, "model_cache"),
        )
        _embedder_type = "fastembed"
        return _embedder, _embedder_type
    except Exception:
        pass

    # 2. Try SentenceTransformers (local cache only to prevent offline socket hangs)
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(
            "all-MiniLM-L6-v2",
            cache_folder=os.path.join(config.KNOWLEDGE_BASE_DIR, "model_cache"),
            local_files_only=True
        )
        _embedder_type = "sentence_transformers"
        return _embedder, _embedder_type
    except Exception:
        pass

    # 3. Deterministic offline fallback
    _embedder = "offline"
    _embedder_type = "offline"
    return _embedder, _embedder_type


def _normalize(vectors):
    vectors = np.array(vectors, dtype=np.float32)
    if len(vectors.shape) == 1:
        vectors = vectors.reshape(1, -1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


def _offline_hash_embed(text):
    # deterministic 384-dim pseudo-embedding for testing or offline environments
    h = hashlib.sha256(text.encode("utf-8")).digest()
    arr = np.frombuffer(h * 12, dtype=np.uint8)[:config.EMBEDDING_DIMENSION].astype(np.float32)
    norm = np.linalg.norm(arr)
    return (arr / (norm if norm > 0 else 1.0)).astype(np.float32)


def embed_texts(texts):
    embedder, emb_type = _get_embedder()
    try:
        if emb_type == "fastembed":
            return _normalize(list(embedder.embed(list(texts))))
        elif emb_type == "sentence_transformers":
            return _normalize(embedder.encode(list(texts), show_progress_bar=False))
    except Exception as err:
        print(f"[EMBEDDING ERROR] embed_texts fallback: {err}", flush=True)

    return np.vstack([_offline_hash_embed(t) for t in texts])


def embed_query(query):
    embedder, emb_type = _get_embedder()
    try:
        if emb_type == "fastembed":
            return _normalize(list(embedder.embed([query])))
        elif emb_type == "sentence_transformers":
            return _normalize(embedder.encode([query], show_progress_bar=False))
    except Exception as err:
        print(f"[EMBEDDING ERROR] embed_query fallback: {err}", flush=True)

    return _offline_hash_embed(query).reshape(1, -1)


class _Encoder:
    def encode(self, texts, show_progress_bar=False, **kwargs):
        return embed_texts(texts)


def get_model():
    return _Encoder()
