"""Services package."""

from services.auth_service import (
    signup_student,
    signup_teacher,
    login,
    logout,
    get_current_user,
    require_teacher,
)
from services.storage_service import (
    upload_pdf,
    delete_pdf,
    download_pdf,
    get_public_url,
)
from services.document_service import upload_document
from services.ingestion_service import ingest_document
from services.qa_service import ask_question
from services.quiz_service import get_quiz, log_attempt, list_attempts
from services.notes_service import get_revision_notes
from services.flashcard_service import get_flashcards
from services.doubts_service import clear_doubt
from services.source_service import get_document_url, get_available_sources
from services.syllabus_service import upload_and_process_syllabus, get_syllabus_diff, tag_document

__all__ = [
    "signup_student",
    "signup_teacher",
    "login",
    "logout",
    "get_current_user",
    "require_teacher",
    "upload_pdf",
    "delete_pdf",
    "download_pdf",
    "get_public_url",
    "upload_document",
    "ingest_document",
    "ask_question",
    "get_quiz",
    "log_attempt",
    "list_attempts",
    "get_revision_notes",
    "get_flashcards",
    "clear_doubt",
    "get_document_url",
    "get_available_sources",
    "upload_and_process_syllabus",
    "get_syllabus_diff",
    "tag_document",
]
