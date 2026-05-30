"""
ui/auth_ui.py
-------------
Login and registration forms rendered when user is not authenticated.
"""

import streamlit as st
from core.auth import login_user, register_user


def render_auth():
    """
    Show login/register tabs. Returns True when user is authenticated.
    """
    # Centered container via columns
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 28px;">
            <div style="font-size:2.5rem;">📚</div>
            <div style="font-size:1.6rem; font-weight:700; color:#e2e8f0;">DocIntel</div>
            <div style="font-size:0.82rem; color:#64748b; text-transform:uppercase;
                        letter-spacing:0.08em; margin-top:4px;">
                Document Intelligence Platform
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        # ── Login ─────────────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", placeholder="your_username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In", type="primary", use_container_width=True, key="login_btn"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in..."):
                        ok, msg = login_user(username, password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # ── Register ──────────────────────────────────────────────────────────
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            new_username = st.text_input("Username", key="reg_username", placeholder="choose_username")
            new_email    = st.text_input("Email",    key="reg_email",    placeholder="you@example.com")
            new_pass     = st.text_input("Password", type="password", key="reg_password", placeholder="min 6 characters")
            new_pass2    = st.text_input("Confirm Password", type="password", key="reg_password2", placeholder="repeat password")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account", type="primary", use_container_width=True, key="reg_btn"):
                if not all([new_username, new_email, new_pass, new_pass2]):
                    st.error("Please fill in all fields.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account..."):
                        ok, msg = register_user(new_username, new_email, new_pass)
                    if ok:
                        st.success(msg + " Switch to Sign In to continue.")
                    else:
                        st.error(msg)
