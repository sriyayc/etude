"""
Syllabus comparator.
Compares two extracted syllabi and produces a structured diff.

Three-pass comparison:
  Pass 1 — Unit level: find added/removed entire units
  Pass 2 — Topic level: recursively diff topics at all 4 levels using embeddings
  Pass 3 — Cross-unit moved detection: reclassify removed→added pairs as moved

Vector comparison:
  Cosine similarity between embeddings handles renamed topics.
  Threshold 0.85 = same topic, below = genuinely different.
  No external libraries needed — pure Python cosine similarity.
"""

import math


SIMILARITY_THRESHOLD = 0.85  # above = same topic (possibly renamed)
MOVED_THRESHOLD = 0.85       # above = topic moved between units, not removed


# ------------------------------------------------------------------ #
#  Public entry point                                                  #
# ------------------------------------------------------------------ #

def compare_syllabi(old: dict, new: dict) -> dict:
    """
    Compare old and new syllabus JSON produced by extractor.py.

    Returns:
        {
            "subject":        str,
            "old_year":       str,
            "new_year":       str,
            "units": {
                "added":   [unit_name, ...],
                "removed": [unit_name, ...],
                "unchanged": [unit_name, ...]
            },
            "topics": {
                "added":   [{path, name, unit}, ...],
                "removed": [{path, name, unit}, ...],
                "moved":   [{name, from_unit, to_unit}, ...],
                "renamed": [{old_name, new_name, unit, similarity}, ...],
            },
            "summary": {
                "total_added":   int,
                "total_removed": int,
                "total_moved":   int,
                "total_renamed": int,
            }
        }
    """
    print(f"Comparing syllabi: {old['academic_year']} vs {new['academic_year']}")

    # Pass 1 — Unit level
    print("Pass 1: Unit-level comparison")
    unit_diff = _pass1_unit_comparison(old, new)

    # Pass 2 — Topic level (recursive through all 4 levels)
    print("Pass 2: Topic-level recursive comparison")
    topic_diff = _pass2_topic_comparison(old, new, unit_diff)

    # Pass 3 — Cross-unit moved topic detection
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
#  Pass 1 — Unit level comparison                                     #
# ------------------------------------------------------------------ #

def _pass1_unit_comparison(old: dict, new: dict) -> dict:
    """
    Compare units between old and new syllabus using embedding similarity.
    Handles renamed units (e.g. 'Process Management' → 'Process and Thread Management').
    """
    old_units = {u["unit"]: u for u in old["units"]}
    new_units = {u["unit"]: u for u in new["units"]}

    added = []
    removed = []
    unchanged = []
    renamed = []

    old_nums = set(old_units.keys())
    new_nums = set(new_units.keys())

    # Units present in both — check if name changed significantly
    for num in old_nums & new_nums:
        old_unit = old_units[num]
        new_unit = new_units[num]
        sim = _cosine_similarity(old_unit["embedding"], new_unit["embedding"])
        if sim >= SIMILARITY_THRESHOLD:
            unchanged.append(old_unit["unit_name"])
        else:
            renamed.append({
                "unit_number": num,
                "old_name": old_unit["unit_name"],
                "new_name": new_unit["unit_name"],
                "similarity": round(sim, 3)
            })
            unchanged.append(old_unit["unit_name"])

    # Units only in old — removed
    for num in old_nums - new_nums:
        removed.append(old_units[num]["unit_name"])

    # Units only in new — added
    for num in new_nums - old_nums:
        added.append(new_units[num]["unit_name"])

    return {
        "added":    added,
        "removed":  removed,
        "unchanged": unchanged,
        "renamed":  renamed,
    }


# ------------------------------------------------------------------ #
#  Pass 2 — Recursive topic comparison                                #
# ------------------------------------------------------------------ #

def _pass2_topic_comparison(old: dict, new: dict, unit_diff: dict) -> dict:
    """
    For each unit present in both syllabi, recursively compare topics
    at all levels using embedding similarity.

    Builds path strings like:
    "Unit 1 > CPU Scheduling > Scheduling Algorithms > FIFO"
    for precise change reporting.
    """
    added = []
    removed = []
    renamed = []

    old_units = {u["unit"]: u for u in old["units"]}
    new_units = {u["unit"]: u for u in new["units"]}

    shared_unit_nums = set(old_units.keys()) & set(new_units.keys())

    for num in shared_unit_nums:
        old_unit = old_units[num]
        new_unit = new_units[num]
        unit_path = f"Unit {num}: {old_unit['unit_name']}"

        unit_added, unit_removed, unit_renamed = _diff_topic_lists(
            old_topics=old_unit["topics"],
            new_topics=new_unit["topics"],
            parent_path=unit_path,
            unit_name=old_unit["unit_name"],
            depth=1,
        )
        added.extend(unit_added)
        removed.extend(unit_removed)
        renamed.extend(unit_renamed)

    # Topics from entirely removed units are all removed
    removed_unit_nums = set(old_units.keys()) - set(new_units.keys())
    for num in removed_unit_nums:
        unit = old_units[num]
        unit_path = f"Unit {num}: {unit['unit_name']}"
        all_nodes = _flatten_topics(unit["topics"], unit_path)
        for node in all_nodes:
            removed.append({
                "path": node["path"],
                "name": node["name"],
                "unit": unit["unit_name"],
                "level": node["level"],
            })

    # Topics from entirely added units are all added
    added_unit_nums = set(new_units.keys()) - set(old_units.keys())
    for num in added_unit_nums:
        unit = new_units[num]
        unit_path = f"Unit {num}: {unit['unit_name']}"
        all_nodes = _flatten_topics(unit["topics"], unit_path)
        for node in all_nodes:
            added.append({
                "path": node["path"],
                "name": node["name"],
                "unit": unit["unit_name"],
                "level": node["level"],
            })

    return {
        "added":   added,
        "removed": removed,
        "moved":   [],      # filled by Pass 3
        "renamed": renamed,
    }


def _diff_topic_lists(
    old_topics: list[dict],
    new_topics: list[dict],
    parent_path: str,
    unit_name: str,
    depth: int,
) -> tuple[list, list, list]:
    """
    Compare two lists of topics at the same level using embedding similarity.
    Recursively diffs subtopics for matched pairs.
    Returns (added, removed, renamed) lists.
    """
    added = []
    removed = []
    renamed = []

    if depth > 4:
        return added, removed, renamed

    old_matched = set()
    new_matched = set()

    # Build similarity matrix
    matches = []
    for i, old_t in enumerate(old_topics):
        for j, new_t in enumerate(new_topics):
            sim = _cosine_similarity(old_t["embedding"], new_t["embedding"])
            if sim >= SIMILARITY_THRESHOLD:
                matches.append((sim, i, j))

    # Sort by similarity descending — best matches first
    matches.sort(reverse=True)

    # Greedily assign best matches
    for sim, i, j in matches:
        if i in old_matched or j in new_matched:
            continue
        old_matched.add(i)
        new_matched.add(j)

        old_t = old_topics[i]
        new_t = new_topics[j]
        old_path = f"{parent_path} > {old_t['name']}"
        new_path = f"{parent_path} > {new_t['name']}"

        # Check if name changed despite being the same topic
        if old_t["name"].strip().lower() != new_t["name"].strip().lower():
            renamed.append({
                "old_name":   old_t["name"],
                "new_name":   new_t["name"],
                "unit":       unit_name,
                "path":       old_path,
                "similarity": round(sim, 3),
                "level":      depth,
            })

        # Recurse into subtopics
        if old_t.get("subtopics") or new_t.get("subtopics"):
            sub_added, sub_removed, sub_renamed = _diff_topic_lists(
                old_topics=old_t.get("subtopics", []),
                new_topics=new_t.get("subtopics", []),
                parent_path=old_path,
                unit_name=unit_name,
                depth=depth + 1,
            )
            added.extend(sub_added)
            removed.extend(sub_removed)
            renamed.extend(sub_renamed)

    # Unmatched old topics = removed
    for i, old_t in enumerate(old_topics):
        if i not in old_matched:
            old_path = f"{parent_path} > {old_t['name']}"
            removed.append({
                "path":  old_path,
                "name":  old_t["name"],
                "unit":  unit_name,
                "level": depth,
            })
            # All children of a removed topic are also removed
            if old_t.get("subtopics"):
                for node in _flatten_topics(old_t["subtopics"], old_path):
                    removed.append({
                        "path":  node["path"],
                        "name":  node["name"],
                        "unit":  unit_name,
                        "level": node["level"],
                    })

    # Unmatched new topics = added
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
                for node in _flatten_topics(new_t["subtopics"], new_path):
                    added.append({
                        "path":  node["path"],
                        "name":  node["name"],
                        "unit":  unit_name,
                        "level": node["level"],
                    })

    return added, removed, renamed


# ------------------------------------------------------------------ #
#  Pass 3 — Cross-unit moved topic detection                          #
# ------------------------------------------------------------------ #

def _pass3_moved_detection(topic_diff: dict, old: dict, new: dict) -> dict:
    """
    Check if any 'removed' topic appears as 'added' in a different unit.
    If embedding similarity >= MOVED_THRESHOLD, reclassify as 'moved'.

    This catches reorganizations where a topic shifts between units
    without being genuinely removed from the syllabus.
    """
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

    # Remove matched 'added' entries that were actually moves
    added_remaining = [a for j, a in enumerate(added) if j not in added_matched]

    topic_diff["removed"] = removed_remaining
    topic_diff["added"] = added_remaining
    topic_diff["moved"] = moved

    return topic_diff


def _get_embedding_for_topic(name: str, syllabus: dict) -> list[float] | None:
    """Search syllabus tree for a topic by name and return its embedding."""
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


# ------------------------------------------------------------------ #
#  Utilities                                                           #
# ------------------------------------------------------------------ #

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure Python cosine similarity. No external libraries needed."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _flatten_topics(topics: list[dict], parent_path: str, level: int = 1) -> list[dict]:
    """Recursively flatten a topic tree into a list of nodes with paths."""
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
