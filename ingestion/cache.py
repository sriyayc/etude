"""Embedding cache via content hash check."""

from providers.factory import get_vectorstore


def filter_new_chunks(chunks: list[dict], vectorstore) -> tuple[list[dict], int]:
    """
    Remove chunks whose content_hash already exists in Qdrant.
    
    Returns:
        (new_chunks_to_embed, skipped_count)
    """
    if not chunks:
        return [], 0
    
    hashes = [c["content_hash"] for c in chunks]
    existing_hashes = _fetch_existing_hashes(vectorstore, hashes)
    
    new_chunks = [c for c in chunks if c["content_hash"] not in existing_hashes]
    skipped = len(chunks) - len(new_chunks)
    
    return new_chunks, skipped


def _fetch_existing_hashes(vectorstore, hashes: list[str]) -> set[str]:
    """Query Qdrant for any chunks already stored with these hashes."""
    existing = set()
    
    for h in hashes:
        records = vectorstore.fetch_by_filter(
            filters={"content_hash": h},
            limit=1
        )
        if records:
            existing.add(h)
    
    return existing


