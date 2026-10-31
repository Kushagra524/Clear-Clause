import os
from dotenv import load_dotenv

load_dotenv()

# huggingface api token for mistral inference
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# embedding model runs locally
EMBEDDING_MODEL = "thenlper/gte-small"
EMBEDDING_DIMENSION = 384

# llm via huggingface inference api
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.15

# cross-encoder reranker runs locally
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# rag pipeline settings
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_RETRIEVAL = 15
TOP_K_RERANKED = 5
RRF_K = 60

# faiss index paths
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
FAISS_INDEX_PATH = os.path.join(KNOWLEDGE_BASE_DIR, "faiss_index")
RAW_DATA_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "raw")
BM25_INDEX_PATH = os.path.join(KNOWLEDGE_BASE_DIR, "bm25_index.pkl")

# flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20mb

# supported file types
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
