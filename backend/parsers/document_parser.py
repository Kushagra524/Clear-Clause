import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import os
import re


def extract_text_from_pdf(file_path):
    # try pdfplumber first for better table/layout handling
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        if text_parts:
            return "\n\n".join(text_parts)
    except Exception:
        pass

    # fallback to pypdf2 for simpler pdfs
    try:
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as err:
        raise ValueError(f"Could not read PDF: {err}")


def extract_text_from_docx(file_path):
    # reads paragraphs and table cells from docx
    try:
        doc = DocxDocument(file_path)
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    parts.append(row_text)
        return "\n\n".join(parts)
    except Exception as err:
        raise ValueError(f"Could not read DOCX: {err}")


def extract_text_from_txt(file_path):
    # plain text with encoding fallback
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("Could not decode the text file")


def extract_text(file_path):
    # routes to the correct extractor based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_text_from_content(content, filename):
    # for content passed as string (from api request body)
    if not content or len(content.strip()) < 10:
        raise ValueError("Document content is too short to analyze")
    return content.strip()


def clean_extracted_text(text):
    # normalize whitespace and remove artifacts from extraction
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned.append(stripped)
        elif cleaned and cleaned[-1] != '':
            cleaned.append('')
    return '\n'.join(cleaned)
