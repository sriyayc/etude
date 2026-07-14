"""
Syllabus comparator.
Two comparison modes:

Mode 1 — Rich 3-pass comparison (for the syllabus differentiator feature):
  compare_syllabi_json(old_json, new_json) → full diff with embeddings
  Pass 1: Unit-level comparison using embeddings
  Pass 2: Recursive topic-level comparison at all 4 levels
  Pass 3: Cross-unit moved topic detection

Mode 2 — Simple DB comparison (for quick version diffs):
  compare_syllabi(subject, semester, v1, v2) → added/removed/unchanged sets
  Used by syllabus_service.get_syllabus_diff()
"""

import math
import logging
from db.syllabus_repo import list_topics_by_version

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85
MOVED_THRESHOLD = 0.85


# ------------------------------------------------------------------ #
#  Mode 1 — Rich 3-pass comparison                                    #
# ------------------------------------------------------------------ #

def compare_syllabi_json(old: dict, new: dict) -> dict:
    """
    Compare two rich syllabus JSON dicts produced by extractor.extract_syllabus().
    Requires embeddings to be present on all nodes.

    Returns full structured diff with added/removed/moved/renamed at every level.
    """
    print(f"Comparing syllabi: {old['academic_year']} vs {new['academic_year']}")

    print("Pass 1: Unit-level comparison")
    unit_diff = _pass1_unit_comparison(old, new)

    print("Pass 2: Topic-level recursive comparison")
    topic_diff = _pass2_topic_comparison(old, new, unit_diff)

    print("Pass 3: Cross-unit moved topic detection")
    topic_diff = _pass3_moved_detection(topic_diff, old, new)

    result = {
        "subject":  old["subject"],
        "old_year": old["academic_year"],
        "new_year": new["academic_year"],
        "units":    unit_diff,
        "topics":   topic_diff,
        "summary": {
            "total_added":   len(topic_diff["added"]),
            "total_removed": len(topic_diff["removed"]),
            "total_moved":   len(topic_diff["moved"]),
            "total_renamed": len(topic_diff["renamed"]),
        }
    }

    _print_summary(result)
    return result


# ------------------------------------------------------------------ #
#  Mode 2 — Simple DB comparison                                      #
# ------------------------------------------------------------------ #

def compare_syllabi(
    subject: str,
    semester: int,
    v1: int,
    v2: int,
) -> dict:
    """
    Compare two syllabus versions stored in Supabase.
    Fast set-based comparison — no embeddings needed.
    Used by syllabus_service.get_syllabus_diff().
    """
    topics_v1 = list_topics_by_version(subject=subject, semester=semester, version=v1)
    topics_v2 = list_topics_by_version(subject=subject, semester=semester, version=v2)

    set_v1 = {t["topic"] for t in topics_v1}
    set_v2 = {t["topic"] for t in topics_v2}

    added = sorted(list(set_v2 - set_v1))
    removed = sorted(list(set_v1 - set_v2))
    unchanged = sorted(list(set_v1 & set_v2))

    return {
        "added":     added,
        "removed":   removed,
        "unchanged": unchanged,
        "v1_count":  len(set_v1),
        "v2_count":  len(set_v2),
    }


# ------------------------------------------------------------------ #
#  Pass 1 — Unit level                                                #
# ------------------------------------------------------------------ #

def _pass1_unit_comparison(old: dict, new: dict) -> dict:
    old_units = {u["unit"]: u for u in old["units"]}
    new_units = {u["unit"]: u for u in new["units"]}

    added = []
    removed = []
    unchanged = []
    renamed = []

    old_nums = set(old_units.keys())
    new_nums = set(new_units.keys())

    for num in old_nums & new_nums:
        old_unit = old_units[num]
        new_unit = new_units[num]
        sim = _cosine_similarity(old_unit["embedding"], new_unit["embedding"])
        if sim >= SIMILARITY_THRESHOLD:
            unchanged.append(old_unit["unit_name"])
        else:
            renamed.append({
                "unit_number": num,
                "old_name":    old_unit["unit_name"],
                "new_name":    new_unit["unit_name"],
                "similarity":  round(sim, 3),
            })
            unchanged.append(old_unit["unit_name"])

    for num in old_nums - new_nums:
        removed.append(old_units[num]["unit_name"])

    for num in new_nums - old_nums:
        added.append(new_units[num]["unit_name"])

    return {
        "added":     added,
        "removed":   removed,
        "unchanged": unchanged,
        "renamed":   renamed,
    }


# ------------------------------------------------------------------ #
#  Pass 2 — Recursive topic comparison                                #
# ------------------------------------------------------------------ #

def _pass2_topic_comparison(old: dict, new: dict, unit_diff: dict) -> dict:
    added = []
    removed = []
    renamed = []

    old_units = {u["unit"]: u for u in old["units"]}
    new_units = {u["unit"]: u for u in new["units"]}

    shared = set(old_units.keys()) & set(new_units.keys())

    for num in shared:
        old_unit = old_units[num]
        new_unit = new_units[num]
        unit_path = f"Unit {num}: {old_unit['unit_name']}"

        u_added, u_removed, u_renamed = _diff_topic_lists(
            old_topics=old_unit["topics"],
            new_topics=new_unit["topics"],
            parent_path=unit_path,
            unit_name=old_unit["unit_name"],
            depth=1,
        )
        added.extend(u_added)
        removed.extend(u_removed)
        renamed.extend(u_renamed)

    for num in set(old_units.keys()) - set(new_units.keys()):
        unit = old_units[num]
        unit_path = f"Unit {num}: {unit['unit_name']}"
        for node in _flatten_topics(unit["topics"], unit_path):
            removed.append({
                "path":  node["path"],
                "name":  node["name"],
                "unit":  unit["unit_name"],
                "level": node["level"],
            })

    for num in set(new_units.keys()) - set(old_units.keys()):
        unit = new_units[num]
        unit_path = f"Unit {num}: {unit['unit_name']}"
        for node in _flatten_topics(unit["topics"], unit_path):
            added.append({
                "path":  node["path"],
                "name":  node["name"],
                "unit":  unit["unit_name"],
                "level": node["level"],
            })

    return {
        "added":   added,
        "removed": removed,
        "moved":   [],
        "renamed": renamed,
    }


def _diff_topic_lists(
    old_topics: list[dict],
    new_topics: list[dict],
    parent_path: str,
    unit_name: str,
    depth: int,
) -> tuple[list, list, list]:
    added = []
    removed = []
    renamed = []

    if depth > 4:
        return added, removed, renamed

    old_matched = set()
    new_matched = set()

    matches = []
    for i, old_t in enumerate(old_topics):
        for j, new_t in enumerate(new_topics):
            sim = _cosine_similarity(old_t.get("embedding"), new_t.get("embedding"))
            if sim >= SIMILARITY_THRESHOLD:
                matches.append((sim, i, j))

    matches.sort(reverse=True)

    for sim, i, j in matches:
        if i in old_matched or j in new_matched:
            continue
        old_matched.add(i)
        new_matched.add(j)

        old_t = old_topics[i]
        new_t = new_topics[j]
        old_path = f"{parent_path} > {old_t['name']}"

        if old_t["name"].strip().lower() != new_t["name"].strip().lower():
            renamed.append({
                "old_name":   old_t["name"],
                "new_name":   new_t["name"],
                "unit":       unit_name,
                "path":       old_path,
                "similarity": round(sim, 3),
                "level":      depth,
            })

        if old_t.get("subtopics") or new_t.get("subtopics"):
            s_added, s_removed, s_renamed = _diff_topic_lists(
                old_topics=old_t.get("subtopics", []),
                new_topics=new_t.get("subtopics", []),
                parent_path=old_path,
                unit_name=unit_name,
                depth=depth + 1,
            )
            added.extend(s_added)
            removed.extend(s_removed)
            renamed.extend(s_renamed)

    for i, old_t in enumerate(old_topics):
        if i not in old_matched:
            old_path = f"{parent_path} > {old_t['name']}"
            removed.append({
                "path":  old_path,
                "name":  old_t["name"],
                "unit":  unit_name,
                "level": depth,
            })
            if old_t.get("subtopics"):
                for node in _flatten_topics(old_t["subtopics"], old_path, depth + 1):
                    removed.append({
                        "path":  node["path"],
                        "name":  node["name"],
                        "unit":  unit_name,
                        "level": node["level"],
                    })

    for j, new_t in enumerate(new_topics):
        if j not in new_matched:
            new_path = f"{parent_path} > {new_t['name']}"
            added.append({
                "path":  new_path,
                "name":  new_t["name"],
                "unit":  unit_name,
                "level": depth,
            })
            if new_t.get("subtopics"):
                for node in _flatten_topics(new_t["subtopics"], new_path, depth + 1):
                    added.append({
                        "path":  node["path"],
                        "name":  node["name"],
                        "unit":  unit_name,
                        "level": node["level"],
                    })

    return added, removed, renamed


# ------------------------------------------------------------------ #
#  Pass 3 — Cross-unit moved detection                                #
# ------------------------------------------------------------------ #

def _pass3_moved_detection(topic_diff: dict, old: dict, new: dict) -> dict:
    removed = topic_diff["removed"]
    added = topic_diff["added"]
    moved = []

    removed_remaining = []
    added_matched = set()

    for rem in removed:
        rem_embedding = _get_embedding_for_topic(rem["name"], old)
        if rem_embedding is None:
            removed_remaining.append(rem)
            continue

        best_sim = 0
        best_match = None
        best_j = None

        for j, add in enumerate(added):
            if j in added_matched:
                continue
            add_embedding = _get_embedding_for_topic(add["name"], new)
            if add_embedding is None:
                continue
            sim = _cosine_similarity(rem_embedding, add_embedding)
            if sim > best_sim:
                best_sim = sim
                best_match = add
                best_j = j

        if best_sim >= MOVED_THRESHOLD and best_match is not None:
            moved.append({
                "name":       rem["name"],
                "from_unit":  rem["unit"],
                "to_unit":    best_match["unit"],
                "similarity": round(best_sim, 3),
            })
            added_matched.add(best_j)
        else:
            removed_remaining.append(rem)

    added_remaining = [a for j, a in enumerate(added) if j not in added_matched]

    topic_diff["removed"] = removed_remaining
    topic_diff["added"]   = added_remaining
    topic_diff["moved"]   = moved

    return topic_diff


# ------------------------------------------------------------------ #
#  Utilities                                                           #
# ------------------------------------------------------------------ #

def _cosine_similarity(a, b) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_embedding_for_topic(name: str, syllabus: dict):
    def search(topics):
        for t in topics:
            if t["name"].strip().lower() == name.strip().lower():
                return t.get("embedding")
            if t.get("subtopics"):
                result = search(t["subtopics"])
                if result is not None:
                    return result
        return None

    for unit in syllabus["units"]:
        result = search(unit["topics"])
        if result is not None:
            return result
    return None


def _flatten_topics(topics: list[dict], parent_path: str, level: int = 1) -> list[dict]:
    nodes = []
    for t in topics:
        path = f"{parent_path} > {t['name']}"
        nodes.append({"path": path, "name": t["name"], "level": level})
        if t.get("subtopics"):
            nodes.extend(_flatten_topics(t["subtopics"], path, level + 1))
    return nodes


def _print_summary(result: dict) -> None:
    print(f"\nSyllabus diff: {result['old_year']} → {result['new_year']}")
    print(f"  Units added:    {len(result['units']['added'])}")
    print(f"  Units removed:  {len(result['units']['removed'])}")
    print(f"  Topics added:   {result['summary']['total_added']}")
    print(f"  Topics removed: {result['summary']['total_removed']}")
    print(f"  Topics moved:   {result['summary']['total_moved']}")
    print(f"  Topics renamed: {result['summary']['total_renamed']}")
