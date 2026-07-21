"""Flashcards generation feature."""

import json
import logging
from retrieval.retriever import retrieve
from prompts.flashcard_prompt import build_flashcard_prompt
from providers.factory import get_llm

logger = logging.getLogger(__name__)

def generate_flashcards(
    topic: str,
    subject: str,
    semester: int,
    num_cards: int = 8,
    chunks: list | None = None,
) -> dict:
    """
    Generate study flashcards on a topic using retrieved reference materials.
    """
    # A caller can pass deck-specific grounding (the unit's own slides). Only
    # fall back to subject-wide semantic retrieval when it doesn't.
    if not chunks:
        chunks = retrieve(query=topic, subject=subject, semester=semester)
    
    if not chunks:
        return {
            "success": False,
            "message": f"No reference materials found for topic '{topic}' to generate flashcards.",
            "cards": []
        }
        
    prompt = build_flashcard_prompt(topic, chunks, num_cards)
    
    llm = get_llm()
    raw_response = llm.generate(prompt)
    
    try:
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        cards = json.loads(clean_response)
        
        return {
            "success": True,
            "cards": cards,
            "sources": [
                {
                    "source_file": c["source_file"],
                    "page_number": c["page_number"]
                }
                for c in chunks
            ]
        }
    except Exception as e:
        logger.error(f"Failed to parse flashcard response: {e}\nRaw response:\n{raw_response}")
        return {
            "success": False,
            "message": "Failed to parse the generated flashcards. Please try again.",
            "cards": []
        }
