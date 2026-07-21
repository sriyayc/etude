"""
One-off data population script: ingest the CS 2024-curriculum syllabus text
(data/syllabus/UG_CSE_2024_Curriculum_and_Syllabi.txt) into the `subjects`
and `syllabus_topics` tables for Semesters 1-6, using the app's EXISTING
syllabus ingestion pipeline (services/syllabus_service.upload_and_process_syllabus).

This script does not modify any application code -- it only calls existing
service functions with generated per-subject syllabus PDFs.

Usage:
    python scripts/ingest_cse_syllabi.py
"""

import os
import re
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz

from services.auth_service import login
from services.syllabus_service import upload_and_process_syllabus
from db.subjects_repo import upsert_subject

SOURCE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "syllabus", "UG_CSE_2024_Curriculum_and_Syllabi.txt",
)

ADMIN_SRN = "PES2UG24CS523"
ADMIN_PASSWORD = "TeacherDemo2026!"

MAX_RETRIES = 2
RETRY_BACKOFF_SECS = 15
INTER_SUBJECT_DELAY_SECS = 2


# ------------------------------------------------------------------ #
#  Parsing the source text file                                       #
# ------------------------------------------------------------------ #

def parse_course_list(text: str) -> list[dict]:
    """Part 1: semester-by-semester course list. Returns list of
    {code, name, semester}, skipping Sem VII/VIII and audit/bridge courses."""

    roman_to_int = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    }

    # Only look at part 1 -- stop at the detailed-content divider.
    divider_idx = text.find('DETAILED "Course Content"')
    part1 = text[:divider_idx] if divider_idx != -1 else text

    lines = part1.splitlines()
    current_sem = None
    courses = []

    sem_header_re = re.compile(r"===\s*([IVX]+)\s+SEMESTER", re.IGNORECASE)
    course_line_re = re.compile(r"^(UE\S+)\s*-\s*(.+?)\s*\(([^()]*)\)\s*$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        sem_match = sem_header_re.search(line)
        if sem_match:
            current_sem = roman_to_int.get(sem_match.group(1).upper())
            continue

        if current_sem is None or current_sem > 6:
            continue

        # Skip section labels like "Core:", "Elective I (choose 1):"
        if line.endswith(":") and not course_line_re.match(line):
            continue

        m = course_line_re.match(line)
        if not m:
            continue

        code, name, meta = m.group(1), m.group(2).strip(), m.group(3)

        # Skip audit/bridge courses -- no fixed unit syllabus, not real
        # CS core/elective content.
        if "audit" in meta.lower() or "bridge course" in name.lower():
            continue

        courses.append({"code": code, "name": name, "semester": current_sem})

    return courses


def parse_detailed_content(text: str) -> dict[str, str]:
    """Part 2: per-subject 'Course Content' blocks, verbatim (incl. 'Unit N:'
    headers). Returns {subject_code: content_block_text}."""

    divider_idx = text.find('DETAILED "Course Content"')
    part2 = text[divider_idx:] if divider_idx != -1 else ""

    # Blocks are delimited by lines of dashes; each block starts with a
    # header line "CODE: Title (...)" or "CODE - Title (...)".
    blocks = re.split(r"-{10,}\s*\n", part2)

    header_re = re.compile(r"^(UE\S+)\s*[:\-]\s*(.+)$")
    content: dict[str, str] = {}

    i = 0
    while i < len(blocks):
        block = blocks[i].strip()
        m = header_re.match(block) if block else None
        if m:
            code = m.group(1).strip()
            # The body (Course Content + Units) is the *next* block, since
            # blocks alternate: [header][body][header][body]...
            body = blocks[i + 1].strip() if i + 1 < len(blocks) else ""
            if code not in content and body:
                content[code] = body
        i += 1

    return content


def normalize_unit_headers(text: str) -> str:
    """The pipeline's regex requires 'Unit' + whitespace + number + ':'
    ('Unit\\s+\\d+\\s*:'). Source uses several inconsistent variants --
    'Unit1:' (no space), 'Unit-1:' (dash before number), 'Unit 1- Title'
    and 'Unit 2 - Title' (dash instead of colon after the number).
    Normalize all of them to 'Unit N: ' so every unit is detected."""
    return re.sub(r"\bUnit[\s\-]*(\d+)\s*[\-:]\s*", r"Unit \1: ", text)


# ------------------------------------------------------------------ #
#  PDF generation                                                     #
# ------------------------------------------------------------------ #

def build_syllabus_pdf(subject_code: str, subject_name: str, content_block: str, out_path: str) -> None:
    """Build a simple text-extractable PDF containing the subject name and
    its verbatim Course Content block (with 'Unit N:' headers preserved).

    Places text manually line-by-line (word-wrapped) and paginates when a
    page fills up -- avoids insert_textbox's leftover-text quirks, and
    keeps the PDF trivially re-extractable by PyMuPDF downstream.
    """
    import textwrap

    full_text = f"{subject_code}: {subject_name}\n\n{content_block}"

    doc = fitz.open()
    page_rect = fitz.paper_rect("a4")
    margin = 36
    fontsize = 10
    line_height = fontsize * 1.4
    wrap_width = 95  # chars per line, conservative for helv @10pt on A4

    top_y = margin + fontsize
    bottom_y = page_rect.height - margin

    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    y = top_y

    for raw_line in full_text.split("\n"):
        raw_line = raw_line.rstrip()
        wrapped = textwrap.wrap(raw_line, width=wrap_width) or [""]
        for line in wrapped:
            if y > bottom_y:
                page = doc.new_page(width=page_rect.width, height=page_rect.height)
                y = top_y
            page.insert_text((margin, y), line, fontsize=fontsize, fontname="helv")
            y += line_height

    doc.save(out_path)
    doc.close()


# ------------------------------------------------------------------ #
#  Main ingestion run                                                 #
# ------------------------------------------------------------------ #

def main():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    courses = parse_course_list(text)
    detailed = parse_detailed_content(text)

    print(f"Parsed {len(courses)} courses (Sem 1-6) from course list.")
    print(f"Parsed {len(detailed)} detailed content blocks.")

    missing = [c["code"] for c in courses if c["code"] not in detailed]
    if missing:
        print(f"WARNING: {len(missing)} courses have no detailed content block: {missing}")

    print("\nLogging in as admin...")
    login(srn=ADMIN_SRN, password=ADMIN_PASSWORD)
    print("Login OK.\n")

    # PyMuPDF stamps a creation-date in the PDF, so byte-identical content
    # still produces a different content_hash across runs -- upload_document's
    # hash-based dedup then misses, and it tries to upload to the same
    # storage_path again, which 409s. A per-run suffix on the filename
    # avoids colliding with any file left behind by a previous (e.g. killed
    # mid-run) attempt.
    run_id = str(int(time.time()))

    results = []
    tmp_dir = tempfile.mkdtemp(prefix="syllabus_ingest_")

    for idx, course in enumerate(courses, 1):
        code = course["code"]
        name = course["name"]
        semester = course["semester"]

        print(f"[{idx}/{len(courses)}] {code} (Sem {semester}) - {name}")

        content_block = detailed.get(code)
        if not content_block:
            print("  SKIP: no detailed content block found in source file.")
            results.append({
                "code": code, "semester": semester, "success": False,
                "topics_count": 0, "error": "no detailed content block in source file",
            })
            continue

        content_block = normalize_unit_headers(content_block)

        try:
            upsert_subject(semester=semester, subject_code=code, subject_name=name)
        except Exception as e:
            print(f"  FAIL (upsert_subject): {e}")
            results.append({
                "code": code, "semester": semester, "success": False,
                "topics_count": 0, "error": f"upsert_subject: {e}",
            })
            continue

        pdf_path = os.path.join(tmp_dir, f"{code}_syllabus_{run_id}.pdf")
        try:
            build_syllabus_pdf(code, name, content_block, pdf_path)
        except Exception as e:
            print(f"  FAIL (build_pdf): {e}")
            results.append({
                "code": code, "semester": semester, "success": False,
                "topics_count": 0, "error": f"build_pdf: {e}",
            })
            continue

        last_error = None
        success = False
        topics_count = 0

        for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES retries
            try:
                res = upload_and_process_syllabus(
                    file_path=pdf_path, subject=code, semester=semester,
                )
                if res.get("success"):
                    success = True
                    topics_count = res.get("topics_count", 0)
                    print(f"  OK: {topics_count} topics (version {res.get('version')})")
                    break
                else:
                    last_error = res.get("message", "unknown failure")
                    print(f"  attempt {attempt} failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                print(f"  attempt {attempt} raised: {last_error}")

            if attempt <= MAX_RETRIES:
                print(f"  retrying in {RETRY_BACKOFF_SECS}s...")
                time.sleep(RETRY_BACKOFF_SECS)

        results.append({
            "code": code, "semester": semester, "success": success,
            "topics_count": topics_count, "error": None if success else last_error,
        })

        try:
            os.remove(pdf_path)
        except OSError:
            pass

        time.sleep(INTER_SUBJECT_DELAY_SECS)

    # ------------------------------------------------------------ #
    #  Summary                                                      #
    # ------------------------------------------------------------ #
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = len(results)
    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    total_topics = sum(r["topics_count"] for r in results)

    by_sem: dict[int, list[dict]] = {}
    for r in results:
        by_sem.setdefault(r["semester"], []).append(r)

    for sem in sorted(by_sem):
        sem_results = by_sem[sem]
        ok = sum(1 for r in sem_results if r["success"])
        print(f"  Sem {sem}: {ok}/{len(sem_results)}")

    print(f"\nTotal: {len(succeeded)}/{total} succeeded, {len(failed)} failed")
    print(f"Total topics_count across all subjects: {total_topics}")

    if failed:
        print("\nFailures:")
        for r in failed:
            print(f"  - {r['code']} (Sem {r['semester']}): {r['error']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
