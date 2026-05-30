"""
utils/helpers.py
----------------
Text cleaning and chunking utilities used during document ingestion.
"""

import re
import os
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))


# ── Text Cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove excessive whitespace, null bytes, and non-printable chars."""
    text = text.replace("\x00", "")                  # null bytes
    text = re.sub(r"\s+", " ", text)                 # collapse whitespace
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)     # non-printable chars
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE,
                      overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Word-boundary-aware sliding window chunker.

    Args:
        text:       Cleaned document text.
        chunk_size: Max words per chunk.
        overlap:    Words shared between consecutive chunks.

    Returns:
        List of chunk strings.
    """
    words  = text.split()
    chunks = []
    start  = 0

    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap   # slide forward with overlap

    return chunks


def chunk_pages(pages: list[tuple[int, str]],
                chunk_size: int = CHUNK_SIZE,
                overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Chunk page-aware text. Returns list of dicts with page_number, text.

    Args:
        pages: list of (page_number, page_text) tuples.
    """
    result = []
    global_index = 0

    for page_num, page_text in pages:
        page_text = clean_text(page_text)
        if not page_text:
            continue
        chunks = split_into_chunks(page_text, chunk_size, overlap)
        for chunk in chunks:
            result.append({
                "chunk_index": global_index,
                "page_number": page_num,
                "text":        chunk,
            })
            global_index += 1

    return result


# ── Misc ──────────────────────────────────────────────────────────────────────

def truncate(text: str, max_chars: int = 200) -> str:
    return text[:max_chars] + "..." if len(text) > max_chars else text


def bytes_to_kb(b: int) -> int:
    return max(1, b // 1024)


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith((".pdf", ".docx", ".txt"))
