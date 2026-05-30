"""
database/db.py
--------------
SQLite schema and all query helpers used across the app.
Tables: users, documents, chunks, chat_history
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Text,
    DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ── Engine ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username     = Column(String(50), unique=True, nullable=False)
    email        = Column(String(120), unique=True, nullable=False)
    password     = Column(String(256), nullable=False)     # bcrypt hash
    created_at   = Column(DateTime, default=datetime.utcnow)
    is_active    = Column(Boolean, default=True)

    documents    = relationship("Document", back_populates="owner", cascade="all, delete")
    chats        = relationship("ChatHistory", back_populates="user", cascade="all, delete")


class Document(Base):
    __tablename__ = "documents"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False)
    filename     = Column(String(255), nullable=False)
    file_type    = Column(String(10), nullable=False)      # pdf | docx | txt
    file_size_kb = Column(Integer, nullable=False)
    total_chunks = Column(Integer, default=0)
    status       = Column(String(20), default="processing")  # processing | ready | failed
    uploaded_at  = Column(DateTime, default=datetime.utcnow)

    owner        = relationship("User", back_populates="documents")
    chunks       = relationship("Chunk", back_populates="document", cascade="all, delete")


class Chunk(Base):
    __tablename__ = "chunks"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id  = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id      = Column(String, nullable=False)
    chunk_index  = Column(Integer, nullable=False)
    page_number  = Column(Integer, nullable=True)
    text_preview = Column(String(200), nullable=False)     # first 200 chars for display
    pinecone_id  = Column(String, nullable=False)          # vector ID stored in Pinecone

    document     = relationship("Document", back_populates="chunks")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False)
    session_id   = Column(String, nullable=False)          # groups messages into a conversation
    role         = Column(String(10), nullable=False)      # user | assistant
    content      = Column(Text, nullable=False)
    sources      = Column(Text, nullable=True)             # JSON list of citations
    created_at   = Column(DateTime, default=datetime.utcnow)

    user         = relationship("User", back_populates="chats")


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(engine)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_session():
    return SessionLocal()


# --- User helpers ---

def create_user(username: str, email: str, hashed_password: str) -> User:
    db = get_session()
    try:
        user = User(username=username, email=email, password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user_by_username(username: str) -> User | None:
    db = get_session()
    try:
        return db.query(User).filter(User.username == username).first()
    finally:
        db.close()


def get_user_by_email(email: str) -> User | None:
    db = get_session()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


# --- Document helpers ---

def create_document(user_id: str, filename: str, file_type: str, file_size_kb: int) -> Document:
    db = get_session()
    try:
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size_kb=file_size_kb,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    finally:
        db.close()


def update_document_status(doc_id: str, status: str, total_chunks: int = 0):
    db = get_session()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = status
            doc.total_chunks = total_chunks
            db.commit()
    finally:
        db.close()


def get_user_documents(user_id: str) -> list[Document]:
    db = get_session()
    try:
        return (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.uploaded_at.desc())
            .all()
        )
    finally:
        db.close()


def delete_document(doc_id: str, user_id: str) -> bool:
    """Delete document + its chunks from SQLite (caller handles Pinecone cleanup)."""
    db = get_session()
    try:
        doc = db.query(Document).filter(
            Document.id == doc_id,
            Document.user_id == user_id
        ).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_document_by_id(doc_id: str, user_id: str) -> Document | None:
    db = get_session()
    try:
        return db.query(Document).filter(
            Document.id == doc_id,
            Document.user_id == user_id
        ).first()
    finally:
        db.close()


# --- Chunk helpers ---

def save_chunks(chunks_data: list[dict]):
    """
    chunks_data: list of dicts with keys:
        document_id, user_id, chunk_index, page_number, text_preview, pinecone_id
    """
    db = get_session()
    try:
        for c in chunks_data:
            chunk = Chunk(
                document_id  = c["document_id"],
                user_id      = c["user_id"],
                chunk_index  = c["chunk_index"],
                page_number  = c.get("page_number"),
                text_preview = c["text_preview"][:200],
                pinecone_id  = c["pinecone_id"],
            )
            db.add(chunk)
        db.commit()
    finally:
        db.close()


def get_pinecone_ids_for_document(doc_id: str) -> list[str]:
    db = get_session()
    try:
        chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
        return [c.pinecone_id for c in chunks]
    finally:
        db.close()


# --- Chat helpers ---

def save_message(user_id: str, session_id: str, role: str, content: str, sources: str = None):
    db = get_session()
    try:
        msg = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
        )
        db.add(msg)
        db.commit()
    finally:
        db.close()


def get_chat_history(user_id: str, session_id: str, limit: int = 20) -> list[ChatHistory]:
    db = get_session()
    try:
        return (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_user_sessions(user_id: str) -> list[str]:
    """Return distinct session IDs for a user, most recent first."""
    db = get_session()
    try:
        rows = (
            db.query(ChatHistory.session_id, ChatHistory.created_at)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .all()
        )
        seen = []
        for row in rows:
            if row.session_id not in seen:
                seen.append(row.session_id)
        return seen
    finally:
        db.close()
