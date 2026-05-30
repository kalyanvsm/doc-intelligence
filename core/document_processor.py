"""
core/document_processor.py
---------------------------
Extracts text from PDF, DOCX, and TXT files.
Returns page-aware output for accurate citations later.
"""

import io
from typing import Union
import streamlit as st


# ── PDF Extraction ────────────────────────────────────────────────────────────

def extract_pdf(file_bytes: bytes) -> list[tuple[int, str]]:
    """
    Extract text page-by-page from a PDF.
    Returns: [(page_number, page_text), ...]
    """
    try:
        import fitz  # pymupdf
        doc    = fitz.open(stream=file_bytes, filetype="pdf")
        pages  = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                pages.append((i, text))
        doc.close()
        return pages
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


# ── DOCX Extraction ───────────────────────────────────────────────────────────

def extract_docx(file_bytes: bytes) -> list[tuple[int, str]]:
    """
    Extract text from a DOCX file paragraph by paragraph.
    DOCX has no real pages, so we group every 30 paragraphs as a 'page'.
    Returns: [(page_number, text_block), ...]
    """
    try:
        from docx import Document
        doc        = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        pages      = []
        group_size = 30                          # ~1 page worth of paragraphs
        for i in range(0, len(paragraphs), group_size):
            group     = paragraphs[i: i + group_size]
            page_num  = (i // group_size) + 1
            pages.append((page_num, "\n".join(group)))
        return pages
    except Exception as e:
        raise RuntimeError(f"DOCX extraction failed: {e}")


# ── TXT Extraction ────────────────────────────────────────────────────────────

def extract_txt(file_bytes: bytes) -> list[tuple[int, str]]:
    """
    Extract text from a plain text file.
    Groups every 100 lines as a 'page'.
    Returns: [(page_number, text_block), ...]
    """
    try:
        text  = file_bytes.decode("utf-8", errors="replace")
        lines = [l for l in text.splitlines() if l.strip()]

        pages      = []
        group_size = 100
        for i in range(0, len(lines), group_size):
            group    = lines[i: i + group_size]
            page_num = (i // group_size) + 1
            pages.append((page_num, "\n".join(group)))
        return pages
    except Exception as e:
        raise RuntimeError(f"TXT extraction failed: {e}")


# ── Dispatcher ────────────────────────────────────────────────────────────────

def extract_text(file_bytes: bytes, filename: str) -> list[tuple[int, str]]:
    """
    Route to the correct extractor based on file extension.
    Returns: [(page_number, page_text), ...]
    Raises: ValueError for unsupported types, RuntimeError for extraction errors.
    """
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return extract_pdf(file_bytes)
    elif ext == "docx":
        return extract_docx(file_bytes)
    elif ext == "txt":
        return extract_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Use PDF, DOCX, or TXT.")


def get_file_type(filename: str) -> str:
    return filename.lower().rsplit(".", 1)[-1]
