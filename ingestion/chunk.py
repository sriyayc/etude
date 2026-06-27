
import hashlib
from datetime import datetime, timezone


def chunk_pages(
    pages: list[dict],
    document_id: str,
    source_file: str,
    document_type: str,
    subject: str,
    semester: int,
    embedding_model: str,
    version: int = 1,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Split pages into chunks. Each chunk has full metadata for ingestion.
    """
    allchunks = []
    chunk_index = 0
    
    for page in pages:
        words = page["text"].split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if not chunk_text.strip():
                continue
            
            content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            #same text always provides same hashing here
            chunk = {
                "chunk_id": f"{document_id}_chunk_{chunk_index}",
                "document_id": document_id,
                "source_file": source_file,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "document_type": document_type,
                "subject": subject,
                "semester": semester,
                "unit_number": None,
                "topic": None,
                "embedding_model": embedding_model,
                "content_hash": content_hash,
                "version": version,
                "is_current": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            allchunks.append(chunk)
            chunk_index += 1
    
    return allchunks

