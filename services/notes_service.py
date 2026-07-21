"""Notes service."""

from features.notes import generate_notes as _generate_notes
from db import generated_content_repo
from services import grounding


def get_revision_notes(
    topic: str,
    subject: str,
    semester: int,
    unit_number: int,
    document_id: str | None = None,
) -> dict:
    """
    Get the revision notes for a unit -- generated once and cached, not
    regenerated per student per visit.
    """
    cached = generated_content_repo.get_cached_notes(subject, semester, unit_number)
    if cached:
        return {
            "success": True,
            "notes_md": cached["notes_md"],
            "sources": cached.get("sources") or [],
        }

    chunks = grounding.deck_chunks(document_id, source_file=topic) if document_id else None
    result = _generate_notes(
        topic=topic,
        subject=subject,
        semester=semester,
        chunks=chunks or None,
    )

    if result.get("success"):
        generated_content_repo.save_notes(
            subject=subject,
            semester=semester,
            unit_number=unit_number,
            unit_title=topic,
            notes_md=result["notes_md"],
            sources=result.get("sources") or [],
        )

    return result
