---
title: ClearClause — AI Legal Document Analyzer
emoji: ⚖️
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# ClearClause — Agentic RAG Legal Document Analyzer

> **Platform creators:** Kirti Kumari & Kushagra Srivastava

ClearClause is a production-ready legal contract intelligence platform powered by **Agentic RAG** (Retrieval-Augmented Generation). Upload any contract in PDF, DOCX, or TXT format and receive instant, deep analysis from 7 specialized AI agents.

---

## 🚀 Live 1-Click Cloud Deployment (Browser Accessible)

ClearClause is built with a unified multi-stage Docker container that bundles both the React frontend and Python agentic backend into a single deployable service. Anyone can access the full UI directly in their browser.

### Option 1: Hugging Face Spaces (Recommended — 100% Free 16GB RAM)
1. Go to [Hugging Face Spaces](https://huggingface.co/new-space).
2. Set Space Name (e.g. `clearclause`).
3. Select **Docker** as the Space SDK.
4. Push this repository to your Space (or link your GitHub repository).
5. In **Settings -> Variables and Secrets**, add:
   - `LLM_API_KEY` = your Groq API key (free at [console.groq.com](https://console.groq.com/keys))
6. Done! Your app is live at `https://huggingface.co/spaces/YOUR_USERNAME/clearclause` and accessible to anyone via link!

### Option 2: Render
1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Web Service** -> connect your repository.
3. Choose **Docker** runtime.
4. Set Environment Variables:
   - `LLM_API_KEY` = your Groq or HuggingFace API key
   - `PORT` = `7860`
5. Deploy!

### Option 3: Local Docker
```bash
docker build -t clearclause .
docker run -p 7860:7860 -e LLM_API_KEY=your_key clearclause
```
Then visit **http://localhost:7860** in your browser.

---

## What makes ClearClause unique

- **7 Specialized ReAct Agents** running in a reason-act-observe loop:
  1. **Summary Agent**: Plain-language executive brief & document classification
  2. **Red Flag Detector**: Identifies 14+ high-risk traps (unlimited liability, auto-renewals, unilateral terms)
  3. **Green Flag Detector**: Detects protective clauses (mutual caps, fair termination, GDPR provisions)
  4. **Obligation Extractor**: Extracts actionable duties, deadlines, payment milestones, and notice periods
  5. **Comparison Agent**: Benchmarks against industry standard contract templates
  6. **Risk Scoring Agent**: 0–100 multi-dimensional risk score (financial, operational, legal, compliance)
  7. **Negotiation Advisor**: Provides exact counter-clause language and tactical negotiation advice
- **4-Stage Hybrid Retrieval**: FAISS semantic vector search + BM25 keyword search + Reciprocal Rank Fusion (RRF) + Cross-Encoder re-ranking
- **FastEmbed ONNX Inference**: Ultra-fast embeddings (BAAI/bge-small-en-v1.5) with minimal CPU and RAM usage
- **Blazing Fast Groq LLM Inference**: Llama-3.1-8b-instant engine delivering responses in 1-3 seconds
- **Scraped Multi-Jurisdiction Knowledge Base**: Pre-indexed Indian Contract Act 1872, US law, UK law, GDPR, employment, lease, and deceptive clause patterns
- **Unified Single-Port Web Service**: Production Flask server automatically serves compiled React SPA static assets

---

## AI Pipeline

```
Document Upload (PDF / DOCX / TXT)
      ↓
Document Parser (pdfplumber + PyPDF2 + python-docx)
      ↓
Semantic Chunker + Legal-Aware Structure Detection
      ↓
FastEmbed ONNX Vector Embeddings (BAAI/bge-small-en-v1.5)
      ↓
┌──────────────────────────────────────────────┐
│  FAISS Vector Store     ← Dense semantic     │
│  BM25 Keyword Index     ← Exact lexical      │
│  Reciprocal Rank Fusion ← Rank aggregation   │
│  Cross-Encoder Reranker ← Precision rerank   │
└──────────────────────────────────────────────┘
      ↓
7 Parallel ReAct Agents (Groq / HuggingFace Llama-3.1)
  1. Summary Agent
  2. Red Flag Detector
  3. Green Flag Detector
  4. Obligation Extractor
  5. Comparison Agent
  6. Risk Scoring Agent
  7. Negotiation Advisor
      ↓
Single-Port Flask REST API + React 18 Frontend
```

---

## Tech Stack & Performance Optimizations

| Layer | Technology | Optimization / Benefit |
|-------|------------|------------------------|
| **Frontend** | React 18 + Vite + TypeScript + Tailwind CSS v4 | Sub-second load, responsive, instant tab switching |
| **Backend API** | Flask + Flask-CORS + Gunicorn | Threaded concurrent workers, zero bloat |
| **LLM Inference** | Groq Llama-3.1-8b-instant (or HF Inference) | **500+ tokens/sec** — completes full analysis in 2-3s |
| **Embedding Engine** | FastEmbed (`bge-small-en-v1.5`) | **ONNX runtime** — 3x faster than PyTorch on CPU, <100MB RAM |
| **Vector Store** | FAISS (`IndexFlatIP`) | Real-time exact inner product cosine search |
| **Lexical Search** | BM25 (`rank_bm25`) | Legal terminology and specific clause matching |
| **Document Parsers** | `pdfplumber`, `PyPDF2`, `python-docx` | Dual-engine PDF extraction with layout and table preservation |

---

## Project Structure

```
clearclause/
├── Dockerfile                          # Multi-stage production container
├── .dockerignore                       # Docker build exclusions
├── README.md                           # Documentation & HF Spaces metadata
├── backend/
│   ├── app.py                          # Unified Flask app & SPA static server
│   ├── config.py                       # Configuration & environment loader
│   ├── requirements.txt                # Lean Python dependencies
│   ├── .env.example                    # Sample environment variables
│   ├── agents/
│   │   ├── orchestrator.py             # 7-Agent parallel orchestrator
│   │   ├── summary_agent.py            # Summary & document classification
│   │   ├── red_flag_agent.py           # Unfavorable terms & risks
│   │   ├── green_flag_agent.py         # Protective provisions
│   │   ├── obligation_agent.py         # Party commitments & deadlines
│   │   ├── comparison_agent.py         # Standard contract benchmarking
│   │   ├── risk_scoring_agent.py       # 0-100 numerical risk scoring
│   │   └── negotiation_agent.py        # Counter-clauses & strategies
│   ├── rag/
│   │   ├── embeddings.py               # FastEmbed ONNX embeddings
│   │   ├── vector_store.py             # FAISS index
│   │   ├── bm25_index.py               # BM25 keyword index
│   │   ├── retriever.py                # Hybrid RRF retriever
│   │   ├── reranker.py                 # Cross-encoder re-ranker
│   │   └── chunker.py                  # Semantic & legal-aware chunking
│   ├── llm/
│   │   └── mistral_client.py           # High-speed LLM client
│   ├── parsers/
│   │   └── document_parser.py          # PDF, DOCX, TXT extraction
│   └── knowledge_base/                 # Legal corpus, FAISS & BM25 indices
└── artifacts/legal-document-analyzer/  # React frontend
    ├── src/
    │   ├── App.tsx                     # Main React application
    │   ├── index.css                   # Tailwind theme styles
    │   └── main.tsx                    # React DOM entrypoint
    ├── index.html                      # HTML template
    ├── package.json                    # Frontend dependencies
    └── vite.config.ts                  # Vite build configuration
```

---

## API Endpoints

```http
GET  /api/healthz              # Health check + Knowledge Base stats
GET  /api/documents            # List all analyzed documents
POST /api/documents            # Analyze a new document (File or JSON)
GET  /api/documents/:id        # Get complete analysis by ID
GET  /api/documents/summary    # Library statistics
```

---

## Legal Disclaimer

ClearClause provides informational analysis only. It is not a law firm, does not provide legal advice, and does not replace review by a qualified legal professional.

---

*Platform creators: **Kirti Kumari** & **Kushagra Srivastava***
