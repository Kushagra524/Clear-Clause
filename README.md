# ClearClause — Agentic RAG Legal Document Analyzer

> **Platform creators:** Kirti Kumari & Kushagra Srivastava

ClearClause is a production-grade legal document analyzer powered by **Agentic RAG** (Retrieval-Augmented Generation). Upload any contract in PDF, DOCX, or TXT format and receive an instant deep analysis from 7 specialized AI agents.

## What makes it unique

- **7 specialized ReAct agents** running in a reason-act-observe loop
- **4-stage hybrid retrieval**: FAISS semantic search + BM25 keyword search + Reciprocal Rank Fusion + Cross-Encoder re-ranking
- **GTE-small embeddings** — blazing fast 33M-parameter model, outperforms models 10x its size on retrieval benchmarks
- **Scraped multi-jurisdiction legal knowledge base** — Indian Contract Act, US law, UK law, GDPR, employment, real estate, fraud patterns
- **Semantic chunking with legal-aware fallback** — understands document structure AND meaning
- **Token-efficient hybrid** — local embeddings + HuggingFace Inference API for LLM (maximizes free tier)

## AI Pipeline

```
Document Upload
      ↓
Document Parser (PDF/DOCX/TXT)
      ↓
Semantic Chunker + Legal-Aware Fallback
      ↓
GTE-small Embeddings (local, 33M params)
      ↓
┌─────────────────────────────────┐
│  FAISS Vector Store             │ ← semantic search
│  BM25 Keyword Index             │ ← keyword search
│  Reciprocal Rank Fusion         │ ← merge results
│  Cross-Encoder Re-ranker        │ ← precision boost
└─────────────────────────────────┘
      ↓
7 ReAct Agents (Mistral-7B via HuggingFace API)
  1. Summary Agent
  2. Red Flag Detector
  3. Green Flag Detector
  4. Obligation Extractor
  5. Comparison Agent
  6. Risk Scoring Agent
  7. Negotiation Advisor
      ↓
Flask REST API → React + Vite Frontend
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS v4 |
| Backend API | Flask + Flask-CORS |
| Embedding model | GTE-small (thenlper/gte-small) — local inference |
| LLM | Mistral-7B-Instruct — HuggingFace Inference API |
| Vector store | FAISS (IndexFlatIP) |
| Keyword search | BM25 (rank_bm25) |
| Re-ranker | ms-marco-MiniLM-L-6-v2 (Cross-Encoder) — local |
| Document parsing | pdfplumber + PyPDF2 + python-docx |
| Web scraping | BeautifulSoup + requests |

## Project structure

```
clearclause/
├── backend/
│   ├── app.py                      # Flask entry point
│   ├── config.py                   # All configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Copy to .env and fill
│   ├── agents/
│   │   ├── orchestrator.py         # ReAct agent orchestrator
│   │   ├── red_flag_agent.py       # Detects risky clauses
│   │   ├── green_flag_agent.py     # Detects protective clauses
│   │   ├── summary_agent.py        # Plain-language summary
│   │   ├── obligation_agent.py     # Extracts duties & deadlines
│   │   ├── comparison_agent.py     # Compares vs. standard templates
│   │   ├── risk_scoring_agent.py   # 0-100 risk scoring
│   │   └── negotiation_agent.py    # Counter-term suggestions
│   ├── rag/
│   │   ├── embeddings.py           # GTE-small local embeddings
│   │   ├── vector_store.py         # FAISS index
│   │   ├── bm25_index.py           # BM25 keyword index
│   │   ├── retriever.py            # Hybrid retrieval + RRF
│   │   ├── reranker.py             # Cross-encoder re-ranker
│   │   └── chunker.py              # Semantic + legal-aware chunking
│   ├── llm/
│   │   └── mistral_client.py       # HuggingFace API client
│   ├── parsers/
│   │   └── document_parser.py      # PDF, DOCX, TXT extraction
│   ├── scraper/
│   │   ├── scrape_legal_data.py    # Web scraper + built-in corpus
│   │   └── build_knowledge_base.py # One-time KB builder script
│   └── knowledge_base/             # Auto-created on first run
│       ├── raw/                    # Scraped text files
│       ├── faiss_index/            # FAISS index files
│       └── bm25_index.pkl          # BM25 index file
└── artifacts/legal-document-analyzer/  # React frontend
    ├── src/App.tsx                 # Main React app
    ├── src/index.css               # Tailwind + theme
    ├── index.html
    ├── package.json
    └── vite.config.ts
```

## Setup & running

### 1. Get a HuggingFace API token (free)
1. Go to https://huggingface.co/settings/tokens
2. Create a token with `Inference` permission
3. Accept the Mistral-7B model terms at https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3

### 2. Backend setup

```bash
cd backend

# copy and fill environment variables
copy .env.example .env
# edit .env and add your HF_API_TOKEN

# create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# install dependencies
pip install -r requirements.txt

# build the knowledge base (one-time, ~2-3 minutes)
python scraper/build_knowledge_base.py

# start the Flask API
python app.py
# API runs at http://localhost:5000
```

### 3. Frontend setup

```bash
cd artifacts/legal-document-analyzer

# install dependencies
npm install

# start dev server
npm run dev
# Frontend runs at http://localhost:5173
```

### 4. Open the app
Navigate to **http://localhost:5173** and upload a legal document.

## API endpoints

```http
GET  /api/healthz              # Health check + KB stats
GET  /api/documents            # List all analyzed documents
POST /api/documents            # Analyze a new document
GET  /api/documents/:id        # Get single document analysis
GET  /api/documents/summary    # Library summary stats
```

### POST /api/documents — JSON body

```json
{
  "filename": "contract.txt",
  "mimeType": "text/plain",
  "content": "The full document text...",
  "size": 12345
}
```

### POST /api/documents — File upload

```bash
curl -X POST http://localhost:5000/api/documents \
  -F "file=@contract.pdf"
```

## Legal disclaimer

ClearClause provides informational analysis only. It is not a law firm, does not provide legal advice, and does not replace review by a qualified legal professional.

---

*Platform creators: **Kirti Kumari** & **Kushagra Srivastava***
