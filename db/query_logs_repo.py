"""Repository for query_logs table operations."""

from db.client import get_client


def log_query(
    user_id: str,
    question: str,
    answer: str = None,
    retrieved_chunk_ids: list[str] = None,
    response_time_ms: int = None,
):
    client = get_client()
    response = client.table("query_logs").insert({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "retrieved_chunk_ids": retrieved_chunk_ids or [],
        "response_time_ms": response_time_ms,
    }).execute()
    return response.data[0] if response.data else None


def get_user_queries(user_id: str, limit: int = 50):
    client = get_client()
    response = (
        client.table("query_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data