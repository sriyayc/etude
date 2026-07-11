"""Source service."""

from services.storage_service import get_public_url
from db.documents_repo import get_document, list_documents


def get_document_url(document_id: str) -> str:
    """
    Get the public URL of a document.
    """
    doc = get_document(document_id)
    if doc:
        return get_public_url(doc["storage_path"])
    return None


def get_available_sources(subject: str = None, semester: int = None) -> list[dict]:
    """
    List all available documents for a subject and semester.
    """
    return list_documents(subject=subject, semester=semester, is_current=True)
