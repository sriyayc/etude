"""Document service."""

import os
import hashlib

from services.auth_service import require_admin
from services.storage_service import upload_pdf
from db.documents_repo import (
    create_document,
    get_document_by_hash,
    list_documents,
    mark_outdated,
)


def upload_document(
    file_path: str,
    title: str,
    document_type: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Upload a document to storage, version it, and save metadata in Supabase.
    Idempotent — skips if content hash already exists.
    """
    admin = require_admin()

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    content_hash = hasher.hexdigest()

    existing = get_document_by_hash(content_hash)
    if existing:
        return {
            "success":       True,
            "message":       "Document already exists (content hash match).",
            "title":         existing["title"],
            "document_type": existing["document_type"],
            "storage_path":  existing["storage_path"],
            "document_id":   existing["id"],
            "version":       existing["version"],
        }

    # Namespace by semester/subject and prefix with the content hash so two
    # different files that happen to share a name (e.g. every subject having a
    # "unit_4.pdf") can't collide in the bucket. A bare "{type}/{filename}"
    # path made a chemistry upload 409 against a statics file of the same name.
    filename = os.path.basename(file_path)
    storage_path = f"{document_type}/{semester}/{subject}/{content_hash[:12]}-{filename}"

    upload_pdf(file_path=file_path, storage_path=storage_path)

    current_docs = list_documents(subject=subject, semester=semester, is_current=True)
    matching = next(
        (d for d in current_docs if d["title"].lower() == title.lower()),
        None
    )

    version = 1
    if matching:
        mark_outdated(matching["id"])
        version = matching["version"] + 1

    doc = create_document(
        uploaded_by=admin["user_id"],
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
        "success":       True,
        "message":       "Document uploaded successfully.",
        "title":         title,
        "document_type": document_type,
        "storage_path":  storage_path,
        "document_id":   doc["id"] if doc else None,
        "version":       version,
    }
