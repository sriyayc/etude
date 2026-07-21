"""Revision notes generation feature."""

import logging
from retrieval.retriever import retrieve
from prompts.notes_prompt import build_notes_prompt
from providers.factory import get_llm

logger = logging.getLogger(__name__)

def generate_notes(
    topic: str,
    subject: str,
    semester: int,
    chunks: list | None = None,
) -> dict:
    """
    Generate revision/study notes on a topic using retrieved reference materials.
    """
    # A caller can pass deck-specific grounding (the unit's own slides). Only
    # fall back to subject-wide semantic retrieval when it doesn't.
    if not chunks:
        chunks = retrieve(query=topic, subject=subject, semester=semester)
    
    if not chunks:
        return {
            "success": False,
            "message": f"No reference materials found for topic '{topic}' to generate notes.",
            "notes_md": ""
        }
        
    prompt = build_notes_prompt(topic, chunks)
    
    llm = get_llm()
    notes_md = llm.generate(prompt)
    
    return {
        "success": True,
        "notes_md": notes_md,
        "sources": [
            {
                "source_file": c["source_file"],
                "page_number": c["page_number"]
            }
            for c in chunks
        ]
    }
