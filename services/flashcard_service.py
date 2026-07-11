"""Flashcard service."""

from features.flashcards import generate_flashcards


def get_flashcards(
    topic: str,
    subject: str,
    semester: int,
    num_cards: int = 8,
) -> dict:
    """
    Generate study flashcards on a topic.
    """
    return generate_flashcards(
        topic=topic,
        subject=subject,
        semester=semester,
        num_cards=num_cards,
    )
