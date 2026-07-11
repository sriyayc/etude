"""Syllabus comparison module."""

from db.syllabus_repo import list_topics_by_version


def compare_syllabi(
    subject: str,
    semester: int,
    v1: int,
    v2: int,
) -> dict:
    """
    Compare two versions of a syllabus to identify additions, deletions, and unchanged topics.
    """
    # 1. Fetch topics for both versions
    topics_v1 = list_topics_by_version(subject=subject, semester=semester, version=v1)
    topics_v2 = list_topics_by_version(subject=subject, semester=semester, version=v2)

    # 2. Extract topic text sets for comparison
    set_v1 = {t["topic"] for t in topics_v1}
    set_v2 = {t["topic"] for t in topics_v2}

    # 3. Compute diffs
    added = sorted(list(set_v2 - set_v1))
    removed = sorted(list(set_v1 - set_v2))
    unchanged = sorted(list(set_v1 & set_v2))

    return {
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
        "v1_count": len(set_v1),
        "v2_count": len(set_v2),
    }
