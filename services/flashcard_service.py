"""Flashcard service."""

from features.flashcards import generate_flashcards as _generate_flashcards
from db import generated_content_repo


def get_flashcards(
    topic: str,
    subject: str,
    semester: int,
    unit_number: int,
    num_cards: int = 8,
) -> dict:
    """
    Get the flashcard set for a unit -- generated once and cached, not
    regenerated per student per visit.
    """
    cached = generated_content_repo.get_cached_flashcards(subject, semester, unit_number)
    if cached:
        return {
            "success": True,
            "cards": cached["cards"],
            "sources": cached.get("sources") or [],
        }

    result = _generate_flashcards(
        topic=topic,
        subject=subject,
        semester=semester,
        num_cards=num_cards,
    )

    if result.get("success"):
        generated_content_repo.save_flashcards(
            subject=subject,
            semester=semester,
            unit_number=unit_number,
            unit_title=topic,
            cards=result["cards"],
            sources=result.get("sources") or [],
        )

    return result
