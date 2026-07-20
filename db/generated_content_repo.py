"""Repository for cached per-unit generated content.

Quiz/flashcards/notes are generated once per (subject, semester,
unit_number) and shared by every student who opens that unit -- not
regenerated per student per visit.
"""

from db.client import get_client


def get_cached_quiz(subject: str, semester: int, unit_number: int) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_quizzes")
        .select("*")
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("unit_number", unit_number)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def save_quiz(
    subject: str,
    semester: int,
    unit_number: int,
    unit_title: str,
    questions: list[dict],
    sources: list[dict],
) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_quizzes")
        .upsert(
            {
                "subject": subject,
                "semester": semester,
                "unit_number": unit_number,
                "unit_title": unit_title,
                "questions": questions,
                "sources": sources,
            },
            on_conflict="subject,semester,unit_number",
        )
        .execute()
    )
    return response.data[0] if response.data else None


def get_cached_flashcards(subject: str, semester: int, unit_number: int) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_flashcards")
        .select("*")
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("unit_number", unit_number)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def save_flashcards(
    subject: str,
    semester: int,
    unit_number: int,
    unit_title: str,
    cards: list[dict],
    sources: list[dict],
) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_flashcards")
        .upsert(
            {
                "subject": subject,
                "semester": semester,
                "unit_number": unit_number,
                "unit_title": unit_title,
                "cards": cards,
                "sources": sources,
            },
            on_conflict="subject,semester,unit_number",
        )
        .execute()
    )
    return response.data[0] if response.data else None


def get_cached_notes(subject: str, semester: int, unit_number: int) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_notes")
        .select("*")
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("unit_number", unit_number)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def save_notes(
    subject: str,
    semester: int,
    unit_number: int,
    unit_title: str,
    notes_md: str,
    sources: list[dict],
) -> dict | None:
    client = get_client()
    response = (
        client.table("unit_notes")
        .upsert(
            {
                "subject": subject,
                "semester": semester,
                "unit_number": unit_number,
                "unit_title": unit_title,
                "notes_md": notes_md,
                "sources": sources,
            },
            on_conflict="subject,semester,unit_number",
        )
        .execute()
    )
    return response.data[0] if response.data else None
