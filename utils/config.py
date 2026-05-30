"""
utils/config.py
---------------
Single source of truth for all configuration values.
Reads from Streamlit secrets (cloud) with .env fallback (local dev).
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    """Try st.secrets first, then os.environ, then default."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


# ── Exported Config ───────────────────────────────────────────────────────────

GROQ_API_KEY         = _get("GROQ_API_KEY")
GROQ_MODEL           = _get("GROQ_MODEL", "llama-3.3-70b-versatile")

PINECONE_API_KEY     = _get("PINECONE_API_KEY")
PINECONE_INDEX_NAME  = _get("PINECONE_INDEX_NAME", "doc-intelligence")

EMBEDDING_MODEL      = _get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_DIMENSION  = int(_get("EMBEDDING_DIMENSION", "768"))

APP_SECRET_KEY       = _get("APP_SECRET_KEY", "change_me")
MAX_FILE_SIZE_MB     = int(_get("MAX_FILE_SIZE_MB", "20"))
CHUNK_SIZE           = int(_get("CHUNK_SIZE", "512"))
CHUNK_OVERLAP        = int(_get("CHUNK_OVERLAP", "50"))
TOP_K_RESULTS        = int(_get("TOP_K_RESULTS", "5"))


def validate_config():
    """Call on startup — raises clear errors if critical keys are missing."""
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not PINECONE_API_KEY:
        missing.append("PINECONE_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required config keys: {', '.join(missing)}. "
            "Add them to .streamlit/secrets.toml or .env"
        )
