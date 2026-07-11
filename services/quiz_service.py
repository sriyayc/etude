"""Quiz service."""

from services.auth_service import get_current_user
from features.quiz import generate_quiz
from db.quiz_attempts_repo import create_attempt, get_user_attempts


def get_quiz(
    topic: str,
    subject: str,
    semester: int,
    num_questions: int = 5,
) -> dict:
    """
    Generate a quiz on a topic.
    """
    return generate_quiz(
        topic=topic,
        subject=subject,
        semester=semester,
        num_questions=num_questions,
    )


def log_attempt(
    topic_name: str,
    score: int,
    total_questions: int,
    questions: list[dict],
) -> dict:
    """
    Save a quiz attempt to the database.
    """
    user = get_current_user()
    return create_attempt(
        user_id=user["user_id"],
        topic_name=topic_name,
        score=score,
        total_questions=total_questions,
        questions=questions,
    )


def list_attempts(limit: int = 20) -> list[dict]:
    """
    Get the current user's past quiz attempts.
    """
    user = get_current_user()
    return get_user_attempts(user_id=user["user_id"], limit=limit)
