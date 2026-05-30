"""
core/embeddings.py
------------------
Loads the BGE embedding model locally (no API cost).
Caches the model in Streamlit so it only loads once per session.
"""

import streamlit as st
from utils.config import EMBEDDING_MODEL


# ── Model Loader (cached) ─────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading embedding model... (first time only)")
def load_embedding_model():
    """
    Downloads and caches the sentence-transformer model.
    Uses Streamlit's cache_resource so it stays in memory across reruns.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model


# ── Embedding Generation ──────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of chunk strings.

    Returns:
        List of float vectors (one per text).
    """
    model      = load_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,   # cosine similarity works better normalized
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Embed a single user query string.
    BGE models work best with a prefix for queries.
    """
    prefixed = f"Represent this sentence for searching relevant passages: {query}"
    model    = load_embedding_model()
    vector   = model.encode(
        prefixed,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector.tolist()
