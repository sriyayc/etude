"""Repository for syllabus_topics table operations."""

from db.client import get_client


def create_topic(
    document_id: str,
    subject: str,
    semester: int,
    unit_number: int,
    unit_title: str,
    topic: str,
    version: int,
    is_current: bool = True,
):
    client = get_client()
    response = client.table("syllabus_topics").insert({
        "document_id": document_id,
        "subject": subject,
        "semester": semester,
        "unit_number": unit_number,
        "unit_title": unit_title,
        "topic": topic,
        "version": version,
        "is_current": is_current,
    }).execute()
    return response.data[0] if response.data else None


def list_current_topics(subject: str, semester: int):
    """All current topics for a subject. Used for syllabus tagging."""
    client = get_client()
    response = (
        client.table("syllabus_topics")
        .select("*")
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("is_current", True)
        .execute()
    )
    return response.data


def list_topics_by_version(subject: str, semester: int, version: int):
    """Used for syllabus comparison."""
    client = get_client()
    response = (
        client.table("syllabus_topics")
        .select("*")
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("version", version)
        .execute()
    )
    return response.data


def mark_outdated(subject: str, semester: int, version: int):
    """Mark old syllabus version as not current. Called when new version is uploaded."""
    client = get_client()
    response = (
        client.table("syllabus_topics")
        .update({"is_current": False})
        .eq("subject", subject)
        .eq("semester", semester)
        .eq("version", version)
        .execute()
    )
    return response.data