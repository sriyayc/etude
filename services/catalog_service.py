"""Catalog service.

Bridges a freshly ingested slides/textbook PDF into the parts of the app
that don't read from Qdrant:

  - `subjects` / `slides` tables, which back the resources-browsing UI
    (subjects grid -> subject detail -> slide viewer).
  - `syllabus_topics`, which backs the unit picker on the quiz/flashcard/
    notes pages.

There's no separate machine-readable syllabus outline for a slides deck,
so the unit/module structure is inferred from the deck's own running
headers ("Module 5 - Energy storage devices") and the "Module content:" /
"Class content:" bullet-list overview slides that already exist in
typical university slide decks. This is best-effort, not exact.
"""

import re
from collections import Counter

from db import subjects_repo, syllabus_repo
from ingestion.extract import extract_pages

_ROMAN_NUMERALS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
}

# Matches a running header like "Module 5- Energy Storage devices- Batteries"
# or "Module VI- Electrochemical Sensors". Only the module number + the
# first title segment (before the next dash) are kept -- later dashes are
# usually a sub-topic breadcrumb, not part of the module's own name.
_MODULE_RE = re.compile(
    r"Module\s+([0-9]+|[IVX]+)\s*[-–:]?\s*([A-Za-z][^\n]{0,60})",
    re.IGNORECASE,
)

# Matches "Module content:" / "Class content:" overview slides and
# captures everything after the colon as the bullet list to parse.
_CONTENT_RE = re.compile(
    r"(?:Module|Class)\s+[Cc]ontent\s*:\s*(.*)",
    re.IGNORECASE | re.DOTALL,
)

_BULLET_SPLIT_RE = re.compile(r"[•▪]")


def sync_catalog(
    pdf_path: str,
    document_uuid: str,
    subject_name: str,
    semester: int,
) -> dict:
    """Sync one ingested PDF into subjects/slides/syllabus_topics.

    Safe to call again for the same document_uuid -- slides upsert on
    (document_id, slide_number), and subjects upsert on
    (semester, slug) -- where the slug is derived from subject_name.

    Returns:
        {"slides_created": int, "modules_detected": int, "topics_created": int}
    """
    pages = extract_pages(pdf_path)

    module_by_page, module_titles = _detect_modules(pages)

    slide_rows = [
        {
            "document_id": document_uuid,
            "slide_number": page["page_number"],
            "module_number": module_by_page.get(page["page_number"], 0),
            "title": _derive_slide_title(page["text"]),
            "content": page["text"].strip(),
        }
        for page in pages
    ]
    subjects_repo.bulk_upsert_slides(slide_rows)

    subjects_repo.upsert_subject(
        semester=semester,
        subject_name=subject_name,
        syllabus_status="current",
        slide_count=len(pages),
        page_count=len(pages),
        slides_document_id=document_uuid,
    )

    topics_created = _sync_syllabus_topics(
        pages=pages,
        module_by_page=module_by_page,
        module_titles=module_titles,
        document_id=document_uuid,
        subject=subjects_repo.slugify(subject_name),
        semester=semester,
    )

    return {
        "slides_created": len(slide_rows),
        "modules_detected": len(module_titles),
        "topics_created": topics_created,
    }


# ------------------------------------------------------------------ #
#  Module / unit detection                                            #
# ------------------------------------------------------------------ #

def _parse_module_number(raw: str) -> int | None:
    raw = raw.strip().upper()
    if raw.isdigit():
        return int(raw)
    return _ROMAN_NUMERALS.get(raw)


def _clean_module_title(raw: str) -> str:
    raw = raw.strip().strip("-–:").strip()
    # Drop anything after a further dash -- that's a sub-topic breadcrumb,
    # e.g. "Energy Storage devices- Batteries" -> "Energy Storage devices".
    raw = re.split(r"[–-]", raw)[0].strip()
    return re.sub(r"\s+", " ", raw)


def _detect_modules(
    pages: list[dict],
) -> tuple[dict[int, int], dict[int, str]]:
    """Detect (page_number -> module_number) and (module_number -> title).

    Running headers repeat on every slide, so a module header is only
    trusted once the same (number, title) pair has appeared on at least
    two pages -- this filters out one-off typos in the source deck
    (seen in practice: a single slide mislabelled with the wrong module
    name) without needing to hand-curate anything.
    """
    raw_matches: list[tuple[int, int, str]] = []
    for page in pages:
        match = _MODULE_RE.search(page["text"][:100])
        if not match:
            continue
        number = _parse_module_number(match.group(1))
        if number is not None:
            raw_matches.append(
                (page["page_number"], number, _clean_module_title(match.group(2)))
            )

    pair_counts = Counter(
        (number, title.lower()) for _, number, title in raw_matches
    )

    module_titles: dict[int, str] = {}
    for number, title_lower in pair_counts:
        if pair_counts[(number, title_lower)] < 2:
            continue
        if number in module_titles:
            continue
        display_title = next(
            title for _, n, title in raw_matches
            if n == number and title.lower() == title_lower
        )
        module_titles[number] = display_title

    # Only trust a page's match if its title matches the validated title
    # for that module number -- this is what excludes the one-off typo
    # page from being treated as a boundary in the pass below.
    validated_by_page = {
        page_num: number
        for page_num, number, title in raw_matches
        if module_titles.get(number, "").lower() == title.lower()
    }

    # Carry the last validated module forward onto pages that don't repeat
    # the header (e.g. mid-topic content slides), so every page still gets
    # tagged with a module_number.
    module_by_page: dict[int, int] = {}
    current_module = 0
    for page in pages:
        page_num = page["page_number"]
        if page_num in validated_by_page:
            current_module = validated_by_page[page_num]
        module_by_page[page_num] = current_module

    return module_by_page, module_titles


def _sync_syllabus_topics(
    pages: list[dict],
    module_by_page: dict[int, int],
    module_titles: dict[int, str],
    document_id: str,
    subject: str,
    semester: int,
) -> int:
    """Build unit/topic rows from "content:" overview slides and save them.

    Replaces any existing current topics for this subject/semester so
    re-syncing the same deck doesn't pile up duplicates.
    """
    if not module_titles:
        return 0

    topics_by_module: dict[int, list[str]] = {}

    for page in pages:
        content_match = _CONTENT_RE.search(page["text"])
        if not content_match:
            continue
        module_number = module_by_page.get(page["page_number"], 0)
        if module_number not in module_titles:
            continue

        bullets = _BULLET_SPLIT_RE.split(content_match.group(1))
        existing = topics_by_module.setdefault(module_number, [])
        for bullet in bullets:
            text = re.sub(r"\s+", " ", bullet.strip().strip(":").strip())
            if 2 < len(text) < 60 and text not in existing:
                existing.append(text)

    existing_current = syllabus_repo.list_current_topics(
        subject=subject, semester=semester
    )
    version = 1
    if existing_current:
        old_version = max(t["version"] for t in existing_current)
        syllabus_repo.mark_outdated(
            subject=subject, semester=semester, version=old_version
        )
        version = old_version + 1

    created = 0
    for module_number, topics in topics_by_module.items():
        unit_title = module_titles[module_number]
        for topic in topics:
            syllabus_repo.create_topic(
                document_id=document_id,
                subject=subject,
                semester=semester,
                unit_number=module_number,
                unit_title=unit_title,
                topic=topic,
                version=version,
                is_current=True,
            )
            created += 1

    return created


def _derive_slide_title(page_text: str) -> str:
    """Best-effort human title for a slide from its first meaningful line."""
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    for line in lines:
        if line.upper() == "ENGINEERING CHEMISTRY":
            continue
        if len(line) > 3:
            return line[:80]
    return "Untitled slide"
