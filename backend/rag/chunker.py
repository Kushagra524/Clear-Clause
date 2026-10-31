import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# legal section heading patterns for structure-aware splitting
SECTION_PATTERNS = [
    r'^(?:ARTICLE|SECTION|CLAUSE|PART)\s+[IVXLCDM\d]+',
    r'^\d+\.\d*\s+[A-Z]',
    r'^[A-Z][A-Z\s]{4,}$',
    r'^(?:WHEREAS|NOW\s*,?\s*THEREFORE|IN\s+WITNESS)',
    r'^(?:DEFINITIONS?|TERM(?:INATION)?|PAYMENT|INDEMNIF|CONFIDEN|GOVERNING\s+LAW)',
]


def is_section_heading(line):
    # checks if a line looks like a legal section header
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    for pattern in SECTION_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            return True
    return False


def split_into_sentences(text):
    # sentence boundary detection tuned for legal text
    abbreviations = {'mr', 'mrs', 'ms', 'dr', 'prof', 'inc', 'ltd', 'corp', 'co',
                     'no', 'nos', 'vol', 'dept', 'est', 'approx', 'govt', 'vs',
                     'art', 'sec', 'cl', 'para', 'sub', 'ref'}
    sentences = []
    current = []
    tokens = re.split(r'([.!?]+[\s])', text)

    for token in tokens:
        current.append(token)
        joined = ''.join(current).strip()

        if re.search(r'[.!?]\s*$', token):
            words = joined.split()
            if words:
                last_word = re.sub(r'[.!?]+$', '', words[-1] if len(words) == 1 else words[-2]).lower()
                if last_word in abbreviations:
                    continue
            if len(joined) > 15:
                sentences.append(joined)
                current = []

    remainder = ''.join(current).strip()
    if remainder:
        sentences.append(remainder)

    return sentences


def semantic_chunk(sentences, embedder, threshold=0.45, max_chunk_size=512):
    # groups consecutive sentences by embedding similarity
    if not sentences:
        return []

    embeddings = embedder.encode(sentences, show_progress_bar=False)
    chunks = []
    current_chunk = [sentences[0]]
    current_length = len(sentences[0].split())

    for i in range(1, len(sentences)):
        sim = cosine_similarity(
            embeddings[i-1].reshape(1, -1),
            embeddings[i].reshape(1, -1)
        )[0][0]

        sentence_words = len(sentences[i].split())

        if sim >= threshold and (current_length + sentence_words) <= max_chunk_size:
            current_chunk.append(sentences[i])
            current_length += sentence_words
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
            current_length = sentence_words

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def legal_aware_chunk(text, embedder, chunk_size=512, chunk_overlap=64):
    # splits by legal headings first, then applies semantic chunking within each section
    lines = text.split('\n')
    sections = []
    current_section = []
    current_heading = "Preamble"

    for line in lines:
        if is_section_heading(line):
            if current_section:
                sections.append({
                    "heading": current_heading,
                    "text": '\n'.join(current_section)
                })
            current_heading = line.strip()
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append({
            "heading": current_heading,
            "text": '\n'.join(current_section)
        })

    # check if document had meaningful section structure
    has_structure = len(sections) > 2

    all_chunks = []

    if has_structure:
        # legal-aware path: chunk within each section
        for section in sections:
            section_text = section["text"].strip()
            if not section_text:
                continue

            sentences = split_into_sentences(section_text)
            if not sentences:
                continue

            section_chunks = semantic_chunk(sentences, embedder, max_chunk_size=chunk_size)
            for chunk in section_chunks:
                all_chunks.append({
                    "text": chunk,
                    "section": section["heading"],
                    "method": "legal_semantic"
                })
    else:
        # fallback: pure semantic chunking for unstructured documents
        sentences = split_into_sentences(text)
        if sentences:
            pure_chunks = semantic_chunk(sentences, embedder, max_chunk_size=chunk_size)
            for chunk in pure_chunks:
                all_chunks.append({
                    "text": chunk,
                    "section": "Document",
                    "method": "semantic"
                })

    # add overlap context between adjacent chunks
    if chunk_overlap > 0 and len(all_chunks) > 1:
        for i in range(1, len(all_chunks)):
            prev_words = all_chunks[i-1]["text"].split()
            overlap_words = prev_words[-chunk_overlap:] if len(prev_words) > chunk_overlap else prev_words
            all_chunks[i]["context_prefix"] = ' '.join(overlap_words)

    return all_chunks
