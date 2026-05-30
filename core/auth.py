"""
core/auth.py
------------
Handles user registration, login verification, and Streamlit session state.
Uses bcrypt for password hashing — no plain-text passwords stored.
"""

import bcrypt
import streamlit as st
from database.db import create_user, get_user_by_username, get_user_by_email


# ── Password Helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Returns (success: bool, message: str)
    """
    username = username.strip().lower()
    email    = email.strip().lower()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email:
        return False, "Enter a valid email address."

    if get_user_by_username(username):
        return False, "Username already taken."
    if get_user_by_email(email):
        return False, "An account with this email already exists."

    hashed = hash_password(password)
    create_user(username=username, email=email, hashed_password=hashed)
    return True, "Account created! You can now log in."


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(username: str, password: str) -> tuple[bool, str]:
    """
    Returns (success: bool, message: str).
    On success, sets Streamlit session state keys.
    """
    username = username.strip().lower()
    user = get_user_by_username(username)

    if not user:
        return False, "No account found with that username."
    if not user.is_active:
        return False, "This account has been deactivated."
    if not verify_password(password, user.password):
        return False, "Incorrect password."

    # ── Persist to session state ──────────────────────────────────────────────
    st.session_state["authenticated"] = True
    st.session_state["user_id"]       = user.id
    st.session_state["username"]      = user.username
    st.session_state["email"]         = user.email

    return True, f"Welcome back, {user.username}!"


# ── Logout ────────────────────────────────────────────────────────────────────

def logout_user():
    for key in ["authenticated", "user_id", "username", "email",
                "session_id", "messages"]:
        st.session_state.pop(key, None)


# ── Session Guard ─────────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def require_auth():
    """Call at the top of any page that needs login. Stops execution if not authed."""
    if not is_authenticated():
        st.warning("Please log in to continue.")
        st.stop()
