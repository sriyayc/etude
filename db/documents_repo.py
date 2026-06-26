"""Repository for documents table operations."""

from db.client import get_client

client = get_client()



def create_document(
    uploaded_by: str,
    title: str,
    storage_bucket: str,
    storage_path: str,
    document_type: str,
):
    response = (
        client.table("documents")
        .insert(
            {
                "uploaded_by": uploaded_by,
                "title": title,
                "storage_bucket": storage_bucket,
                "storage_path": storage_path,
                "document_type": document_type,
            }
        )
        .execute()
    )

    return response.data



def get_document(document_id: str):
    response = (
        client.table("documents")
        .select("*")
        .eq("id", document_id)
        .single()
        .execute()
    )

    return response.data




def list_documents():
    response = (
        client.table("documents")
        .select("*")
        .execute()
    )

    return response.data




def delete_document(document_id: str):
    response = (
        client.table("documents")
        .delete()
        .eq("id", document_id)
        .execute()
    )

    return response.data




def update_document(document_id: str, updates: dict):
    response = (
        client.table("documents")
        .update(updates)
        .eq("id", document_id)
        .execute()
    )

    return response.data






