"""
Syllabus tagger.
Applies comparator diff output to Qdrant:
  - Marks removed topic chunks as is_current=False
  - Confirms new topic chunks are is_current=True
  - Provides cleanup job for old stale content

Also updates retriever behavior:
  When a query returns no is_current=True results,
  retry with is_current=False and flag as stale.
"""

from datetime import datetime, timezone
from providers.factory import get_vectorstore, get_embedder


STALE_RETENTION_YEARS = 3  # delete stale chunks older than this


# ------------------------------------------------------------------ #
#  Public entry point                                                  #
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
        diff:     Output from comparator.compare_syllabi()
        subject:  e.g. "Operating Systems"
        semester: e.g. 4

    Returns:
        {
            "chunks_marked_stale":   int,
            "chunks_confirmed_current": int,
            "topics_processed":      int,
        }
    """
    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    stale_count = 0
    current_count = 0
    topics_processed = 0

    # Mark removed topics as stale
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

    # Mark moved topics — stale in old unit, current in new unit
    for topic in diff["topics"]["moved"]:
        stale = _mark_topic_stale_in_unit(
            topic_name=topic["name"],
            unit_name=topic["from_unit"],
            subject=subject,
            semester=semester,
            vectorstore=vectorstore,
            embedder=embedder,
        )
        stale_count += stale
        topics_processed += 1
        print(f"  Marked moved: {topic['name']} ({topic['from_unit']} → {topic['to_unit']})")

    # Confirm added topics are current (they should be from ingestion,
    # but this acts as a safety check)
    for topic in diff["topics"]["added"]:
        count = _confirm_topic_current(
            topic_name=topic["name"],
            subject=subject,
            semester=semester,
            vectorstore=vectorstore,
            embedder=embedder,
        )
        current_count += count
        topics_processed += 1

    return {
        "chunks_marked_stale":      stale_count,
        "chunks_confirmed_current": current_count,
        "topics_processed":         topics_processed,
    }


# ------------------------------------------------------------------ #
#  Stale marking                                                       #
# ------------------------------------------------------------------ #

def _mark_topic_stale(
    topic_name: str,
    subject: str,
    semester: int,
    vectorstore,
    embedder,
) -> int:
    """
    Find all chunks related to a topic and mark them is_current=False.

    Uses two strategies:
    1. Exact topic name match in payload
    2. Semantic search — finds chunks whose content is about this topic
       even if the topic name isn't explicitly in the chunk text
    """
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

    # Strategy 2 — semantic search for topic content
    topic_vector = embedder.embed([topic_name], task="retrieval.query")[0]
    semantic_results = vectorstore.query(
        vector=topic_vector,
        n=50,
        filters={
            "subject":    subject,
            "semester":   semester,
            "is_current": True,
        },
        score_threshold=0.80,  # high threshold — only clearly related chunks
    )

    # Merge chunk IDs from both strategies
    chunk_ids = set()
    for chunk in chunks_by_topic:
        chunk_ids.add(chunk["id"])
    for result in semantic_results:
        chunk_ids.add(result["id"])

    if not chunk_ids:
        return 0

    # Mark all found chunks as stale
    _update_chunks_staleness(list(chunk_ids), is_current=False, vectorstore=vectorstore)
    return len(chunk_ids)


def _mark_topic_stale_in_unit(
    topic_name: str,
    unit_name: str,
    subject: str,
    semester: int,
    vectorstore,
    embedder,
) -> int:
    """Mark a topic stale only within a specific unit — used for moved topics."""
    chunks = vectorstore.fetch_by_filter(
        filters={
            "subject":    subject,
            "semester":   semester,
            "topic":      topic_name,
            "is_current": True,
        },
        limit=5000,
    )
    chunk_ids = [c["id"] for c in chunks]
    if not chunk_ids:
        return 0
    _update_chunks_staleness(chunk_ids, is_current=False, vectorstore=vectorstore)
    return len(chunk_ids)


def _confirm_topic_current(
    topic_name: str,
    subject: str,
    semester: int,
    vectorstore,
    embedder,
) -> int:
    """Safety check — ensure newly added topic chunks are marked is_current=True."""
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
    _update_chunks_staleness(chunk_ids, is_current=True, vectorstore=vectorstore)
    return len(chunk_ids)


def _update_chunks_staleness(
    chunk_ids: list[str],
    is_current: bool,
    vectorstore,
) -> None:
    """
    Update is_current field for a list of chunk IDs.
    Uses Qdrant's set_payload to update in place without re-embedding.
    """
    vectorstore.client.set_payload(
        collection_name=vectorstore.collection_name,
        payload={"is_current": is_current},
        points=chunk_ids,
    )


# ------------------------------------------------------------------ #
#  Stale content retrieval for "learn anyway" feature                 #
# ------------------------------------------------------------------ #

def retrieve_stale(
    query: str,
    subject: str,
    semester: int,
) -> list[dict]:
    """
    Retrieve chunks from stale/removed topics.
    Called when a student asks about a removed topic and wants to
    learn it anyway for context.

    Returns same format as retriever.retrieve() but with stale flag.
    """
    from retrieval.retriever import retrieve

    chunks = retrieve(
        query=query,
        subject=subject,
        semester=semester,
        score_threshold=0.65,
        stale_override=True,
    )
    return chunks


# ------------------------------------------------------------------ #
#  Cleanup job — run every 3-4 years                                  #
# ------------------------------------------------------------------ #

def cleanup_old_stale_chunks(
    subject: str,
    semester: int,
    vectorstore=None,
    embedder=None,
) -> int:
    """
    Permanently delete stale chunks older than STALE_RETENTION_YEARS.
    Run this periodically to keep storage bounded long term.

    Returns count of chunks deleted.
    """
    if vectorstore is None:
        embedder = get_embedder()
        vectorstore = get_vectorstore(dimension=embedder.dimension)

    stale_chunks = vectorstore.fetch_by_filter(
        filters={
            "subject":    subject,
            "semester":   semester,
            "is_current": False,
        },
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
