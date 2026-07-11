"""Syllabus tagger module."""

import logging
from db.syllabus_repo import list_current_topics
from providers.factory import get_embedder, get_vectorstore

logger = logging.getLogger(__name__)


def tag_document_chunks(
    document_id: str,
    subject: str,
    semester: int,
) -> int:
    """
    Tag ingested document chunks in Qdrant with matching syllabus topics using semantic similarity.
    Returns the number of chunks successfully tagged.
    """
    # 1. Fetch current syllabus topics
    topics = list_current_topics(subject=subject, semester=semester)
    if not topics:
        logger.warning(f"No active syllabus topics found for subject '{subject}', semester {semester}.")
        return 0

    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    tagged_count = 0

    # 2. For each syllabus topic, find the top matching chunks in Qdrant and tag them
    for t in topics:
        topic_text = t["topic"]
        unit_num = t["unit_number"]

        try:
            # Embed the topic text as a retrieval query
            vectors = embedder.embed([topic_text], task="retrieval.query")
            if not vectors:
                continue
            query_vector = vectors[0]

            # Query Qdrant, filtering by the specific document
            results = vectorstore.query(
                vector=query_vector,
                n=3,  # tag the top 3 most semantically relevant chunks
                filters={"document_id": document_id, "is_current": True},
                score_threshold=0.25,  # must meet a minimum similarity threshold
            )

            if not results:
                continue

            point_ids = [res["id"] for res in results]

            # Update the metadata payload of these points in Qdrant
            vectorstore.client.set_payload(
                collection_name=vectorstore.collection_name,
                payload={
                    "topic": topic_text,
                    "unit_number": unit_num,
                },
                points=point_ids,
            )
            tagged_count += len(point_ids)

        except Exception as e:
            logger.error(f"Failed to tag chunks for topic '{topic_text}': {e}")
            continue

    return tagged_count
