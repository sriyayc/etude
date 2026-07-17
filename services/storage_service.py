"""Storage service."""

from db.client import get_client

BUCKET_NAME = "documents"


def upload_pdf(file_path: str, storage_path: str):
    client = get_client()
    try:
        with open(file_path, "rb") as file:
            response = client.storage.from_(BUCKET_NAME).upload(storage_path, file)
        return response
    except Exception as e:
        raise Exception(f"Failed to upload PDF: {e}")


def delete_pdf(storage_path: str):
    client = get_client()
    return client.storage.from_(BUCKET_NAME).remove([storage_path])


def download_pdf(storage_path: str):
    client = get_client()
    return client.storage.from_(BUCKET_NAME).download(storage_path)


def get_public_url(storage_path: str):
    client = get_client()
    return client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
