"""
ui/styles.py
------------
Custom CSS injected into Streamlit for a polished dark UI.
"""

import streamlit as st


def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background: #0a0b0f;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0f1117 !important;
        border-right: 1px solid #1e2130;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
    }

    /* ── App title in sidebar ── */
    .app-title {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF, #48cfad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 1.5rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── Doc card in sidebar ── */
    .doc-card {
        background: #161822;
        border: 1px solid #1e2130;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        transition: border-color 0.2s;
    }

    .doc-card:hover {
        border-color: #6C63FF44;
    }

    .doc-name {
        font-size: 0.82rem;
        font-weight: 600;
        color: #e2e8f0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .doc-meta {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 2px;
        font-family: 'JetBrains Mono', monospace;
    }

    .doc-status-ready {
        display: inline-block;
        font-size: 0.65rem;
        padding: 1px 7px;
        border-radius: 20px;
        background: #14532d44;
        color: #4ade80;
        border: 1px solid #4ade8033;
        font-weight: 600;
    }

    .doc-status-processing {
        display: inline-block;
        font-size: 0.65rem;
        padding: 1px 7px;
        border-radius: 20px;
        background: #92400e44;
        color: #fbbf24;
        border: 1px solid #fbbf2433;
        font-weight: 600;
    }

    .doc-status-failed {
        display: inline-block;
        font-size: 0.65rem;
        padding: 1px 7px;
        border-radius: 20px;
        background: #7f1d1d44;
        color: #f87171;
        border: 1px solid #f8717133;
        font-weight: 600;
    }

    /* ── Chat messages ── */
    .chat-bubble-user {
        background: #1a1d2e;
        border: 1px solid #2d3154;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #e2e8f0;
        font-size: 0.9rem;
        max-width: 80%;
        margin-left: auto;
    }

    .chat-bubble-assistant {
        background: #111318;
        border: 1px solid #1e2130;
        border-radius: 2px 12px 12px 12px;
        padding: 14px 16px;
        margin: 8px 0;
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.65;
        max-width: 88%;
    }

    /* ── Source citations ── */
    .source-card {
        background: #0f1117;
        border: 1px solid #1e2130;
        border-left: 3px solid #6C63FF;
        border-radius: 0 6px 6px 0;
        padding: 8px 12px;
        margin-top: 4px;
        font-size: 0.75rem;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }

    .source-label {
        color: #6C63FF;
        font-weight: 600;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Chat input ── */
    .stChatInput {
        padding-left: 0px !important;
    }

    .stChatInput textarea {
        background: #111318 !important;
        /*border: 1px solid #1e2130 !important;*/
        border-radius: 30px !important;
        color: #e2e8f0 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        padding-left: -16px !important;
    }

    .stChatInput textarea:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px #6C63FF22 !important;
        border-radius: 10px !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: #161822;
        border: 1px solid #1e2130;
        color: #94a3b8;
        border-radius: 6px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.82rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        border-color: #6C63FF;
        color: #e2e8f0;
        background: #1a1d2e;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C63FF, #48cfad);
        border: none;
        color: white;
        font-weight: 600;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: #111318;
        border: 1px dashed #2d3154;
        border-radius: 8px;
        padding: 8px;
    }

    /* ── Divider ── */
    hr {
        border: none;
        border-top: 1px solid #1e2130;
        margin: 16px 0;
    }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: #111318;
        border: 1px solid #1e2130;
        border-radius: 8px;
        padding: 12px 16px;
    }

    /* ── Welcome screen ── */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
        text-align: center;
    }

    .welcome-icon {
        font-size: 3.5rem;
        margin-bottom: 16px;
    }

    .welcome-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 8px;
    }

    .welcome-sub {
        font-size: 0.95rem;
        color: #64748b;
        max-width: 420px;
        line-height: 1.6;
    }

    .welcome-steps {
        margin-top: 32px;
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        justify-content: center;
    }

    .step-chip {
        background: #111318;
        border: 1px solid #1e2130;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.8rem;
        color: #94a3b8;
    }

    .step-chip span {
        color: #6C63FF;
        font-weight: 700;
        margin-right: 6px;
    }

    /* ── Auth forms ── */
    .auth-container {
        max-width: 400px;
        margin: 60px auto;
        background: #0f1117;
        border: 1px solid #1e2130;
        border-radius: 12px;
        padding: 32px;
    }

    .auth-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 4px;
    }

    .auth-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 24px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0a0b0f; }
    ::-webkit-scrollbar-thumb { background: #1e2130; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #6C63FF44; }

    </style>
    """, unsafe_allow_html=True)
