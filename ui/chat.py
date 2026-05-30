"""
ui/chat.py
----------
Main chat interface: renders messages, handles input,
calls the RAG pipeline, displays citations.
"""

import json
import uuid
import streamlit as st
from core.rag_pipeline import answer_question
from database.db       import save_message, get_chat_history


# ── Session Init ──────────────────────────────────────────────────────────────

def init_chat_session():
    """Initialise session state keys for the chat on first load."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    if "messages" not in st.session_state:
        # Load last 20 messages from DB for the current session
        history = get_chat_history(
            user_id    = st.session_state["user_id"],
            session_id = st.session_state["session_id"],
        )
        st.session_state["messages"] = [
            {
                "role":    m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources else [],
            }
            for m in history
        ]


# ── Message Rendering ─────────────────────────────────────────────────────────

def render_message(msg: dict):
    """Render a single chat message with appropriate styling."""
    role    = msg["role"]
    content = msg["content"]
    sources = msg.get("sources", [])

    if role == "user":
        st.markdown(
            f'<div class="chat-bubble-user">{content}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="chat-bubble-assistant">{content}</div>',
            unsafe_allow_html=True,
        )
        if sources:
            render_sources(sources)


def render_sources(sources: list[dict]):
    """Render collapsible source citations below an assistant message."""
    with st.expander(f"📎 {len(sources)} source(s) used", expanded=False):
        for i, src in enumerate(sources, start=1):
            score_pct = int(src.get("score", 0) * 100)
            preview   = src.get("text_preview", "")[:180]
            st.markdown(f"""
            <div class="source-card">
                <div class="source-label">Source {i}</div>
                <div style="color:#e2e8f0; font-size:0.78rem; margin:3px 0;">
                    📄 {src['filename']} &nbsp;·&nbsp; Page {src['page_number']}
                    &nbsp;·&nbsp; <span style="color:#48cfad;">{score_pct}% match</span>
                </div>
                <div style="color:#64748b; font-size:0.72rem; margin-top:4px; font-style:italic;">
                    "{preview}..."
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── Welcome Screen ────────────────────────────────────────────────────────────

def render_welcome():
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-icon">🧠</div>
        <div class="welcome-title">Ask anything about your documents</div>
        <div class="welcome-sub">
            Upload PDFs, Word docs, or text files in the sidebar,
            then start chatting. All answers come directly from your documents.
        </div>
        <div class="welcome-steps">
            <div class="step-chip"><span>1</span> Upload a document</div>
            <div class="step-chip"><span>2</span> Ask a question</div>
            <div class="step-chip"><span>3</span> Get cited answers</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main Chat Renderer ────────────────────────────────────────────────────────

def render_chat():
    init_chat_session()

    messages = st.session_state["messages"]

    # ── Welcome or message history ────────────────────────────────────────────
    if not messages:
        render_welcome()
    else:
        for msg in messages:
            render_message(msg)

    # ── Chat input ────────────────────────────────────────────────────────────
    question = st.chat_input("Ask a question about your documents...")

    if question:
        user_id    = st.session_state["user_id"]
        session_id = st.session_state["session_id"]
        doc_ids    = st.session_state.get("selected_doc_ids") or None

        # Add user message
        user_msg = {"role": "user", "content": question, "sources": []}
        st.session_state["messages"].append(user_msg)
        render_message(user_msg)

        # Save user message to DB
        save_message(
            user_id    = user_id,
            session_id = session_id,
            role       = "user",
            content    = question,
        )

        # Build chat history for multi-turn context (exclude current question)
        history_for_llm = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["messages"][:-1]
        ]

        # Generate answer
        with st.spinner("Thinking..."):
            result = answer_question(
                question     = question,
                user_id      = user_id,
                chat_history = history_for_llm,
                doc_ids      = doc_ids,
            )

        answer  = result["answer"]
        sources = result["sources"]

        # Add assistant message
        asst_msg = {"role": "assistant", "content": answer, "sources": sources}
        st.session_state["messages"].append(asst_msg)
        render_message(asst_msg)

        # Save assistant message to DB
        save_message(
            user_id    = user_id,
            session_id = session_id,
            role       = "assistant",
            content    = answer,
            sources    = json.dumps(sources),
        )
