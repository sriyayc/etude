"""Features package."""

from features.qa import answer_question
from features.quiz import generate_quiz
from features.flashcards import generate_flashcards
from features.notes import generate_notes
from features.doubts import resolve_doubt

__all__ = [
    "answer_question",
    "generate_quiz",
    "generate_flashcards",
    "generate_notes",
    "resolve_doubt",
]
