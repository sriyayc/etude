"""Ingestion service."""

from services.auth_service import require_teacher
from ingestion.ingest import ingest_pdf


def ingest_document(
    pdf_path: str,
    document_type: str,
    subject: str,
    semester: int,
    version: int = 1,
) -> dict:
    """
    Ingest a PDF document (extract, chunk, embed, and load to vector store).
    Only teachers can trigger ingestion.
    """
    require_teacher()
    return ingest_pdf(
        pdf_path=pdf_path,
        document_type=document_type,
        subject=subject,
        semester=semester,
        version=version,
    )
