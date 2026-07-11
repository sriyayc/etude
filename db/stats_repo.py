"""Repository for user stats — points, rank, streak, leaderboard."""

from db.client import get_client

client = get_client()


def get_user_points(user_id: str) -> int:
    response = (
        client.table("user_points")
        .select("points")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    return rows[0]["points"] if rows else 0


def get_user_rank(user_id: str) -> int | None:
    response = (
        client.table("leaderboard")
        .select("rank")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    return rows[0]["rank"] if rows else None


def get_user_streak(user_id: str) -> int:
    response = (
        client.table("user_streaks")
        .select("current_streak")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    return rows[0]["current_streak"] if rows else 0


def get_leaderboard(limit: int = 20) -> list[dict]:
    """Full ranked leaderboard (points, rank, streak), ordered by rank."""
    response = (
        client.table("leaderboard_full")
        .select("*")
        .order("rank")
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_subjects_active(user_id: str) -> int:
    """Distinct topics/subjects the user has attempted a quiz in."""
    response = (
        client.table("quiz_attempts")
        .select("topic_name")
        .eq("user_id", user_id)
        .execute()
    )
    topics = {row["topic_name"] for row in (response.data or [])}
    return len(topics)


def get_recent_quiz_activity(user_id: str, limit: int = 10) -> list[dict]:
    response = (
        client.table("quiz_attempts")
        .select("*")
        .eq("user_id", user_id)
        .order("attempted_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []
