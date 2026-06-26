"""Repository for quiz_attempts table operations."""

from db.client import get_client


def create_attempt(
    user_id: str,
    topic_name: str,
    score: int,
    total_questions: int,
    questions: list[dict],
):
    client = get_client()
    response = client.table("quiz_attempts").insert({
        "user_id": user_id,
        "topic_name": topic_name,
        "score": score,
        "total_questions": total_questions,
        "questions": questions,
    }).execute()
    return response.data[0] if response.data else None


def get_user_attempts(user_id: str, limit: int = 20):
    client = get_client()
    response = (
        client.table("quiz_attempts")
        .select("*")
        .eq("user_id", user_id)
        .order("attempted_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data