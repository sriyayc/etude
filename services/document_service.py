"""Document service."""

import os
import hashlib

from services.auth_service import require_teacher
from services.storage_service import upload_pdf
from db.documents_repo import (
    create_document,
    get_document_by_hash,
    list_documents,
    mark_outdated
)


def upload_document(
    file_path: str,
    title: str,
    document_type: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Upload a document to storage, version it, and save its metadata in Supabase.
    """
    teacher = require_teacher()

    # 1. Compute content hash to ensure idempotency
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    content_hash = hasher.hexdigest()

    existing = get_document_by_hash(content_hash)
    if existing:
        return {
            "success": True,
            "message": "Document already exists (content hash match).",
            "title": existing["title"],
            "document_type": existing["document_type"],
            "storage_path": existing["storage_path"],
            "document_id": existing["id"],
        }

    # 2. Upload the file to storage
    filename = os.path.basename(file_path)
    storage_path = f"{document_type}/{filename}"

    upload_pdf(
        file_path=file_path,
        storage_path=storage_path,
    )

    # 3. Handle versioning if a document with the same title/subject already exists
    current_docs = list_documents(subject=subject, semester=semester, is_current=True)
    matching_doc = next((d for d in current_docs if d["title"].lower() == title.lower()), None)
    
    version = 1
    if matching_doc:
        mark_outdated(matching_doc["id"])
        version = matching_doc["version"] + 1

    # 4. Save metadata in Database
    doc = create_document(
        uploaded_by=teacher["user_id"],
        title=title,
        storage_bucket="documents",
        storage_path=storage_path,
        document_type=document_type,
        subject=subject,
        semester=semester,
        content_hash=content_hash,
        version=version,
        is_current=True,
    )

    return {
        "success": True,
        "message": "Document uploaded successfully.",
        "title": title,
        "document_type": document_type,
        "storage_path": storage_path,
        "document_id": doc["id"] if doc else None,
        "version": version,
    }