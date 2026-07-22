"""Repository for subjects and slides table operations.

Subjects are identified by ``(semester, slug)``, where the slug is derived
from the subject *name*. PES reissues course codes every academic year, so
keying on the code meant a subject silently became a new subject each June
and lost its uploaded slides. The name is stable; the code is not.
"""

import re

from db.client import get_client


def slugify(subject_name: str) -> str:
    """Derive a subject's stable identifier from its name.

    Mirrors the ``public.subject_slug()`` SQL function exactly -- both sides
    must agree or a lookup will miss a row the DB thinks already exists.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", (subject_name or "").lower())
    return re.sub(r"-{2,}", "-", slug).strip("-")


def list_subjects_by_semester(semester: int) -> list[dict]:
    client = get_client()
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .order("subject_name")
        .execute()
    )
    return response.data or []


def get_subject(semester: int, slug: str) -> dict | None:
    client = get_client()
    response = (
        client.table("subjects")
        .select("*")
        .eq("semester", semester)
        .eq("slug", slug)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def get_subject_any(semester: int, slug: str) -> dict | None:
    """Fetch a subject, tolerating a transient auth/RLS/network hiccup.

    ``get_subject`` runs as the signed-in user. If a page loads before this
    session's token is bound (or a request momentarily fails), that read comes
    back empty and the UI renders an existing subject as "Subject not found".
    The catalog isn't sensitive -- every logged-in user sees all of it -- so
    fall back to the service client for this read-only lookup before giving up.
    """
    try:
        row = get_subject(semester, slug)
    except Exception:
        row = None
    if row is not None:
        return row

    try:
        from db.client import get_service_client

        response = (
            get_service_client()
            .table("subjects")
            .select("*")
            .eq("semester", semester)
            .eq("slug", slug)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def upsert_subject(
    semester: int,
    subject_name: str,
    syllabus_status: str = "current",
    slide_count: int = 0,
    page_count: int = 0,
    slides_document_id: str | None = None,
    notes_document_id: str | None = None,
) -> dict | None:
    """Create or update the (semester, slug) row.

    Only overwrites slides_document_id/notes_document_id when a value is
    given, so syncing a slides upload doesn't clobber a notes doc already
    attached to this subject (and vice versa).
    """
    client = get_client()

    payload = {
        "semester": semester,
        "slug": slugify(subject_name),
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
        .upsert(payload, on_conflict="semester,slug")
        .execute()
    )
    return response.data[0] if response.data else None


def create_subject(semester: int, subject_name: str) -> dict:
    """Add an empty subject to a semester. Admin-only (enforced by RLS)."""
    name = (subject_name or "").strip()
    if not name:
        raise ValueError("Subject name cannot be empty.")

    slug = slugify(name)
    if not slug:
        raise ValueError("Subject name must contain at least one letter or digit.")

    if get_subject(semester, slug) is not None:
        raise ValueError(f"'{name}' already exists in semester {semester}.")

    row = upsert_subject(semester=semester, subject_name=name)
    if row is None:
        raise RuntimeError("Could not create the subject.")
    return row


def delete_subject(semester: int, slug: str) -> None:
    """Remove a subject. Refuses if slides are still attached.

    Deleting a subject with an attached document would orphan its slides,
    ingested chunks and syllabus topics, so the caller has to detach the
    material first -- deliberately a separate, explicit step.
    """
    subject = get_subject(semester, slug)
    if subject is None:
        raise ValueError("That subject no longer exists.")

    if subject.get("slides_document_id"):
        raise ValueError(
            f"'{subject.get('subject_name')}' still has slides attached. "
            "Remove the uploaded material before deleting the subject."
        )

    get_client().table("subjects").delete().eq("semester", semester).eq(
        "slug", slug
    ).execute()


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


def count_slides_for_documents(document_ids: list[str]) -> dict[str, int]:
    """Return {document_id: slide_count} for many decks in a single query.

    Replaces an N+1 (one list_slides per deck) when building the unit picker.
    """
    if not document_ids:
        return {}
    client = get_client()
    response = (
        client.table("slides")
        .select("document_id")
        .in_("document_id", document_ids)
        .execute()
    )
    counts: dict[str, int] = {}
    for row in response.data or []:
        doc_id = str(row.get("document_id"))
        counts[doc_id] = counts.get(doc_id, 0) + 1
    return counts


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
