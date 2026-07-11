"""Retriever module for semantic search in Qdrant."""

import logging
from providers.factory import get_embedder, get_vectorstore

logger = logging.getLogger(__name__)

def retrieve(
    query: str,
    subject: str,
    semester: int,
    n: int = 5,
    document_type: str = None,
    document_id: str = None,
    score_threshold: float = 0.0,
) -> list[dict]:
    """
    Retrieve top-n relevant chunks from the vector store for a given query,
    applying filters for subject, semester, and other optional metadata.
    
    Args:
        query: The user's search query or question.
        subject: The subject to search within (e.g., 'python').
        semester: The semester number (e.g., 1).
        n: Number of relevant chunks to retrieve. Default is 5.
        document_type: Optional document type to filter by (e.g., 'textbook', 'slides').
        document_id: Optional document UUID to filter by.
        score_threshold: Minimum similarity score threshold.
        
    Returns:
        List of retrieved chunks, where each chunk is a formatted dictionary:
        {
            "chunk_id": str,
            "document_id": str,
            "source_file": str,
            "page_number": int,
            "chunk_index": int,
            "chunk_text": str,
            "document_type": str,
            "subject": str,
            "semester": int,
            "score": float
        }
    """
    if not query.strip():
        logger.warning("Empty query received for retrieval.")
        return []

    try:
        # 1. Initialize the embedding provider and vector store
        embedder = get_embedder()
        vectorstore = get_vectorstore(dimension=embedder.dimension)
        
        # 2. Embed the query with the query-specific task
        query_vectors = embedder.embed([query], task="retrieval.query")
        if not query_vectors:
            logger.error("Embedding provider returned empty vector list.")
            return []
        query_vector = query_vectors[0]
        
        # 3. Construct filters for Qdrant payload search
        filters = {
            "is_current": True,
            "subject": subject,
            "semester": semester,
        }
        
        if document_type:
            filters["document_type"] = document_type
        if document_id:
            filters["document_id"] = document_id
            
        # 4. Perform vector similarity query
        raw_results = vectorstore.query(
            vector=query_vector,
            n=n,
            filters=filters,
            score_threshold=score_threshold,
        )
        
        # 5. Format the results
        retrieved_chunks = []
        for res in raw_results:
            payload = res.get("payload", {})
            retrieved_chunks.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "source_file": payload.get("source_file"),
                "page_number": payload.get("page_number"),
                "chunk_index": payload.get("chunk_index"),
                "chunk_text": payload.get("chunk_text"),
                "document_type": payload.get("document_type"),
                "subject": payload.get("subject"),
                "semester": payload.get("semester"),
                "score": res.get("score", 0.0),
            })
            
        return retrieved_chunks

    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return []