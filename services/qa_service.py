"""QA service."""

import time
from services.auth_service import get_current_user
from features.qa import answer_question
from db.query_logs_repo import log_query


def ask_question(
    query: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Answer a user query and log the interaction in the query_logs DB table.
    """
    user = get_current_user()
    
    start_time = time.time()
    result = answer_question(query=query, subject=subject, semester=semester)
    end_time = time.time()
    
    response_time_ms = int((end_time - start_time) * 1000)
    
    # Log the interaction
    log_query(
        user_id=user["user_id"],
        question=query,
        answer=result["answer"],
        retrieved_chunk_ids=[],  # Can be populated if retriever logs chunk IDs
        response_time_ms=response_time_ms,
    )
    
    return result
