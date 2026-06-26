"""Repository for documents table operations."""

from db.client import get_client


def create_document(
    uploaded_by: str,
    title: str,
    storage_bucket: str,
    storage_path: str,
    document_type: str,
    subject: str,
    semester: int,
    content_hash: str,
    version: int = 1,
    is_current: bool = True,
):
    client = get_client()
    response = client.table("documents").insert({
        "uploaded_by": uploaded_by,
        "title": title,
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "document_type": document_type,
        "subject": subject,
        "semester": semester,
        "content_hash": content_hash,
        "version": version,
        "is_current": is_current,
    }).execute()
    return response.data[0] if response.data else None


def get_document(document_id: str):
    client = get_client()
    response = client.table("documents").select("*").eq("id", document_id).single().execute()
    return response.data


def get_document_by_hash(content_hash: str):
    """Used for idempotent ingestion — skip if already exists."""
    client = get_client()
    response = client.table("documents").select("*").eq("content_hash", content_hash).execute()
    return response.data[0] if response.data else None


def list_documents(subject: str = None, semester: int = None, is_current: bool = True):
    client = get_client()
    query = client.table("documents").select("*").eq("is_current", is_current)
    if subject:
        query = query.eq("subject", subject)
    if semester is not None:
        query = query.eq("semester", semester)
    response = query.execute()
    return response.data


def delete_document(document_id: str):
    client = get_client()
    response = client.table("documents").delete().eq("id", document_id).execute()
    return response.data


def mark_outdated(document_id: str):
    """Used when a new version supersedes this one."""
    client = get_client()
    response = client.table("documents").update({"is_current": False}).eq("id", document_id).execute()
    return response.data