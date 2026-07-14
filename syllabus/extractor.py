"""
Syllabus extractor.
Converts a syllabus PDF into a structured JSON topic tree with embeddings,
AND saves topics to the Supabase syllabus_topics table for version tracking.

Two outputs from one run:
  1. Rich JSON with embeddings attached — used by comparator.py for 3-pass diff
  2. Supabase rows in syllabus_topics — used for version querying and tagging

Approach:
  1. Extract raw text from PDF using PyMuPDF
  2. Split into unit sections using regex (reliable for Indian university format)
  3. Send each unit to Groq separately for topic hierarchy extraction
  4. Embed every node (unit, topic, subtopic) for comparison later
  5. Save flattened topics to Supabase with version tracking
  6. Return full structured JSON with embeddings
"""

import re
import json
import logging
from datetime import datetime, timezone

import fitz

from providers.factory import get_llm, get_embedder
from db.syllabus_repo import create_topic, list_current_topics, mark_outdated

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Public entry point                                                  #
# ------------------------------------------------------------------ #

def extract_syllabus(
    pdf_path: str,
    document_id: str,
    subject: str,
    semester: int,
    academic_year: str = None,
    version: int = 1,
) -> dict:
    """
    Extract structured syllabus from PDF.
    Saves topics to Supabase AND returns rich JSON with embeddings.

    Args:
        pdf_path:      Path to syllabus PDF
        document_id:   Document UUID from documents table
        subject:       e.g. "Operating Systems"
        semester:      e.g. 4
        academic_year: e.g. "2024-25" (optional, inferred if not given)
        version:       Starting version number (auto-incremented if prior version exists)

    Returns:
        {
            "success":       bool,
            "message":       str,
            "topics_count":  int,
            "version":       int,
            "academic_year": str,
            "syllabus_json": dict,  # rich JSON with embeddings for comparator
        }
    """
    print(f"Extracting syllabus: {pdf_path}")

    raw_text = _extract_text(pdf_path)
    if not raw_text.strip():
        return {
            "success": False,
            "message": "Syllabus PDF is empty or text could not be extracted.",
            "topics_count": 0,
            "syllabus_json": None,
        }

    unit_sections = _split_by_units(raw_text)
    if not unit_sections:
        return {
            "success": False,
            "message": (
                f"No unit sections found in {pdf_path}. "
                f"Check that the PDF contains 'Unit N:' headers."
            ),
            "topics_count": 0,
            "syllabus_json": None,
        }

    print(f"Found {len(unit_sections)} units")

    # Handle versioning — mark previous version outdated
    current_topics = list_current_topics(subject=subject, semester=semester)
    if current_topics:
        old_version = max(t["version"] for t in current_topics)
        mark_outdated(subject=subject, semester=semester, version=old_version)
        version = old_version + 1
        print(f"Marked version {old_version} as outdated. New version: {version}")

    if academic_year is None:
        year = datetime.now().year
        academic_year = f"{year}-{str(year + 1)[2:]}"

    llm = get_llm()
    embedder = get_embedder()
    units = []
    topics_count = 0

    for unit_num, unit_name, unit_text in unit_sections:
        print(f"  Extracting Unit {unit_num}: {unit_name}")

        topics = _extract_unit_topics(unit_text, unit_name, llm)
        topics = _embed_topics(topics, embedder)
        unit_embedding = _embed_text(unit_name, embedder)

        # Save flattened topics to Supabase
        flat_topics = _flatten_for_db(topics)
        for topic_text in flat_topics:
            try:
                create_topic(
                    document_id=document_id,
                    subject=subject,
                    semester=semester,
                    unit_number=unit_num,
                    unit_title=unit_name,
                    topic=topic_text,
                    version=version,
                    is_current=True,
                )
                topics_count += 1
            except Exception as e:
                logger.error(f"Failed to save topic '{topic_text}': {e}")

        units.append({
            "unit":      unit_num,
            "unit_name": unit_name,
            "embedding": unit_embedding,
            "topics":    topics,
        })

    syllabus_json = {
        "subject":       subject,
        "semester":      semester,
        "academic_year": academic_year,
        "extracted_at":  datetime.now(timezone.utc).isoformat(),
        "units":         units,
    }

    print(f"Extraction complete: {topics_count} topics saved, {_count_nodes(syllabus_json)} total nodes")

    return {
        "success":       True,
        "message":       f"Successfully extracted and saved {topics_count} topics.",
        "topics_count":  topics_count,
        "version":       version,
        "academic_year": academic_year,
        "syllabus_json": syllabus_json,
    }


# ------------------------------------------------------------------ #
#  PDF text extraction                                                 #
# ------------------------------------------------------------------ #

def _extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n".join(pages)


# ------------------------------------------------------------------ #
#  Unit splitting                                                      #
# ------------------------------------------------------------------ #

def _split_by_units(text: str) -> list[tuple[int, str, str]]:
    """
    Split syllabus text into unit sections.
    Handles 'Unit 1:' and 'Unit 1 :' (space before colon).
    Returns list of (unit_number, unit_name, unit_text).
    """
    pattern = r'(?=Unit\s+\d+\s*:)'
    sections = re.split(pattern, text, flags=re.IGNORECASE)
    sections = [s.strip() for s in sections if s.strip()]

    header_pattern = r'Unit\s+(\d+)\s*:\s*([^\n]+)'
    result = []

    for section in sections:
        match = re.match(header_pattern, section, re.IGNORECASE)
        if not match:
            continue
        unit_num = int(match.group(1))
        unit_name = match.group(2).strip()
        result.append((unit_num, unit_name, section))

    return sorted(result, key=lambda x: x[0])


# ------------------------------------------------------------------ #
#  LLM-based topic extraction per unit                                #
# ------------------------------------------------------------------ #

def _extract_unit_topics(unit_text: str, unit_name: str, llm) -> list[dict]:
    """
    Send one unit's text to the LLM and extract a structured topic hierarchy.
    Returns a list of topic dicts with nested subtopics up to 4 levels deep.
    """
    prompt = f"""You are extracting the topic hierarchy from one unit of a university syllabus.

UNIT: {unit_name}
SYLLABUS TEXT:
{unit_text}

Extract ALL topics and subtopics from this unit into a JSON structure.
Follow these rules strictly:

1. A TOPIC is a major concept, algorithm, data structure, system component, or named technique.
   Examples: "CPU Scheduling", "Semaphores", "Page Replacement Algorithms"

2. A SUBTOPIC is something listed under a topic — usually after a colon, dash, or comma separation.
   Examples: Under "CPU Scheduling" → "FIFO", "Round Robin", "Priority Scheduling"

3. Detect parent-child relationships using these signals:
   - Colon pattern: "Shell programming: variables, control flow" → variables and control flow are children
   - Dash pattern: "Page Replacement Algorithms-FIFO, LRU, Optimal" → FIFO, LRU, Optimal are children
   - Capitalized term followed by lowercase items → lowercase items are children
   - Named algorithm/problem lists → always children of the concept before them
   - System call groupings → e.g. "fork(), vfork(), wait()" are children of "system calls for process management"

4. Go up to 4 levels deep if the content warrants it. Do not invent depth that isn't there.
   If a topic has no subtopics, set subtopics to [].

5. Preserve exact technical names. Do not paraphrase, simplify, or rename anything.

6. Do not include the unit header itself as a topic.

Return ONLY valid JSON in this exact format, nothing else:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "subtopics": [
        {{
          "name": "Subtopic Name",
          "subtopics": []
        }}
      ]
    }}
  ]
}}"""

    try:
        response = llm.generate(prompt, max_tokens=2000)
        cleaned = _clean_json_response(response)
        parsed = json.loads(cleaned)
        topics = parsed.get("topics", [])
        return _validate_topics(topics)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"LLM returned invalid JSON for unit '{unit_name}': {e}. Using fallback.")
        return _fallback_topic_extraction(unit_text)


def _clean_json_response(response: str) -> str:
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        response = "\n".join(lines)
    return response.strip()


def _validate_topics(topics: list) -> list[dict]:
    def validate_node(node: dict, depth: int) -> dict | None:
        if not isinstance(node, dict):
            return None
        name = node.get("name", "").strip()
        if not name:
            return None
        subtopics = []
        if depth < 4:
            for child in node.get("subtopics", []):
                validated = validate_node(child, depth + 1)
                if validated:
                    subtopics.append(validated)
        return {"name": name, "subtopics": subtopics, "embedding": None}

    result = []
    for topic in topics:
        validated = validate_node(topic, depth=1)
        if validated:
            result.append(validated)
    return result


def _fallback_topic_extraction(unit_text: str) -> list[dict]:
    pattern = r'\b([A-Z][a-zA-Z\s\-\/]{3,40})\b'
    matches = re.findall(pattern, unit_text)
    seen = set()
    topics = []
    for match in matches:
        name = match.strip()
        if name not in seen and len(name) > 3:
            seen.add(name)
            topics.append({"name": name, "subtopics": [], "embedding": None})
    return topics[:30]


# ------------------------------------------------------------------ #
#  Embedding                                                           #
# ------------------------------------------------------------------ #

def _embed_text(text: str, embedder) -> list[float]:
    return embedder.embed([text], task="retrieval.passage")[0]


def _embed_topics(topics: list[dict], embedder) -> list[dict]:
    def collect_nodes(nodes: list[dict]) -> list[dict]:
        all_nodes = []
        for node in nodes:
            all_nodes.append(node)
            if node.get("subtopics"):
                all_nodes.extend(collect_nodes(node["subtopics"]))
        return all_nodes

    all_nodes = collect_nodes(topics)
    if not all_nodes:
        return topics

    texts = [node["name"] for node in all_nodes]
    embeddings = embedder.embed(texts, task="retrieval.passage")

    for node, embedding in zip(all_nodes, embeddings):
        node["embedding"] = embedding

    return topics


# ------------------------------------------------------------------ #
#  Utilities                                                           #
# ------------------------------------------------------------------ #

def _flatten_for_db(topics: list[dict], parent: str = None) -> list[str]:
    """
    Flatten topic tree into a list of strings for DB storage.
    Includes all levels — unit-level topics and all subtopics.
    """
    flat = []
    for t in topics:
        flat.append(t["name"])
        if t.get("subtopics"):
            flat.extend(_flatten_for_db(t["subtopics"], t["name"]))
    return flat


def _count_nodes(syllabus: dict) -> int:
    count = 0
    def recurse(topics):
        nonlocal count
        for t in topics:
            count += 1
            if t.get("subtopics"):
                recurse(t["subtopics"])
    for unit in syllabus["units"]:
        count += 1
        recurse(unit["topics"])
    return count


def save_syllabus_json(syllabus: dict, path: str) -> None:
    """Save the rich JSON to disk for later comparison."""
    import json as json_module
    with open(path, "w") as f:
        json_module.dump(syllabus, f, indent=2)
    print(f"Saved syllabus JSON to {path}")


def load_syllabus_json(path: str) -> dict:
    """Load a previously saved syllabus JSON."""
    import json as json_module
    with open(path) as f:
        return json_module.load(f)
