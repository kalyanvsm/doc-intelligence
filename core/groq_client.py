"""
core/groq_client.py
--------------------
Handles all communication with the Groq API.
Builds the RAG prompt and returns the LLM answer.
"""

from groq import Groq
from utils.config import GROQ_API_KEY, GROQ_MODEL


# ── Client (module-level singleton) ──────────────────────────────────────────

_client = None

def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# ── Prompt Builder ────────────────────────────────────────────────────────────

def build_rag_prompt(question: str, context_chunks: list[dict]) -> str:
    """
    Build the context string from retrieved Pinecone chunks.
    Each chunk is labelled with its source for the model to cite.
    """
    context_parts = []
    for i, chunk in enumerate(context_chunks, start=1):
        source = f"[Source {i}: {chunk['filename']}, Page {chunk['page_number']}]"
        context_parts.append(f"{source}\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    return f"""You are a precise document assistant. Answer the user's question using ONLY the context provided below.

Rules:
- Base your answer strictly on the provided context.
- If the context does not contain enough information, say: "I could not find relevant information in your documents."
- Always mention which source (filename and page) supports your answer.
- Be concise and factual. Do not hallucinate or add outside knowledge.

Context:
{context}

Question: {question}

Answer:"""


# ── LLM Call ─────────────────────────────────────────────────────────────────

def generate_answer(
    question:       str,
    context_chunks: list[dict],
    chat_history:   list[dict] | None = None,
    max_tokens:     int = 1024,
) -> str:
    """
    Call Groq API with the RAG prompt and return the answer string.

    Args:
        question:       User's natural language question.
        context_chunks: List of retrieved chunks from Pinecone.
        chat_history:   Optional previous messages for multi-turn context.
        max_tokens:     Max tokens in the response.

    Returns:
        Answer string from the LLM.
    """
    client  = get_groq_client()
    prompt  = build_rag_prompt(question, context_chunks)

    messages = [
        {
            "role":    "system",
            "content": (
                "You are a helpful, precise document intelligence assistant. "
                "You answer questions based only on documents provided to you. "
                "You always cite your sources clearly."
            ),
        }
    ]

    # Inject last 4 exchanges for conversational context (keeps tokens low)
    if chat_history:
        for msg in chat_history[-8:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model      = GROQ_MODEL,
        messages   = messages,
        max_tokens = max_tokens,
        temperature= 0.2,      # low temp = factual, consistent answers
    )

    return response.choices[0].message.content.strip()
