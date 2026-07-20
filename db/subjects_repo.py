"""Repository for subjects and slides table operations."""

from db.client import get_client


def list_subjects_by_semester(semester: int) -> list[dict]:
    client = get_client()
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .order("subject_code")
        .execute()
    )
    return response.data or []


def get_subject(semester: int, subject_code: str) -> dict | None:
    client = get_client()
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .eq("subject_code", subject_code)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_subject(
    semester: int,
    subject_code: str,
    subject_name: str,
    syllabus_status: str = "current",
    slide_count: int = 0,
    page_count: int = 0,
    slides_document_id: str | None = None,
    notes_document_id: str | None = None,
) -> dict | None:
    """Create or update the (semester, subject_code) row.

    Only overwrites slides_document_id/notes_document_id when a value is
    given, so syncing a slides upload doesn't clobber a notes doc already
    attached to this subject (and vice versa).
    """
    client = get_client()

    payload = {
        "semester": semester,
        "subject_code": subject_code,
        "subject_name": subject_name,
        "syllabus_status": syllabus_status,
        "slide_count": slide_count,
        "page_count": page_count,
    }
    if slides_document_id is not None:
        payload["slides_document_id"] = slides_document_id
    if notes_document_id is not None:
        payload["notes_document_id"] = notes_document_id

    response = (
        client.table("subjects")
        .upsert(payload, on_conflict="semester,subject_code")
        .execute()
    )
    return response.data[0] if response.data else None


def bulk_upsert_slides(slides: list[dict]) -> list[dict]:
    """Create or update slide rows.

    Each dict needs: document_id, slide_number, module_number, title, content.
    Upserts on the (document_id, slide_number) unique constraint so
    re-syncing the same document is idempotent.
    """
    if not slides:
        return []

    client = get_client()
    response = (
        client.table("slides")
        .upsert(slides, on_conflict="document_id,slide_number")
        .execute()
    )
    return response.data or []


def list_slides(document_id: str) -> list[dict]:
    client = get_client()
    response = (
        client.table("slides")
        .select("*")
        .eq("document_id", document_id)
        .order("slide_number")
        .execute()
    )
    return response.data or []


def get_slide(document_id: str, slide_number: int) -> dict | None:
    client = get_client()
    response = (
        client.table("slides")
        .select("*")
        .eq("document_id", document_id)
        .eq("slide_number", slide_number)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
