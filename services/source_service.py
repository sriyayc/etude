"""Source service."""

from services.storage_service import get_signed_url
from db.documents_repo import get_document, list_documents


def get_document_url(document_id: str) -> str:
    """
    Get a time-limited download/view URL for a document. The storage
    bucket is private, so this must be a signed URL, not the public one.
    """
    doc = get_document(document_id)
    if doc:
        return get_signed_url(doc["storage_path"])
    return None


def get_available_sources(subject: str = None, semester: int = None) -> list[dict]:
    """
    List all available documents for a subject and semester.
    """
    return list_documents(subject=subject, semester=semester, is_current=True)
