"""
Run once to build the FAISS + BM25 knowledge base from scraped legal data.
Usage: python build_knowledge_base.py
"""
import sys
import os
import json

# add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from scraper.scrape_legal_data import scrape_all_sources
from rag.embeddings import embed_texts, get_model
from rag.vector_store import VectorStore
from rag.bm25_index import BM25Index
from rag.chunker import legal_aware_chunk


def build():
    print("=" * 60)
    print("ClearClause — Building Legal Knowledge Base")
    print("=" * 60)

    # step 1: scrape and load legal data
    print("\n[1/4] Collecting legal knowledge...")
    raw_dir = config.RAW_DATA_DIR
    os.makedirs(raw_dir, exist_ok=True)

    corpus_file = os.path.join(raw_dir, "legal_corpus.json")

    if os.path.exists(corpus_file):
        print(f"  Found existing corpus at {corpus_file}")
        with open(corpus_file, "r", encoding="utf-8") as f:
            all_docs = json.load(f)
        print(f"  Loaded {len(all_docs)} documents")
    else:
        all_docs = scrape_all_sources(raw_dir)

    # step 2: initialize stores
    print("\n[2/4] Initializing vector and keyword stores...")
    os.makedirs(config.FAISS_INDEX_PATH, exist_ok=True)
    vector_store = VectorStore(config.FAISS_INDEX_PATH)
    bm25_index = BM25Index(config.BM25_INDEX_PATH)

    # step 3: chunk and embed all documents
    print("\n[3/4] Chunking and embedding legal documents...")
    embedder = get_model()

    all_texts = []
    all_metadata = []
    total_chunks = 0

    for doc in all_docs:
        text = doc.get("text", "")
        if not text or len(text) < 100:
            continue

        source = doc.get("source", "Unknown")
        jurisdiction = doc.get("jurisdiction", "Unknown")
        print(f"  Processing: {source} ({len(text)} chars)")

        chunks = legal_aware_chunk(
            text,
            embedder,
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )

        for chunk in chunks:
            all_texts.append(chunk["text"])
            all_metadata.append({
                "text": chunk["text"],
                "section": chunk.get("section", ""),
                "source": source,
                "jurisdiction": jurisdiction,
                "chunk_index": len(all_metadata)
            })

        total_chunks += len(chunks)
        print(f"    -> {len(chunks)} chunks")

    print(f"\n  Total: {total_chunks} chunks from {len(all_docs)} documents")

    # step 4: build indexes
    print("\n[4/4] Building FAISS and BM25 indexes...")

    # embed in batches to avoid memory issues
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(all_texts), batch_size):
        batch = all_texts[i:i + batch_size]
        batch_embeddings = embed_texts(batch)
        all_embeddings.append(batch_embeddings)
        print(f"  Embedded batch {i // batch_size + 1}/{(len(all_texts) - 1) // batch_size + 1}")

    import numpy as np
    all_embeddings = np.vstack(all_embeddings)

    vector_store.add(all_embeddings, all_metadata)
    bm25_index.build(all_texts, all_metadata)

    vector_store.save()
    bm25_index.save()

    print("\n" + "=" * 60)
    print(f"Knowledge base built successfully!")
    print(f"  FAISS vectors: {vector_store.total_vectors}")
    print(f"  BM25 documents: {bm25_index.total_documents}")
    print(f"  Index saved to: {config.FAISS_INDEX_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    build()
