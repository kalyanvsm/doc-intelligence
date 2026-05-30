"""
core/pinecone_client.py
-----------------------
All Pinecone operations: index initialisation, upsert, query, delete.
Vectors are namespaced per user_id for strict data isolation.
"""

import streamlit as st
from utils.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBEDDING_DIMENSION


# ── Client + Index (cached) ───────────────────────────────────────────────────

@st.cache_resource(show_spinner="Connecting to Pinecone...")
def get_pinecone_index():
    """
    Initialise Pinecone client and return the index object.
    Creates the index if it doesn't exist yet (serverless, free tier).
    Cached so the connection is reused across Streamlit reruns.
    """
    from pinecone import Pinecone, ServerlessSpec

    pc    = Pinecone(api_key=PINECONE_API_KEY)
    names = [idx.name for idx in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in names:
        pc.create_index(
            name      = PINECONE_INDEX_NAME,
            dimension = EMBEDDING_DIMENSION,
            metric    = "cosine",
            spec      = ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    return pc.Index(PINECONE_INDEX_NAME)


# ── Upsert ────────────────────────────────────────────────────────────────────

def upsert_chunks(
    chunks:      list[dict],
    embeddings:  list[list[float]],
    user_id:     str,
    doc_id:      str,
    filename:    str,
) -> list[str]:
    """
    Store chunk embeddings in Pinecone with metadata.

    Args:
        chunks:     List of dicts with keys: chunk_index, page_number, text
        embeddings: Parallel list of float vectors
        user_id:    Owner's user ID (used as Pinecone namespace)
        doc_id:     Document UUID from SQLite
        filename:   Original filename (for citations)

    Returns:
        List of pinecone_ids in the same order as chunks.
    """
    index      = get_pinecone_index()
    vectors    = []
    pine_ids   = []

    for chunk, embedding in zip(chunks, embeddings):
        pine_id = f"{doc_id}_{chunk['chunk_index']}"
        pine_ids.append(pine_id)

        vectors.append({
            "id":     pine_id,
            "values": embedding,
            "metadata": {
                "user_id":     user_id,
                "doc_id":      doc_id,
                "filename":    filename,
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk.get("page_number", 1),
                "text":        chunk["text"][:1000],   # Pinecone metadata limit
            },
        })

    # Upsert in batches of 100 (Pinecone limit)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i: i + batch_size]
        index.upsert(vectors=batch, namespace=user_id)

    return pine_ids


# ── Query ─────────────────────────────────────────────────────────────────────

def query_similar(
    query_vector: list[float],
    user_id:      str,
    top_k:        int = 5,
    doc_ids:      list[str] | None = None,
) -> list[dict]:
    """
    Retrieve top-k similar chunks from Pinecone for a given query vector.

    Args:
        query_vector: Embedded query float vector.
        user_id:      Namespace to search in (user's own data only).
        top_k:        Number of results to return.
        doc_ids:      Optional list of doc_ids to restrict search to.

    Returns:
        List of dicts: {score, doc_id, filename, page_number, chunk_index, text}
    """
    index  = get_pinecone_index()
    filter = {"user_id": {"$eq": user_id}}

    if doc_ids:
        filter["doc_id"] = {"$in": doc_ids}

    response = index.query(
        vector          = query_vector,
        top_k           = top_k,
        namespace       = user_id,
        include_metadata= True,
        filter          = filter,
    )

    results = []
    for match in response.matches:
        meta = match.metadata
        results.append({
            "score":       round(match.score, 4),
            "doc_id":      meta.get("doc_id", ""),
            "filename":    meta.get("filename", ""),
            "page_number": meta.get("page_number", 1),
            "chunk_index": meta.get("chunk_index", 0),
            "text":        meta.get("text", ""),
        })

    return results


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_document_vectors(pinecone_ids: list[str], user_id: str):
    """
    Delete all Pinecone vectors for a given document.

    Args:
        pinecone_ids: List of vector IDs (from SQLite chunks table).
        user_id:      Namespace where vectors are stored.
    """
    if not pinecone_ids:
        return
    index = get_pinecone_index()
    # Delete in batches of 100
    for i in range(0, len(pinecone_ids), 100):
        batch = pinecone_ids[i: i + 100]
        index.delete(ids=batch, namespace=user_id)
