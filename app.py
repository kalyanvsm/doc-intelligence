"""
app.py  —  Main entry point
Wires together: config validation, DB init, auth gate, sidebar, chat.
"""

import streamlit as st

st.set_page_config(
    page_title = "DocIntel",
    page_icon  = "📚",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Must be first Streamlit calls after set_page_config ──────────────────────
from ui.styles   import inject_styles
inject_styles()

from database.db   import init_db
from utils.config  import validate_config
from core.auth     import is_authenticated
from ui.auth_ui    import render_auth
from ui.sidebar    import render_sidebar
from ui.chat       import render_chat

# ── Startup ───────────────────────────────────────────────────────────────────
@st.cache_resource
def startup():
    validate_config()
    init_db()
    return True

try:
    startup()
except EnvironmentError as e:
    st.error(f"⚠️ Configuration error: {e}")
    st.code("Fill in GROQ_API_KEY and PINECONE_API_KEY in .streamlit/secrets.toml")
    st.stop()

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_authenticated():
    render_auth()
    st.stop()

# ── Authenticated layout ──────────────────────────────────────────────────────
render_sidebar()
render_chat()
