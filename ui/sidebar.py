"""
ui/sidebar.py
-------------
Sidebar: branding, document upload, document list, user info, logout.
"""

import streamlit as st
from core.auth        import logout_user
from core.rag_pipeline import ingest_document, remove_document
from database.db       import get_user_documents


def render_sidebar():
    with st.sidebar:

        # ── Branding ──────────────────────────────────────────────────────────
        st.markdown('<div class="app-title">DocIntel</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Document Intelligence Platform</div>', unsafe_allow_html=True)

        # ── User info ─────────────────────────────────────────────────────────
        username = st.session_state.get("username", "")
        st.markdown(
            f'<div style="font-size:0.8rem; color:#6C63FF; margin-bottom:1rem;">'
            f'{username}</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # ── Upload section ────────────────────────────────────────────────────
        st.markdown("#### Upload Document")

        uploaded = st.file_uploader(
            label       = "Drop a file here",
            type        = ["pdf", "docx", "txt"],
            label_visibility = "collapsed",
            key         = "file_uploader",
        )

        if uploaded:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.caption(f"📄 {uploaded.name}")
            with col2:
                process_btn = st.button("Index", type="primary", use_container_width=True)

            if process_btn:
                with st.spinner("Processing..."):
                    success, msg = ingest_document(
                        file_bytes = uploaded.read(),
                        filename   = uploaded.name,
                        user_id    = st.session_state["user_id"],
                    )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")

        # ── Document List ─────────────────────────────────────────────────────
        st.markdown("#### My Documents")

        user_id = st.session_state["user_id"]
        docs    = get_user_documents(user_id)

        if not docs:
            st.markdown(
                '<div style="font-size:0.8rem; color:#64748b; padding:8px 0;">'
                'No documents yet. Upload one above.</div>',
                unsafe_allow_html=True
            )
        else:
            # Store selected docs in session state for scoped querying
            if "selected_doc_ids" not in st.session_state:
                st.session_state["selected_doc_ids"] = []

            for doc in docs:
                status_html = {
                    "ready":      '<span class="doc-status-ready">● ready</span>',
                    "processing": '<span class="doc-status-processing">● processing</span>',
                    "failed":     '<span class="doc-status-failed">● failed</span>',
                }.get(doc.status, "")

                st.markdown(f"""
                <div class="doc-card">
                    <div class="doc-name">📄 {doc.filename}</div>
                    <div class="doc-meta">{doc.file_size_kb} KB · {doc.total_chunks} chunks &nbsp; {status_html}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])
                with col1:
                    # Checkbox to scope chat to specific docs
                    checked = st.checkbox(
                        "Search this doc",
                        key    = f"chk_{doc.id}",
                        value  = doc.id in st.session_state["selected_doc_ids"],
                    )
                    if checked and doc.id not in st.session_state["selected_doc_ids"]:
                        st.session_state["selected_doc_ids"].append(doc.id)
                    elif not checked and doc.id in st.session_state["selected_doc_ids"]:
                        st.session_state["selected_doc_ids"].remove(doc.id)

                with col2:
                    if st.button("🗑️", key=f"del_{doc.id}", help="Delete document"):
                        with st.spinner("Deleting..."):
                            ok, msg = remove_document(doc.id, user_id)
                        if ok:
                            # Remove from selected list if present
                            if doc.id in st.session_state["selected_doc_ids"]:
                                st.session_state["selected_doc_ids"].remove(doc.id)
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("---")

            # ── Scope info ────────────────────────────────────────────────────
            selected = st.session_state.get("selected_doc_ids", [])
            if selected:
                st.caption(f"🔍 Chat scoped to {len(selected)} document(s)")
            else:
                st.caption("🔍 Chat searches all your documents")

        st.markdown("---")

        # ── New Chat button ───────────────────────────────────────────────────
        if st.button("✨ New Chat", use_container_width=True):
            import uuid
            st.session_state["session_id"] = str(uuid.uuid4())
            st.session_state["messages"]   = []
            st.rerun()

        # ── Logout ────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
