"""
core/rag_pipeline.py
--------------------
Orchestrates the two main flows:

1. ingest_document()  — Upload → Extract → Chunk → Embed → Pinecone + SQLite
2. answer_question()  — Query → Embed → Retrieve → Generate → Cite
"""

import streamlit as st
from utils.helpers import chunk_pages, bytes_to_kb, allowed_file
from utils.config  import TOP_K_RESULTS, MAX_FILE_SIZE_MB

from core.document_processor import extract_text, get_file_type
from core.embeddings          import embed_texts, embed_query
from core.pinecone_client     import upsert_chunks, query_similar, delete_document_vectors
from core.groq_client         import generate_answer

from database.db import (
    create_document, update_document_status,
    save_chunks, get_pinecone_ids_for_document, delete_document,
    get_user_documents,
)


# ── Ingestion Pipeline ────────────────────────────────────────────────────────

def ingest_document(
    file_bytes: bytes,
    filename:   str,
    user_id:    str,
) -> tuple[bool, str]:
    """
    Full ingestion pipeline for one uploaded file.

    Returns:
        (success: bool, message: str)
    """

    # ── Validation ────────────────────────────────────────────────────────────
    if not allowed_file(filename):
        return False, f"'{filename}' is not supported. Upload PDF, DOCX, or TXT."

    size_kb = bytes_to_kb(len(file_bytes))
    if size_kb > MAX_FILE_SIZE_MB * 1024:
        return False, f"File exceeds {MAX_FILE_SIZE_MB} MB limit."

    # ── Create DB record (status=processing) ──────────────────────────────────
    file_type = get_file_type(filename)
    doc       = create_document(
        user_id      = user_id,
        filename     = filename,
        file_type    = file_type,
        file_size_kb = size_kb,
    )
    doc_id = doc.id

    try:
        # ── Step 1: Extract text ──────────────────────────────────────────────
        pages = extract_text(file_bytes, filename)
        if not pages:
            update_document_status(doc_id, "failed")
            return False, "Could not extract any text from the document."

        # ── Step 2: Chunk ─────────────────────────────────────────────────────
        chunks = chunk_pages(pages)
        if not chunks:
            update_document_status(doc_id, "failed")
            return False, "Document produced no usable text chunks."

        # ── Step 3: Embed ─────────────────────────────────────────────────────
        texts      = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        # ── Step 4: Upsert to Pinecone ────────────────────────────────────────
        pinecone_ids = upsert_chunks(
            chunks     = chunks,
            embeddings = embeddings,
            user_id    = user_id,
            doc_id     = doc_id,
            filename   = filename,
        )

        # ── Step 5: Save chunks to SQLite ─────────────────────────────────────
        chunks_data = []
        for chunk, pine_id in zip(chunks, pinecone_ids):
            chunks_data.append({
                "document_id":  doc_id,
                "user_id":      user_id,
                "chunk_index":  chunk["chunk_index"],
                "page_number":  chunk.get("page_number", 1),
                "text_preview": chunk["text"],
                "pinecone_id":  pine_id,
            })
        save_chunks(chunks_data)

        # ── Step 6: Mark document ready ───────────────────────────────────────
        update_document_status(doc_id, "ready", total_chunks=len(chunks))

        return True, f"'{filename}' processed successfully — {len(chunks)} chunks indexed."

    except Exception as e:
        update_document_status(doc_id, "failed")
        return False, f"Processing failed: {str(e)}"


# ── Query Pipeline ────────────────────────────────────────────────────────────

def answer_question(
    question:     str,
    user_id:      str,
    chat_history: list[dict] | None = None,
    doc_ids:      list[str]  | None = None,
) -> dict:
    """
    Full RAG query pipeline.

    Args:
        question:     User's natural language question.
        user_id:      Restricts Pinecone search to user's namespace.
        chat_history: Previous messages for multi-turn context.
        doc_ids:      Optional filter to specific documents.

    Returns:
        {
            "answer":  str,
            "sources": [{"filename", "page_number", "score", "text_preview"}, ...]
        }
    """
    # ── Step 1: Embed query ───────────────────────────────────────────────────
    query_vector = embed_query(question)

    # ── Step 2: Retrieve from Pinecone ────────────────────────────────────────
    chunks = query_similar(
        query_vector = query_vector,
        user_id      = user_id,
        top_k        = TOP_K_RESULTS,
        doc_ids      = doc_ids,
    )

    if not chunks:
        return {
            "answer":  "I couldn't find any relevant information in your documents. Try uploading some files first.",
            "sources": [],
        }

    # ── Step 3: Generate answer via Groq ─────────────────────────────────────
    answer = generate_answer(
        question       = question,
        context_chunks = chunks,
        chat_history   = chat_history,
    )

    # ── Step 4: Build citation list ───────────────────────────────────────────
    sources = []
    seen    = set()
    for chunk in chunks:
        key = (chunk["filename"], chunk["page_number"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "filename":     chunk["filename"],
                "page_number":  chunk["page_number"],
                "score":        chunk["score"],
                "text_preview": chunk["text"][:200],
            })

    return {"answer": answer, "sources": sources}


# ── Document Deletion ─────────────────────────────────────────────────────────

def remove_document(doc_id: str, user_id: str) -> tuple[bool, str]:
    """
    Delete a document from both Pinecone and SQLite.
    """
    try:
        pinecone_ids = get_pinecone_ids_for_document(doc_id)
        delete_document_vectors(pinecone_ids, user_id)
        delete_document(doc_id, user_id)
        return True, "Document deleted successfully."
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"
