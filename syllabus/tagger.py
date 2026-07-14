"""
Syllabus tagger — two responsibilities:

1. tag_document_chunks(document_id, subject, semester)
   Run after ingestion. Tags each chunk with its matching syllabus topic
   and unit_number by doing semantic search over current syllabus topics.
   Populates the topic + unit_number payload fields in Qdrant.

2. apply_syllabus_diff(diff, subject, semester)
   Run after a new syllabus is uploaded and compared.
   Marks removed topic chunks as is_current=False.
   Marks moved topic chunks stale in their old unit.
   Confirms added topic chunks are is_current=True.

ORDER: tag_document_chunks must run BEFORE apply_syllabus_diff
because staleness marking relies on topic field being populated.
"""

import logging
from datetime import datetime, timezone

from db.syllabus_repo import list_current_topics
from providers.factory import get_embedder, get_vectorstore

logger = logging.getLogger(__name__)

STALE_RETENTION_YEARS = 3


# ------------------------------------------------------------------ #
#  Job 1 — Chunk tagging (run after ingestion)                        #
# ------------------------------------------------------------------ #

def tag_document_chunks(
    document_id: str,
    subject: str,
    semester: int,
) -> int:
    """
    Tag ingested document chunks in Qdrant with matching syllabus topics.
    For each syllabus topic, finds the top semantically matching chunks
    and sets their topic + unit_number payload fields.

    Returns the number of chunks successfully tagged.
    """
    topics = list_current_topics(subject=subject, semester=semester)
    if not topics:
        logger.warning(f"No active syllabus topics for '{subject}' semester {semester}.")
        return 0

    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    tagged_count = 0

    for t in topics:
        topic_text = t["topic"]
        unit_num = t["unit_number"]

        try:
            vectors = embedder.embed([topic_text], task="retrieval.query")
            if not vectors:
                continue
            query_vector = vectors[0]

            results = vectorstore.query(
                vector=query_vector,
                n=3,
                filters={"document_id": document_id, "is_current": True},
                score_threshold=0.25,
            )

            if not results:
                continue

            point_ids = [res["id"] for res in results]

            vectorstore.client.set_payload(
                collection_name=vectorstore.collection_name,
                payload={
                    "topic":       topic_text,
                    "unit_number": unit_num,
                },
                points=point_ids,
            )
            tagged_count += len(point_ids)

        except Exception as e:
            logger.error(f"Failed to tag chunks for topic '{topic_text}': {e}")
            continue

    return tagged_count


# ------------------------------------------------------------------ #
#  Job 2 — Staleness marking (run after syllabus comparison)          #
# ------------------------------------------------------------------ #

def apply_syllabus_diff(
    diff: dict,
    subject: str,
    semester: int,
) -> dict:
    """
    Apply comparator diff to Qdrant.
    Marks removed topics as stale, confirms added topics are current.

    Args:
        diff:     Output from comparator.compare_syllabi_json()
        subject:  e.g. "Operating Systems"
        semester: e.g. 4

    Returns counts of chunks updated.
    """
    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    stale_count = 0
    current_count = 0
    topics_processed = 0

    for topic in diff["topics"]["removed"]:
        count = _mark_topic_stale(
            topic_name=topic["name"],
            subject=subject,
            semester=semester,
            vectorstore=vectorstore,
            embedder=embedder,
        )
        stale_count += count
        topics_processed += 1
        print(f"  Marked stale: {topic['name']} ({count} chunks)")

    for topic in diff["topics"]["moved"]:
        stale = _mark_topic_stale(
            topic_name=topic["name"],
            subject=subject,
            semester=semester,
            vectorstore=vectorstore,
            embedder=embedder,
        )
        stale_count += stale
        topics_processed += 1
        print(f"  Marked moved: {topic['name']} ({topic['from_unit']} → {topic['to_unit']})")

    for topic in diff["topics"]["added"]:
        count = _confirm_topic_current(
            topic_name=topic["name"],
            subject=subject,
            semester=semester,
            vectorstore=vectorstore,
        )
        current_count += count
        topics_processed += 1

    return {
        "chunks_marked_stale":      stale_count,
        "chunks_confirmed_current": current_count,
        "topics_processed":         topics_processed,
    }


# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #

def _mark_topic_stale(
    topic_name: str,
    subject: str,
    semester: int,
    vectorstore,
    embedder,
) -> int:
    """Mark all chunks related to a topic as is_current=False using two strategies."""

    # Strategy 1 — exact topic field match
    chunks_by_topic = vectorstore.fetch_by_filter(
        filters={
            "subject":    subject,
            "semester":   semester,
            "topic":      topic_name,
            "is_current": True,
        },
        limit=5000,
    )

    # Strategy 2 — semantic search
    topic_vector = embedder.embed([topic_name], task="retrieval.query")[0]
    semantic_results = vectorstore.query(
        vector=topic_vector,
        n=50,
        filters={
            "subject":    subject,
            "semester":   semester,
            "is_current": True,
        },
        score_threshold=0.80,
    )

    chunk_ids = set()
    for chunk in chunks_by_topic:
        chunk_ids.add(chunk["id"])
    for result in semantic_results:
        chunk_ids.add(result["id"])

    if not chunk_ids:
        return 0

    _set_staleness(list(chunk_ids), is_current=False, vectorstore=vectorstore)
    return len(chunk_ids)


def _confirm_topic_current(
    topic_name: str,
    subject: str,
    semester: int,
    vectorstore,
) -> int:
    """Ensure newly added topic chunks are marked is_current=True."""
    chunks = vectorstore.fetch_by_filter(
        filters={
            "subject":    subject,
            "semester":   semester,
            "topic":      topic_name,
            "is_current": False,
        },
        limit=5000,
    )
    chunk_ids = [c["id"] for c in chunks]
    if not chunk_ids:
        return 0
    _set_staleness(chunk_ids, is_current=True, vectorstore=vectorstore)
    return len(chunk_ids)


def _set_staleness(chunk_ids: list[str], is_current: bool, vectorstore) -> None:
    vectorstore.client.set_payload(
        collection_name=vectorstore.collection_name,
        payload={"is_current": is_current},
        points=chunk_ids,
    )


# ------------------------------------------------------------------ #
#  Stale retrieval — "learn anyway" feature                           #
# ------------------------------------------------------------------ #

def retrieve_stale(query: str, subject: str, semester: int) -> list[dict]:
    """
    Retrieve chunks from stale/removed topics.
    Called when student asks about a removed topic and wants to learn it anyway.
    """
    from retrieval.retriever import retrieve
    return retrieve(
        query=query,
        subject=subject,
        semester=semester,
        score_threshold=0.65,
        stale_override=True,
    )


# ------------------------------------------------------------------ #
#  Cleanup job — run every 3-4 years                                  #
# ------------------------------------------------------------------ #

def cleanup_old_stale_chunks(subject: str, semester: int) -> int:
    """
    Permanently delete stale chunks older than STALE_RETENTION_YEARS.
    Keeps storage bounded for a long-running community tool.
    """
    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    stale_chunks = vectorstore.fetch_by_filter(
        filters={"subject": subject, "semester": semester, "is_current": False},
        limit=50000,
    )

    cutoff = datetime.now(timezone.utc)
    old_ids = []

    for chunk in stale_chunks:
        created_at = chunk["payload"].get("created_at")
        if not created_at:
            continue
        created = datetime.fromisoformat(created_at)
        age_years = (cutoff - created).days / 365
        if age_years >= STALE_RETENTION_YEARS:
            old_ids.append(chunk["id"])

    if old_ids:
        vectorstore.delete_by_ids(old_ids)
        print(f"Deleted {len(old_ids)} stale chunks older than {STALE_RETENTION_YEARS} years")

    return len(old_ids)
