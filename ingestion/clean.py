"""Remove running headers and footers from extracted page text.

A lecture deck repeats the same header/footer on nearly every slide -- the
course name, unit title, university branding, a slide/page number. That
boilerplate adds no meaning but pollutes the embeddings (every chunk looks a
bit like every other) and the grounding text. This strips it out.

Applied only to the text used for RAG / generation (embeddings and the
slides.content column). The raw PDF served to students is never touched, and
module detection runs on the raw pages -- it *keys off* those running headers.

Two removals, kept deliberately separate so neither over-reaches:

  * Recurring lines -- a line that appears *verbatim* on a large fraction of
    pages is boilerplate (course name, unit title, footer). Matching is exact
    (only case/whitespace normalized), so a content line that merely contains
    a number -- "Example 2", "Step 3: ..." -- is never mistaken for a header
    just because a sibling slide has "Example 3".

  * Page/slide numbers -- short lines that are essentially just a number
    ("5", "Page 5", "Slide 5", "5 / 20", "5 of 20"). These vary per page so
    they don't recur verbatim, so they get their own pattern.
"""

import re
from collections import Counter

_WS = re.compile(r"\s+")
_PAGE_NUM_RE = re.compile(r"^(?:page|slide|pg)?\s*\d+\s*(?:(?:/|of)\s*\d+)?$", re.IGNORECASE)

# Real headers/footers are short -- keeps a genuine recurring sentence intact.
_MAX_BOILERPLATE_LEN = 80
# Fraction of pages a line must recur on to count as boilerplate, with a floor
# so it still works on short decks.
_MIN_FRACTION = 0.6
_MIN_PAGES = 3


def _normalize(line: str) -> str:
    return _WS.sub(" ", line.strip().lower())


def _is_page_number(line: str) -> bool:
    return bool(_PAGE_NUM_RE.match(line.strip()))


def clean_pages(pages: list[dict]) -> list[dict]:
    """Return pages with recurring header/footer and page-number lines removed.

    Each page keeps its ``page_number``; only ``text`` is rewritten. Decks too
    short to judge recurrence still get page-number stripping.
    """
    boilerplate: set[str] = set()

    if len(pages) >= _MIN_PAGES:
        counts: Counter[str] = Counter()
        for page in pages:
            seen: set[str] = set()
            for raw in (page.get("text") or "").split("\n"):
                stripped = raw.strip()
                if not stripped or len(stripped) > _MAX_BOILERPLATE_LEN:
                    continue
                if _is_page_number(stripped):
                    continue  # handled separately; don't let it skew counts
                seen.add(_normalize(stripped))
            counts.update(seen)

        threshold = max(_MIN_PAGES, int(len(pages) * _MIN_FRACTION))
        boilerplate = {norm for norm, n in counts.items() if n >= threshold}

    cleaned: list[dict] = []
    for page in pages:
        kept = []
        for raw in (page.get("text") or "").split("\n"):
            stripped = raw.strip()
            if not stripped:
                kept.append(raw)
                continue
            if _is_page_number(stripped):
                continue
            if (
                len(stripped) <= _MAX_BOILERPLATE_LEN
                and _normalize(stripped) in boilerplate
            ):
                continue
            kept.append(raw)
        cleaned.append({**page, "text": "\n".join(kept).strip()})

    return cleaned
