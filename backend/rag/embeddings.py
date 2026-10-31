import os
import numpy as np
import requests
import config

# embedding mode: "api" uses huggingface (low memory), "local" loads the model in-process
EMBED_MODE = os.getenv("EMBED_MODE", "local").lower()
API_URL = f"https://router.huggingface.co/hf-inference/models/{config.EMBEDDING_MODEL}/pipeline/feature-extraction"

# singleton to avoid reloading the model on every call (local mode only)
_model = None


def get_model():
    global _model
    if _model is None:
        # imported here so torch is never loaded in api mode
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(1)
        _model = SentenceTransformer(config.EMBEDDING_MODEL, device="cpu")
    return _model


def _normalize(vectors):
    vectors = np.array(vectors, dtype=np.float32)
    # some endpoints return per-token vectors, so average them into one vector per text
    if vectors.ndim == 3:
        vectors = vectors.mean(axis=1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


def _embed_api(texts):
    # sends texts to huggingface in small batches
    headers = {"Authorization": f"Bearer {config.HF_API_TOKEN}"}
    all_vectors = []
    for start in range(0, len(texts), 16):
        batch = texts[start:start + 16]
        last_error = "unknown error"
        for attempt in range(3):
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": batch, "options": {"wait_for_model": True}},
                timeout=120,
            )
            if response.status_code in (429, 503):
                last_error = f"HTTP {response.status_code}"
                import time
                time.sleep(5 * (attempt + 1))
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"Embedding API HTTP {response.status_code}: {response.text[:300]}")
            all_vectors.extend(response.json())
            break
        else:
            raise RuntimeError(f"Embedding API failed after retries: {last_error}")
    return _normalize(all_vectors)


def embed_texts(texts):
    # encodes a list of strings into dense vectors
    if EMBED_MODE == "api":
        return _embed_api(list(texts))
    model = get_model()
    embeddings = model.encode(
        texts, show_progress_bar=False, normalize_embeddings=True, batch_size=16
    )
    return np.array(embeddings, dtype=np.float32)


def embed_query(query):
    # single query embedding for retrieval
    if EMBED_MODE == "api":
        return _embed_api([query])
    model = get_model()
    embedding = model.encode([query], show_progress_bar=False, normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32)