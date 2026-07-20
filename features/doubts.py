"""Doubts resolution feature."""

import logging
from retrieval.retriever import retrieve
from prompts.doubts_prompt import build_doubts_prompt
from providers.factory import get_llm

logger = logging.getLogger(__name__)

def resolve_doubt(
    doubt: str,
    subject: str,
    semester: int
) -> dict:
    """
    Resolve a student's doubt using reference materials.
    """
    chunks = retrieve(query=doubt, subject=subject, semester=semester)
    
    if not chunks:
        return {
            "success": False,
            "message": "No reference materials found to resolve this doubt.",
            "answer": "This topic is not covered in the provided material."
        }
        
    prompt = build_doubts_prompt(doubt, chunks)
    
    llm = get_llm()
    answer = llm.generate(prompt)
    
    return {
        "success": True,
        "answer": answer,
        "sources": [
            {
                "source_file": c["source_file"],
                "page_number": c["page_number"]
            }
            for c in chunks
        ]
    }
