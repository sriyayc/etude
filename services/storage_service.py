"""Storage service."""

from db.client import get_client

BUCKET_NAME = "documents"


def upload_pdf(file_path: str, storage_path: str):
    client = get_client()
    try:
        with open(file_path, "rb") as file:
            response = client.storage.from_(BUCKET_NAME).upload(
                storage_path, file, file_options={"content-type": "application/pdf"}
            )
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


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Time-limited URL for a file in the "documents" bucket.

    The bucket is private, so get_public_url() returns a URL that 403s --
    this is what the slide viewer and any other real download link must
    use instead. expires_in is in seconds (default 1 hour).
    """
    client = get_client()
    response = client.storage.from_(BUCKET_NAME).create_signed_url(
        storage_path, expires_in
    )
    return response["signedURL"]
