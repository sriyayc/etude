
"""Storage service."""

from db.client import get_client

client = get_client()

BUCKET_NAME = "documents"


def upload_pdf(file_path: str, storage_path: str):
    """
    Upload a PDF to Supabase Storage.
    """

    try:
        with open(file_path, "rb") as file:
            response = client.storage.from_(BUCKET_NAME).upload(
                storage_path,
                file,
            )

        return response

    except Exception as e:
        raise Exception(f"Failed to upload PDF: {e}")


def delete_pdf(storage_path: str):
    """
    Delete a PDF from Supabase Storage.
    """

    return client.storage.from_(BUCKET_NAME).remove(
        [storage_path]
    )


def download_pdf(storage_path: str):
    """
    Download a PDF from Supabase Storage.
    """

    return client.storage.from_(BUCKET_NAME).download(
        storage_path
    )


def get_public_url(storage_path: str):
    """
    Get the public URL of a stored file.
    """

    return client.storage.from_(BUCKET_NAME).get_public_url(
        storage_path
    )

