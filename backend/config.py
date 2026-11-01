import os
from dotenv import load_dotenv

load_dotenv()

# huggingface api token
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# embedding model runs locally with FastEmbed (ONNX runtime, ultra fast and lightweight)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIMENSION = 384

# llm api configuration - supports Groq, HuggingFace, or custom OpenAI-compatible endpoint
LLM_API_KEY = (
    os.getenv("LLM_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or os.getenv("GROQ_Token")
    or os.getenv("GROQ_TOKEN")
    or os.getenv("HF_API_TOKEN")
    or ""
).strip()

LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.15"))

# API endpoint: default to Groq (ultra fast, high free-tier limits)
LLM_API_URL = os.getenv("LLM_API_URL", "")
if not LLM_API_URL:
    if LLM_API_KEY.startswith("gsk_"):
        LLM_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    elif LLM_API_KEY.startswith("hf_"):
        LLM_API_URL = "https://router.huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/v1/chat/completions"
    else:
        LLM_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# cross-encoder reranker (disabled by default for CPU performance and minimal RAM)
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

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
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", "7860")))
APP_ENV = os.getenv("APP_ENV", "production")
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20mb

# supported file types
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

# public deployment config
_default_cors = [
    "*",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
_cors_env = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = [
    origin.strip()
    for origin in (_cors_env.split(",") if _cors_env else [])
    if origin.strip()
]
if not CORS_ORIGINS:
    CORS_ORIGINS = _default_cors
