"""Doubts service."""

from features.doubts import resolve_doubt


def clear_doubt(
    doubt: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Resolve a student's doubt.
    """
    return resolve_doubt(
        doubt=doubt,
        subject=subject,
        semester=semester,
    )
