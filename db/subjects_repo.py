"""Repository for subjects and slides table operations."""

from db.client import get_client

client = get_client()


def list_subjects_by_semester(semester: int) -> list[dict]:
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .order("subject_code")
        .execute()
    )
    return response.data or []


def get_subject(semester: int, subject_code: str) -> dict | None:
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .eq("subject_code", subject_code)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def list_slides(document_id: str) -> list[dict]:
    response = (
        client.table("slides")
        .select("*")
        .eq("document_id", document_id)
        .order("slide_number")
        .execute()
    )
    return response.data or []


def get_slide(document_id: str, slide_number: int) -> dict | None:
    response = (
        client.table("slides")
        .select("*")
        .eq("document_id", document_id)
        .eq("slide_number", slide_number)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
