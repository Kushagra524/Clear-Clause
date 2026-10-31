from sentence_transformers import SentenceTransformer
import numpy as np
import config

# singleton to avoid reloading the model on every call
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def embed_texts(texts):
    # encodes a list of strings into dense vectors
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embeddings, dtype=np.float32)


def embed_query(query):
    # single query embedding for retrieval
    model = get_model()
    embedding = model.encode([query], show_progress_bar=False, normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32)
