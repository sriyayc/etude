"""Notes service."""

from features.notes import generate_notes


def get_revision_notes(
    topic: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Generate study notes on a topic.
    """
    return generate_notes(
        topic=topic,
        subject=subject,
        semester=semester,
    )
