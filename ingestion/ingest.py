"""Ingestion orchestrator."""

import os
import hashlib
import uuid

from ingestion.extract import extract_pages
from ingestion.chunk import chunk_pages
from ingestion.cache import filter_new_chunks
from providers.factory import get_embedder, get_vectorstore


def ingest_pdf(
    pdf_path: str,
    document_type: str,
    subject: str,
    semester: int,
    version: int = 1,
) -> dict:
    """
    Full ingestion pipeline for a single PDF.
    
    Returns:
        {
            "document_id": str,
            "source_file": str,
            "chunks_created": int,
            "chunks_embedded": int,
            "chunks_skipped": int,
        }
    """
    source_file = os.path.basename(pdf_path)
    document_id = _compute_document_id(pdf_path)
    
    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)
    vectorstore.ensure_collection()
    
    print(f"Extracting: {source_file}")
    pages = extract_pages(pdf_path)
    
    print(f"Chunking: {len(pages)} pages")
    chunks = chunk_pages(
        pages=pages,
        document_id=document_id,
        source_file=source_file,
        document_type=document_type,
        subject=subject,
        semester=semester,
        embedding_model=embedder.model_name,
        version=version,
    )
    chunks_created = len(chunks)
    
    print(f"Checking cache: {chunks_created} chunks")
    new_chunks, skipped = filter_new_chunks(chunks, vectorstore)
    
    if not new_chunks:
        print(f"All {skipped} chunks already in Qdrant. Nothing to embed.")
        return {
            "document_id": document_id,
            "source_file": source_file,
            "chunks_created": chunks_created,
            "chunks_embedded": 0,
            "chunks_skipped": skipped,
        }
    
    print(f"Embedding: {len(new_chunks)} new chunks")
    texts = [c["chunk_text"] for c in new_chunks]
    embeddings = embedder.embed(texts, task="retrieval.passage")
    
    print(f"Upserting to Qdrant")
    ids = [_chunk_id_to_uuid(c["chunk_id"]) for c in new_chunks]
    payloads = [_chunk_to_payload(c) for c in new_chunks]
    vectorstore.upsert(ids=ids, vectors=embeddings, payloads=payloads)
    
    print(f"Done.")
    return {
        "document_id": document_id,
        "source_file": source_file,
        "chunks_created": chunks_created,
        "chunks_embedded": len(new_chunks),
        "chunks_skipped": skipped,
    }


def _compute_document_id(pdf_path: str) -> str:
    """Generate deterministic document_id from file content."""
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def _chunk_to_payload(chunk: dict) -> dict:
    """Strip chunk_text from payload? No — keep it for retrieval."""
    return chunk

def _chunk_id_to_uuid(chunk_id: str) -> str:
    """Convert human-readable chunk_id to deterministic UUID for Qdrant."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))


if __name__ == "__main__":
    result = ingest_pdf(
        pdf_path="data/textbooks/python_notes.pdf",
        document_type="lecture_notes",
        subject="python",
        semester=1,
    )
    print(f"\nResult: {result}")