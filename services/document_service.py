"""Document service."""

import os

from services.auth_service import require_teacher
from services.storage_service import upload_pdf
from db.documents_repo import create_document


def upload_document(
    file_path: str,
    title: str,
    document_type: str,
) -> dict:
    """
    Upload a document to storage and save its metadata.
    """

    teacher = require_teacher()

    filename = os.path.basename(file_path)

    storage_path = f"{document_type}/{filename}"

    upload_pdf(
        file_path=file_path,
        storage_path=storage_path,
    )

    create_document(
        uploaded_by=teacher["user_id"],
        title=title,
        storage_bucket="documents",
        storage_path=storage_path,
        document_type=document_type,
    )

    return {
        "success": True,
        "message": "Document uploaded successfully.",
        "title": title,
        "document_type": document_type,
        "storage_path": storage_path,
    }