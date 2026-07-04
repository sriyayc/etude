"""
Shared retrieval pipeline.
Used by all features: qa, notes, quiz, flashcards, doubts.

Pipeline:
  query classification
      → query expansion (Groq generates related queries)
      → vector search with related_vectors (Qdrant)
      → optional reranking (cross-encoder, server only)
      → context expansion (N-1, N+1 neighbors)
      → return clean chunk list

To enable reranking on the server:
  1. Add sentence-transformers to requirements.txt
  2. Set USE_RERANKER = True here or via env var
"""

import time
import os
from providers.factory import get_embedder, get_vectorstore, get_llm

# ------------------------------------------------------------------ #
#  Feature flags                                                       #
# ------------------------------------------------------------------ #

USE_RERANKER = os.getenv("USE_RERANKER", "false").lower() == "true"
_reranker = None  # lazy-loaded only if USE_RERANKER is True


# ------------------------------------------------------------------ #
#  Public entry point                                                  #
# ------------------------------------------------------------------ #

def retrieve(
    query: str,
    subject: str = None,
    semester: int = None,
    expand_query: bool = True,
    expand_context: bool = True,
    score_threshold: float = 0.65,
) -> list[dict]:
    """
    Full retrieval pipeline from raw question to clean chunk list.

    Args:
        query:            Student's question.
        subject:          Optional subject filter e.g. "Computer Networks".
                          Scopes search to one subject, all units within it.
        semester:         Optional semester filter e.g. 5.
        expand_query:     Generate related queries via LLM for broader coverage.
        expand_context:   Pull neighboring chunks (N-1, N+1) for each result.
        score_threshold:  Minimum similarity score. Chunks below this are
                          dropped. If nothing passes, returns [] which
                          triggers the fallback in qa.py.

    Returns:
        List of chunk dicts ready for prompt building:
        [
            {
                "chunk_text":   str,
                "source_file":  str,
                "page_number":  int,
                "document_id":  str,
                "chunk_index":  int,
                "subject":      str,
                "content_hash": str,
                "score":        float,
            },
            ...
        ]
        Returns [] if nothing relevant found — caller must handle fallback.
    """
    t_start = time.time()

    embedder = get_embedder()
    vectorstore = get_vectorstore(dimension=embedder.dimension)

    # Step 1 — Classify query to set n dynamically
    n, candidate_pool = _classify_query(query)
    _log(f"Query classified → n={n}, pool={candidate_pool}")

    # Step 2 — Build metadata filters
    filters = _build_filters(subject, semester)

    # Step 3 — Query expansion
    queries = [query]
    if expand_query:
        variants = _generate_query_variants(query)
        queries += variants
        _log(f"Query expanded → {len(queries)} total queries: {queries}")

    # Step 4 — Embed all queries
    all_texts = queries
    all_vectors = embedder.embed(all_texts, task="retrieval.query")
    query_vector = all_vectors[0]
    related_vectors = all_vectors[1:] if len(all_vectors) > 1 else None

    # Step 5 — Vector search with related query expansion
    raw_results = vectorstore.query(
        vector=query_vector,
        n=candidate_pool,
        filters=filters,
        score_threshold=score_threshold,
        related_vectors=related_vectors,
    )
    _log(f"Vector search → {len(raw_results)} candidates above threshold")

    if not raw_results:
        _log("No results above threshold — returning empty")
        return []

    # Step 6 — Rerank if enabled, otherwise trim to n
    if USE_RERANKER:
        raw_results = _rerank(query, raw_results, top_n=n)
        _log(f"Reranked → top {len(raw_results)} results")
    else:
        raw_results = raw_results[:n]

    # Step 7 — Format results
    chunks = [_format_result(r) for r in raw_results]

    # Step 8 — Context expansion
    if expand_context:
        chunks = _expand_context(chunks, raw_results, vectorstore, filters)
        _log(f"Context expanded → {len(chunks)} total chunks")

    # Step 9 — Deduplicate by content_hash (catches identical text
    # that may have been ingested under different chunk IDs)
    chunks = _deduplicate(chunks)
    _log(f"After dedup → {len(chunks)} chunks")

    _log(f"Total retrieval time: {time.time() - t_start:.2f}s")
    return chunks


# ------------------------------------------------------------------ #
#  Query classification                                               #
# ------------------------------------------------------------------ #

def _classify_query(query: str) -> tuple[int, int]:
    """
    Dynamically set n and candidate_pool based on query type.

    Broad queries (explain, compare, describe) → more chunks needed.
    Simple queries (define, what is, full form) → fewer chunks needed.

    Returns (n, candidate_pool) where candidate_pool > n to give
    reranker/trimming step more candidates to work with.
    """
    q = query.lower()

    broad_signals = [
        "explain", "describe", "how does", "how do", "compare",
        "difference between", "overview", "everything about",
        "all about", "what are", "types of", "advantages",
        "disadvantages", "applications of", "working of"
    ]
    simple_signals = [
        "what is", "define", "definition of", "full form",
        "stands for", "abbreviation", "when was", "who invented"
    ]

    if any(s in q for s in broad_signals):
        return 15, 30   # broad: retrieve 30, keep 15
    elif any(s in q for s in simple_signals):
        return 5, 15    # simple: retrieve 15, keep 5
    else:
        return 8, 20    # default middle ground


# ------------------------------------------------------------------ #
#  Filter builder                                                      #
# ------------------------------------------------------------------ #

def _build_filters(subject: str = None, semester: int = None) -> dict:
    """
    Always filter is_current=True to prevent stale content surfacing.
    Optionally scope to subject and/or semester.
    """
    filters = {"is_current": True}
    if subject:
        filters["subject"] = subject
    if semester:
        filters["semester"] = semester
    return filters


# ------------------------------------------------------------------ #
#  Query expansion                                                     #
# ------------------------------------------------------------------ #

def _generate_query_variants(query: str, n: int = 3) -> list[str]:
    """
    Use the LLM to generate related search queries for broader coverage.

    Generates:
    1. A rephrasing of the original question (catches paraphrased content)
    2. A closely related or commonly compared concept (e.g. TCP → UDP)
    3. A prerequisite or follow-up concept that provides fuller context

    Falls back to [] silently if LLM call fails — original query still runs.
    """
    llm = get_llm()
    prompt = f"""You are helping a search engine retrieve study material for a student.

Given the student's question below, generate exactly {n} short search queries (5-10 words each) that would help retrieve the most complete answer from a textbook. Include:
1. A rephrasing of the original question using different words
2. A closely related concept that is commonly compared or confused with the topic
3. A prerequisite or follow-up concept that gives fuller context

Return ONLY the {n} queries, one per line. No numbering. No explanation. No extra text.

Question: {query}"""

    try:
        response = llm.generate(prompt, max_tokens=120)
        variants = [
            line.strip()
            for line in response.strip().split("\n")
            if line.strip() and len(line.strip()) > 3
        ]
        return variants[:n]
    except Exception as e:
        _log(f"Query expansion failed ({e}) — proceeding with original query only")
        return []


# ------------------------------------------------------------------ #
#  Reranking                                                           #
# ------------------------------------------------------------------ #

def _rerank(query: str, results: list[dict], top_n: int) -> list[dict]:
    """
    Cross-encoder reranking — scores each (query, chunk) pair together
    rather than independently, giving more accurate relevance scoring
    than cosine similarity alone.

    Model: ms-marco-MiniLM-L-6-v2
    - Runs on CPU, no GPU needed
    - ~50ms on server hardware for 25 candidates
    - Zero API cost — runs on the deployment server
    - Requires sentence-transformers in requirements.txt

    Only active when USE_RERANKER=true env var is set.
    Lazy-loaded so teammates without torch can still import this file.
    """
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except ImportError:
            _log("sentence-transformers not installed — skipping rerank, returning top_n by score")
            return results[:top_n]

    pairs = [(query, r["payload"]["chunk_text"]) for r in results]
    scores = _reranker.predict(pairs)
    reranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [r for r, _ in reranked[:top_n]]


# ------------------------------------------------------------------ #
#  Result formatting                                                   #
# ------------------------------------------------------------------ #

def _format_result(result: dict) -> dict:
    """
    Extract exactly what downstream prompts need.
    Keeps content_hash for deduplication step.
    Score is 0.0 for neighbor chunks added during context expansion.
    """
    payload = result["payload"]
    return {
        "chunk_text":   payload["chunk_text"],
        "source_file":  payload["source_file"],
        "page_number":  payload["page_number"],
        "document_id":  payload["document_id"],
        "chunk_index":  payload["chunk_index"],
        "subject":      payload["subject"],
        "content_hash": payload["content_hash"],
        "score":        result["score"],
    }


# ------------------------------------------------------------------ #
#  Context expansion                                                   #
# ------------------------------------------------------------------ #

def _expand_context(
    chunks: list[dict],
    raw_results: list[dict],
    vectorstore,
    base_filters: dict,
) -> list[dict]:
    """
    For each retrieved chunk, also pull chunk_index-1 and chunk_index+1
    from the same document.

    This prevents answers from being generated off a chunk that starts
    or ends mid-explanation. The surrounding chunks provide the full
    sentence and paragraph context.

    Neighbor chunks get score=0.0 since they weren't similarity-matched —
    they're context support, not primary matches.
    """
    expanded = list(chunks)
    seen_keys = {(c["document_id"], c["chunk_index"]) for c in chunks}

    for result in raw_results:
        payload = result["payload"]
        doc_id = payload["document_id"]
        idx = payload["chunk_index"]

        for neighbor_idx in (idx - 1, idx + 1):
            key = (doc_id, neighbor_idx)
            if key in seen_keys or neighbor_idx < 0:
                continue

            neighbor_filters = {**base_filters, "document_id": doc_id}
            neighbors = vectorstore.fetch_by_filter(
                filters=neighbor_filters,
                limit=1000
            )
            match = next(
                (n for n in neighbors if n["payload"]["chunk_index"] == neighbor_idx),
                None,
            )
            if match:
                expanded.append(
                    _format_result({"payload": match["payload"], "score": 0.0})
                )
                seen_keys.add(key)

    return expanded


# ------------------------------------------------------------------ #
#  Deduplication                                                       #
# ------------------------------------------------------------------ #

def _deduplicate(chunks: list[dict]) -> list[dict]:
    """
    Remove duplicate chunks by content_hash.

    This catches identical text that was ingested under different chunk IDs
    (e.g. overlapping chunks from different PDF versions, or the same
    paragraph appearing in both slides and textbook).

    Keeps the first occurrence which has the highest score since chunks
    are already sorted by score at this point.
    """
    seen_hashes = set()
    unique = []
    for chunk in chunks:
        h = chunk["content_hash"]
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(chunk)
    return unique


# ------------------------------------------------------------------ #
#  Logging                                                             #
# ------------------------------------------------------------------ #

def _log(msg: str) -> None:
    """Simple timestamped log. Replace with proper logger in production."""
    print(f"[retriever] {msg}")
