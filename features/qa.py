"""
Q&A feature — first end-to-end feature using the shared retriever.
Every other feature (notes, quiz, flashcards) follows this same pattern:
    retrieve → build prompt → generate → return structured result.
"""
from retrieval.retriever import retrieve
from prompts.qa_prompt import build_qa_prompt
from providers.factory import get_llm

FALLBACK = (
    "This topic is not covered in the provided material. "
    "Please refer to your textbook directly."
)


def answer_question(
    query: str,
    subject: str = None,
    semester: int = None,
) -> dict:
    """
    Full Q&A pipeline: retrieve → prompt → generate → return.

    Returns:
        {
            "answer":   str,          — the generated answer or fallback message
            "sources":  list[dict],   — source_file, page_number, score per chunk
            "grounded": bool,         — False if no relevant chunks were found
            "query":    str,          — original question, useful for UI display
        }

    The Streamlit ask.py page uses:
        result["answer"]   → display in chat
        result["sources"]  → display in source viewer component
        result["grounded"] → show warning banner if False
    """
    chunks = retrieve(query=query, subject=subject, semester=semester)

    if not chunks:
        return {
            "answer":   FALLBACK,
            "sources":  [],
            "grounded": False,
            "query":    query,
        }

    prompt = build_qa_prompt(query, chunks)

    if prompt is None:
        return {
            "answer":   FALLBACK,
            "sources":  [],
            "grounded": False,
            "query":    query,
        }

    llm = get_llm()
    answer = llm.generate(prompt)

    sources = [
        {
            "source_file":  c["source_file"],
            "page_number":  c["page_number"],
            "score":        round(c["score"], 3),
        }
        for c in chunks
        if c["score"] > 0.0  # exclude neighbor chunks from citation list
    ]

    return {
        "answer":   answer,
        "sources":  sources,
        "grounded": True,
        "query":    query,
    }
