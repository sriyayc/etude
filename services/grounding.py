"""Build generation grounding from an uploaded deck's own slides.

Quiz / flashcard / notes generation used to ground on a semantic search of the
unit *title*. That only worked for decks whose slides contained the
"Module content:" overview format (which produced ``syllabus_topics``). Most
uploaded decks don't, and a title like "unit_2" makes a useless search query —
so nothing generated at all.

Each uploaded deck *is* a unit, and every deck has its extracted slide text in
the ``slides`` table. So ground generation directly on that deck's slides,
sampled evenly across the deck and capped to a sane context budget.
"""

from db import subjects_repo

_MAX_CHUNKS = 24
_MAX_CHARS_PER_SLIDE = 1200
_MAX_TOTAL_CHARS = 18000


def deck_chunks(document_id: str, source_file: str) -> list[dict]:
    """Return grounding chunks for one deck, in the shape the prompts expect.

    Empty list means "no usable slide text" — callers should fall back to the
    subject-wide retrieval path rather than failing outright.
    """
    try:
        rows = subjects_repo.list_slides(document_id=str(document_id))
    except Exception:
        return []

    slides = [r for r in rows if (r.get("content") or "").strip()]
    if not slides:
        return []

    # Sample evenly so a long deck's grounding still spans the whole unit
    # instead of only its opening slides.
    if len(slides) > _MAX_CHUNKS:
        step = len(slides) / _MAX_CHUNKS
        slides = [slides[int(i * step)] for i in range(_MAX_CHUNKS)]

    chunks: list[dict] = []
    total = 0
    for r in slides:
        text = (r.get("content") or "").strip()[:_MAX_CHARS_PER_SLIDE]
        if not text:
            continue
        if total + len(text) > _MAX_TOTAL_CHARS:
            break
        total += len(text)
        chunks.append(
            {
                "chunk_text": text,
                "source_file": source_file,
                "page_number": r.get("slide_number") or 0,
            }
        )
    return chunks
