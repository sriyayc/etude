"""Application state."""

import reflex as rx
import asyncio
from datetime import datetime, timezone
from typing import TypedDict

import config
from db import client as db_client
from services import (
    auth_service,
    document_service,
    ingestion_service,
    catalog_service,
    source_service,
    qa_service,
    quiz_service,
    flashcard_service,
    notes_service,
)
from db import (
    documents_repo,
    quiz_attempts_repo,
    stats_repo,
    subjects_repo,
    syllabus_repo,
)


def _deck_sort_key(title: str):
    """Sort deck titles so Unit 2 precedes Unit 10, not the other way round."""
    import re

    match = re.search(r"(\d+)", title or "")
    return (0, int(match.group(1)), title.lower()) if match else (1, 0, (title or "").lower())


def _relative_time(ts, now) -> str:
    """Render a timestamp as 'just now' / '3h ago' / '2d ago'."""
    if not ts:
        return ""
    try:
        when = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return ""
    seconds = (now - when).total_seconds()
    if seconds < 3600:
        return "just now" if seconds < 120 else f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    days = int(seconds // 86400)
    return "yesterday" if days == 1 else f"{days}d ago"


async def bind_session(state) -> None:
    """Bind this request's DB calls to the signed-in user of THIS session.

    Reflex state is per-session but the Supabase client is process-wide, so
    without this every DB call would run as whoever logged in most recently.
    Call at the top of any event handler that touches Supabase.
    """
    user = await state.get_state(UserState)
    db_client.set_access_token(user.access_token or None)


def _load_units(subject: str, semester: int) -> list[dict]:
    """Build the unit list for the quiz / flashcard / notes pickers.

    Each uploaded slide deck *is* a unit -- students upload one PDF per unit.
    Deriving units from the decks works for every subject, unlike the old
    syllabus_topics approach which only produced units for decks whose slides
    happened to contain a "Module content:" overview slide (so most subjects
    showed "No syllabus units found" and could generate nothing).

    Each unit carries its deck's ``document_id`` so generation can ground on
    that unit's own slides. Falls back to syllabus_topics only for subjects
    that have a syllabus doc but no slide decks.
    """
    import re

    try:
        docs = documents_repo.list_documents(subject=subject, semester=semester)
    except Exception:
        docs = []

    decks = [d for d in docs if d.get("document_type") == "slides" and d.get("id")]
    if decks:
        decks.sort(key=lambda d: _deck_sort_key(d.get("title") or ""))
        result: list[dict] = []
        used_numbers: set[int] = set()
        for index, deck in enumerate(decks, start=1):
            title = deck.get("title") or f"Unit {index}"
            match = re.search(r"(\d+)", title)
            number = int(match.group(1)) if match else index
            # Two decks parsing to the same number would collide on the
            # generated-content cache key -- keep them distinct.
            while number in used_numbers:
                number += 1
            used_numbers.add(number)
            doc_id = str(deck.get("id"))
            try:
                slide_n = len(subjects_repo.list_slides(document_id=doc_id))
            except Exception:
                slide_n = 0
            result.append(
                {
                    "unit_number": number,
                    "unit_title": title,
                    "document_id": doc_id,
                    "topic_count": slide_n,
                }
            )
        return result

    # ---- legacy fallback: syllabus_topics-based units ----
    try:
        rows = syllabus_repo.list_current_topics(subject=subject, semester=semester)
    except Exception:
        return []

    units: dict[int, dict] = {}
    for row in rows:
        unit_number = row.get("unit_number") or 0
        if unit_number not in units:
            units[unit_number] = {
                "unit_number": unit_number,
                "unit_title": row.get("unit_title") or f"Unit {unit_number}",
                "document_id": "",
                "topics": [],
            }
        topic = row.get("topic")
        if topic:
            units[unit_number]["topics"].append(topic)

    legacy = sorted(units.values(), key=lambda u: u["unit_number"])
    for unit in legacy:
        unit["topic_count"] = len(unit["topics"])
    return legacy


class ResourceState(rx.State):
    """State for subject, slide, and resource pages."""

    # ---------------------------------------------------------
    # Subject listing
    # ---------------------------------------------------------

    subjects: list[dict] = []
    filter_status: str = "all"
    resource_error: str = ""

    # ---------------------------------------------------------
    # Selected subject
    # ---------------------------------------------------------

    # A subject usually has several slide decks -- one per unit -- so the
    # viewer lists them and swaps between them rather than showing a single
    # PDF pinned to subjects.slides_document_id.
    slide_decks: list[dict] = []
    selected_deck_id: str = ""

    current_subject: dict = {
        "slug": "",
        "subject_name": "Subject",
        "semester": 0,
        "syllabus_status": "current",
        "slide_count": 0,
        "page_count": 0,
        "document_id": "",
    }

    # ---------------------------------------------------------
    # Slides
    # ---------------------------------------------------------

    slides: list[dict] = []
    pdf_url: str = ""

    # ---------------------------------------------------------
    # Slide AI chat
    # ---------------------------------------------------------

    chat_input: str = ""
    chat_messages: list[dict[str, str]] = []
    ai_thinking: bool = False

    # ---------------------------------------------------------
    # Computed values
    # ---------------------------------------------------------

    @rx.var
    def filtered_subjects(self) -> list[dict]:
        """Return subjects matching the selected syllabus filter."""

        if self.filter_status == "all":
            return self.subjects

        if self.filter_status == "current":
            return [
                subject
                for subject in self.subjects
                if subject.get("syllabus_status") == "current"
            ]

        if self.filter_status == "stale":
            return [
                subject
                for subject in self.subjects
                if subject.get("syllabus_status") != "current"
            ]

        return self.subjects

    @rx.var
    def quiz_url(self) -> str:
        """Return the quiz route for the active subject."""

        return (
            f"/resources/{self.semester}/"
            f"{self.subject_slug}/quiz"
        )

    # ---------------------------------------------------------
    # Subject events
    # ---------------------------------------------------------

    @rx.event
    def set_filter(self, value: str):
        """Set the subjects-page syllabus filter."""

        allowed = {"all", "current", "stale"}

        if value not in allowed:
            self.filter_status = "all"
            return

        self.filter_status = value

    @rx.event
    async def load_subjects(self):
        """Load all subjects for the current semester."""
        await bind_session(self)

        self.resource_error = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            rows = subjects_repo.list_subjects_by_semester(
                semester_number
            )
        except Exception as exc:
            self.subjects = []
            self.resource_error = str(exc)
            return

        normalized_subjects: list[dict] = []

        for row in rows:
            normalized_subjects.append(
                {
                    **row,
                    "slug": (
                        row.get("slug") or ""
                    ),
                    "subject_name": (
                        row.get("subject_name")
                        or row.get("subject")
                        or "Unnamed subject"
                    ),
                    "semester": (
                        row.get("semester") or semester_number
                    ),
                    "syllabus_status": (
                        row.get("syllabus_status") or "current"
                    ),
                    "slide_count": (
                        row.get("slide_count") or 0
                    ),
                    "page_count": (
                        row.get("page_count") or 0
                    ),
                    "document_id": (
                        row.get("slides_document_id") or ""
                    ),
                }
            )

        self.subjects = normalized_subjects

    @rx.event
    async def load_subject(self):
        """Load the subject selected by the dynamic route."""
        await bind_session(self)

        self.resource_error = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            subject = subjects_repo.get_subject_any(
                semester=semester_number,
                slug=str(self.subject_slug),
            )
        except Exception as exc:
            self.resource_error = str(exc)
            subject = None

        if not subject:
            self.current_subject = {
                "slug": str(self.subject_slug),
                "subject_name": "Subject not found",
                "semester": semester_number,
                "syllabus_status": "current",
                "slide_count": 0,
                "page_count": 0,
                "document_id": "",
            }
            return

        self.current_subject = {
            **subject,
            "slug": (
                subject.get("slug")
                or str(self.subject_slug)
            ),
            "subject_name": (
                subject.get("subject_name")
                or subject.get("subject")
                or "Unnamed subject"
            ),
            "semester": (
                subject.get("semester")
                or semester_number
            ),
            "syllabus_status": (
                subject.get("syllabus_status")
                or "current"
            ),
            "slide_count": (
                subject.get("slide_count") or 0
            ),
            "page_count": (
                subject.get("page_count") or 0
            ),
            "document_id": (
                subject.get("slides_document_id") or ""
            ),
        }

    # ---------------------------------------------------------
    # Slide events
    # ---------------------------------------------------------

    @rx.event
    async def load_slides(self):
        """Load the active subject and its slides."""
        await bind_session(self)

        self.resource_error = ""
        self.chat_messages = []
        self.chat_input = ""
        self.pdf_url = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            subject = subjects_repo.get_subject_any(
                semester=semester_number,
                slug=str(self.subject_slug),
            )
        except Exception as exc:
            self.resource_error = str(exc)
            self.slides = []
            return

        if not subject:
            self.slides = []
            self.current_subject = {
                "slug": str(self.subject_slug),
                "subject_name": "Subject not found",
                "semester": semester_number,
                "syllabus_status": "current",
                "slide_count": 0,
                "page_count": 0,
                "document_id": "",
            }
            return

        self.current_subject = {
            **subject,
            "slug": (
                subject.get("slug")
                or str(self.subject_slug)
            ),
            "subject_name": (
                subject.get("subject_name")
                or subject.get("subject")
                or "Unnamed subject"
            ),
            "semester": (
                subject.get("semester")
                or semester_number
            ),
            "syllabus_status": (
                subject.get("syllabus_status")
                or "current"
            ),
            "slide_count": (
                subject.get("slide_count") or 0
            ),
            "page_count": (
                subject.get("page_count") or 0
            ),
            "document_id": (
                subject.get("slides_document_id") or ""
            ),
        }

        try:
            docs = documents_repo.list_documents(
                subject=str(self.subject_slug), semester=semester_number
            )
        except Exception:
            docs = []

        decks = [d for d in docs if d.get("document_type") == "slides"]
        # Natural-ish ordering so "Unit 1..Unit 10" doesn't sort 1,10,2.
        decks.sort(key=lambda d: _deck_sort_key(d.get("title") or ""))
        self.slide_decks = [
            {"id": str(d.get("id")), "title": d.get("title") or "Untitled deck"}
            for d in decks
            if d.get("id")
        ]

        # Subjects ingested before multi-deck support only have the single
        # pointer on the subjects row.
        legacy_id = self.current_subject.get("document_id")
        if not self.slide_decks and legacy_id:
            self.slide_decks = [{"id": str(legacy_id), "title": "Lecture slides"}]

        if not self.slide_decks:
            self.slides = []
            self.selected_deck_id = ""
            self.resource_error = "This subject has no slide decks uploaded yet."
            return

        deck_ids = [d["id"] for d in self.slide_decks]
        if self.selected_deck_id not in deck_ids:
            self.selected_deck_id = deck_ids[0]

        await self._load_deck(self.selected_deck_id)

    @rx.event
    async def select_deck(self, deck_id: str):
        """Switch the viewer to another unit's deck."""
        await bind_session(self)
        self.selected_deck_id = deck_id
        self.resource_error = ""
        await self._load_deck(deck_id)

    async def _load_deck(self, document_id: str):
        """Load the PDF URL and extracted slides for one deck."""
        self.pdf_url = ""
        if not document_id:
            self.slides = []
            return

        try:
            self.pdf_url = source_service.get_document_url(str(document_id)) or ""
        except Exception:
            # The extracted-text fallback view still works without a
            # PDF link, so don't let a signed-URL failure blank the page.
            self.pdf_url = ""

        try:
            rows = subjects_repo.list_slides(
                document_id=str(document_id)
            )
        except Exception as exc:
            self.resource_error = str(exc)
            self.slides = []
            return

        normalized_slides: list[dict] = []

        for index, slide in enumerate(rows):
            normalized_slides.append(
                {
                    **slide,
                    "slide_number": (
                        slide.get("slide_number") or index + 1
                    ),
                    "module_number": (
                        slide.get("module_number") or 0
                    ),
                    "title": (
                        slide.get("title")
                        or f"Slide {index + 1}"
                    ),
                    "content": (
                        slide.get("content")
                        or slide.get("slide_text")
                        or ""
                    ),
                }
            )

        self.slides = normalized_slides

        self.current_subject = {
            **self.current_subject,
            "slide_count": len(normalized_slides),
        }

    # ---------------------------------------------------------
    # Chat events
    # ---------------------------------------------------------

    @rx.event
    def set_chat_input(self, value: str):
        """Update the sidebar chat input."""

        self.chat_input = value

    @rx.event
    async def ask_ai(self, preset_question: str = ""):
        """Ask the RAG-grounded AI about the current subject."""

        # qa_service.ask_question() calls get_current_user() and logs to
        # query_logs, so this session's token has to be bound first.
        await bind_session(self)

        question = (
            preset_question.strip()
            or self.chat_input.strip()
        )

        if not question:
            return

        self.chat_messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        self.chat_input = ""
        self.ai_thinking = True
        yield

        try:
            # Unscoped on purpose -- Etude AI answers from every ingested
            # document across every subject and semester, not just the
            # one the student happens to be viewing.
            result = qa_service.ask_question(query=question)
            answer = result.get("answer") or (
                "I couldn't find anything grounded in your "
                "syllabus for that."
            )

            if result.get("sources"):
                cited = ", ".join(
                    f"{s['source_file']} (p.{s['page_number']})"
                    for s in result["sources"][:3]
                )
                answer = f"{answer}\n\nSources: {cited}"

            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

        except Exception as exc:
            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": f"I could not process that question ({exc}).",
                }
            )

        finally:
            self.ai_thinking = False

    @rx.event
    def handle_chat_key(self, key: str, _key_info: dict | None = None):
        """Submit the chat input when Enter is pressed (input's on_change
        alone doesn't wire up a submit -- only the send icon click did)."""

        if key == "Enter":
            return ResourceState.ask_ai("")


class _QuizQuestion(TypedDict):
    question: str
    options: list[str]
    answer: str
    explanation: str


class _SyllabusUnit(TypedDict):
    unit_number: int
    unit_title: str
    document_id: str
    topics: list[str]
    topic_count: int


class _Flashcard(TypedDict):
    front: str
    back: str


class QuizState(rx.State):
    """State for the per-unit quiz page."""

    units: list[_SyllabusUnit] = []
    units_error: str = ""

    selected_unit_title: str = ""
    questions: list[_QuizQuestion] = []
    quiz_sources: list[dict] = []
    quiz_loading: bool = False
    quiz_error: str = ""

    current_index: int = 0
    answers: list[str] = []
    submitted: bool = False
    score: int = 0

    @rx.var
    def has_quiz(self) -> bool:
        return len(self.questions) > 0

    @rx.var
    def current_question(self) -> dict:
        if not self.questions:
            return {
                "question": "",
                "options": [],
                "answer": "",
                "explanation": "",
            }

        index = min(max(self.current_index, 0), len(self.questions) - 1)
        return self.questions[index]

    @rx.var
    def current_question_options(self) -> list[str]:
        # rx.foreach needs a concretely-typed list Var -- indexing
        # current_question["options"] directly yields `Any`, which
        # foreach refuses. This gives it a properly typed list instead.
        return self.current_question.get("options") or []

    @rx.var
    def selected_answer(self) -> str:
        if not self.answers or self.current_index >= len(self.answers):
            return ""
        return self.answers[self.current_index]

    @rx.var
    def progress_label(self) -> str:
        if not self.questions:
            return "0 / 0"
        return f"{self.current_index + 1} / {len(self.questions)}"

    @rx.var
    def is_last_question(self) -> bool:
        return bool(self.questions) and self.current_index == len(self.questions) - 1

    @rx.event
    async def load_units(self):
        await bind_session(self)
        self.units_error = ""
        self.questions = []
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_slug), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    async def generate_quiz(self, unit_number: int, unit_title: str, document_id: str = ""):
        await bind_session(self)
        self.quiz_error = ""
        self.quiz_loading = True
        self.selected_unit_title = unit_title
        self.current_index = 0
        self.answers = []
        self.submitted = False
        self.score = 0
        yield

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            result = quiz_service.get_quiz(
                topic=unit_title,
                subject=str(self.subject_slug),
                semester=semester_number,
                unit_number=unit_number,
                document_id=document_id or None,
            )
        except Exception as exc:
            self.quiz_loading = False
            self.quiz_error = str(exc)
            return

        if not result.get("success"):
            self.quiz_loading = False
            self.quiz_error = (
                result.get("message") or "Could not generate a quiz."
            )
            self.questions = []
            return

        self.questions = result.get("questions") or []
        self.quiz_sources = result.get("sources") or []
        self.answers = ["" for _ in self.questions]
        self.quiz_loading = False

    @rx.event
    def select_answer(self, option: str):
        if self.submitted:
            return
        if 0 <= self.current_index < len(self.answers):
            self.answers[self.current_index] = option

    @rx.event
    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1

    @rx.event
    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1

    @rx.event
    async def submit_quiz(self):
        # quiz_service records the attempt against get_current_user().
        await bind_session(self)

        score = 0
        for index, question in enumerate(self.questions):
            picked = self.answers[index] if index < len(self.answers) else ""
            if picked and picked == question.get("answer"):
                score += 1

        self.score = score
        self.submitted = True

        try:
            quiz_service.log_attempt(
                topic_name=self.selected_unit_title,
                score=score,
                total_questions=len(self.questions),
                questions=self.questions,
            )
        except Exception:
            pass

    @rx.event
    def retake_quiz(self):
        self.current_index = 0
        self.answers = ["" for _ in self.questions]
        self.submitted = False
        self.score = 0

    @rx.event
    def back_to_units(self):
        self.questions = []
        self.selected_unit_title = ""


class FlashcardState(rx.State):
    """State for the per-unit flashcard page."""

    units: list[_SyllabusUnit] = []
    units_error: str = ""

    selected_unit_title: str = ""
    cards: list[_Flashcard] = []
    card_sources: list[dict] = []
    cards_loading: bool = False
    cards_error: str = ""

    current_index: int = 0
    is_flipped: bool = False

    @rx.var
    def has_cards(self) -> bool:
        return len(self.cards) > 0

    @rx.var
    def current_card(self) -> dict:
        if not self.cards:
            return {"front": "", "back": ""}
        index = min(max(self.current_index, 0), len(self.cards) - 1)
        return self.cards[index]

    @rx.var
    def progress_label(self) -> str:
        if not self.cards:
            return "0 / 0"
        return f"{self.current_index + 1} / {len(self.cards)}"

    @rx.event
    async def load_units(self):
        await bind_session(self)
        self.units_error = ""
        self.cards = []
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_slug), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    async def generate_flashcards(self, unit_number: int, unit_title: str, document_id: str = ""):
        await bind_session(self)
        self.cards_error = ""
        self.cards_loading = True
        self.selected_unit_title = unit_title
        self.current_index = 0
        self.is_flipped = False
        yield

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            result = flashcard_service.get_flashcards(
                topic=unit_title,
                subject=str(self.subject_slug),
                semester=semester_number,
                unit_number=unit_number,
                document_id=document_id or None,
            )
        except Exception as exc:
            self.cards_loading = False
            self.cards_error = str(exc)
            return

        if not result.get("success"):
            self.cards_loading = False
            self.cards_error = (
                result.get("message") or "Could not generate flashcards."
            )
            self.cards = []
            return

        self.cards = result.get("cards") or []
        self.card_sources = result.get("sources") or []
        self.cards_loading = False

    @rx.event
    def flip_card(self):
        self.is_flipped = not self.is_flipped

    @rx.event
    def next_card(self):
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.is_flipped = False

    @rx.event
    def prev_card(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.is_flipped = False

    @rx.event
    def back_to_units(self):
        self.cards = []
        self.selected_unit_title = ""


class NotesState(rx.State):
    """State for the per-unit AI-compiled revision notes page."""

    units: list[_SyllabusUnit] = []
    units_error: str = ""

    selected_unit_title: str = ""
    notes_md: str = ""
    notes_sources: list[dict] = []
    notes_loading: bool = False
    notes_error: str = ""

    @rx.var
    def has_notes(self) -> bool:
        return bool(self.notes_md)

    @rx.event
    async def load_units(self):
        await bind_session(self)
        self.units_error = ""
        self.notes_md = ""
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_slug), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    async def generate_notes(self, unit_number: int, unit_title: str, document_id: str = ""):
        await bind_session(self)
        self.notes_error = ""
        self.notes_loading = True
        self.selected_unit_title = unit_title
        yield

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            result = notes_service.get_revision_notes(
                topic=unit_title,
                subject=str(self.subject_slug),
                semester=semester_number,
                unit_number=unit_number,
                document_id=document_id or None,
            )
        except Exception as exc:
            self.notes_loading = False
            self.notes_error = str(exc)
            return

        if not result.get("success"):
            self.notes_loading = False
            self.notes_error = (
                result.get("message") or "Could not generate notes."
            )
            self.notes_md = ""
            return

        self.notes_md = result.get("notes_md") or ""
        self.notes_sources = result.get("sources") or []
        self.notes_loading = False

    @rx.event
    def back_to_units(self):
        self.notes_md = ""
        self.selected_unit_title = ""


class UserState(rx.State):
    # ---- current session / profile ----
    user_id: str = ""
    email: str = ""
    full_name: str = ""
    srn: str = ""
    role: str = ""

    # Per-session Supabase credentials. These live in state (which Reflex keeps
    # per browser session) rather than on a shared client, so two people signed
    # in at once can't overwrite each other's identity.
    access_token: str = ""
    refresh_token: str = ""

    # ---- derived stats (loaded on dashboard/profile) ----
    points: int = 0
    rank: int = 0
    streak: int = 0
    subjects_active: int = 0

    # ---- leaderboard (loaded on /leaderboard) ----
    leaderboard_rows: list[dict] = []
    activity_rows: list[dict] = []
    tracker_rows: list[dict] = []

    # ---- signup form fields ----
    signup_full_name: str = ""
    signup_srn: str = ""
    signup_email: str = ""
    signup_password: str = ""
    signup_error: str = ""
    signup_notice: str = ""
    signup_loading: bool = False

    # ---- password reset ----
    reset_email: str = ""
    reset_password_value: str = ""
    reset_confirm_value: str = ""
    reset_error: str = ""
    reset_notice: str = ""
    reset_loading: bool = False

    # ---- login form fields ----
    login_srn: str = ""
    login_password: str = ""
    login_error: str = ""
    login_loading: bool = False

    # ---- admin upload form fields ----
    upload_title: str = ""
    upload_document_type: str = "textbook"
    # Holds the subject *name* picked from the dropdown. The stable slug is
    # derived from it at use time -- course codes change every year.
    upload_subject: str = ""
    upload_semester: str = "1"
    upload_subject_options: list[str] = []
    new_subject_name: str = ""
    subject_admin_error: str = ""
    subject_admin_notice: str = ""
    upload_error: str = ""
    upload_success: bool = False
    upload_loading: bool = False
    upload_status: str = ""
    upload_done_count: int = 0
    upload_total_count: int = 0

    @rx.var
    def upload_percent(self) -> int:
        """Completed share of a multi-file upload, for the progress bar."""
        if self.upload_total_count <= 0:
            return 0
        return int(self.upload_done_count * 100 / self.upload_total_count)

    # FIX: Changed from standard @property to @rx.var
    @rx.var
    def is_logged_in(self) -> bool:
        return bool(self.user_id)

    # ---- signup field setters ----
    def set_signup_full_name(self, value: str):
        self.signup_full_name = value

    def set_signup_srn(self, value: str):
        self.signup_srn = value

    def set_signup_email(self, value: str):
        self.signup_email = value

    def set_signup_password(self, value: str):
        self.signup_password = value

    # ---- login field setters ----
    def set_login_srn(self, value: str):
        self.login_srn = value

    def set_login_password(self, value: str):
        self.login_password = value

    # ---- upload field setters ----
    def set_upload_title(self, value: str):
        self.upload_title = value

    def set_upload_document_type(self, value: str):
        self.upload_document_type = value

    def set_upload_subject(self, value: str):
        self.upload_subject = value

    def set_new_subject_name(self, value: str):
        self.new_subject_name = value

    @rx.event
    async def set_upload_semester(self, value: str):
        self.upload_semester = value
        # Changing semester invalidates the picked subject -- a subject only
        # exists within one semester.
        self.upload_subject = ""
        await self.load_upload_subjects()

    @rx.event
    async def load_upload_subjects(self):
        """Populate the subject dropdown for the selected semester."""
        await bind_session(self)
        self.subject_admin_error = ""
        try:
            semester_number = int(self.upload_semester)
        except (TypeError, ValueError):
            self.upload_subject_options = []
            return
        try:
            rows = subjects_repo.list_subjects_by_semester(semester_number)
        except Exception as exc:
            self.subject_admin_error = str(exc)
            self.upload_subject_options = []
            return
        self.upload_subject_options = [
            r.get("subject_name") or "" for r in rows if r.get("subject_name")
        ]

    @rx.event
    async def create_new_subject(self):
        """Admin: add a subject to the selected semester."""
        await bind_session(self)
        self.subject_admin_error = ""
        self.subject_admin_notice = ""
        try:
            if auth_service.get_current_user().get("role") != "admin":
                self.subject_admin_error = "Only admins can manage subjects."
                return
            semester_number = int(self.upload_semester)
            row = subjects_repo.create_subject(semester_number, self.new_subject_name)
        except Exception as exc:
            self.subject_admin_error = str(exc)
            return
        self.subject_admin_notice = f"Added '{row.get('subject_name')}'."
        self.new_subject_name = ""
        await self.load_upload_subjects()

    @rx.event
    async def delete_selected_subject(self):
        """Admin: remove the subject currently picked in the dropdown."""
        await bind_session(self)
        self.subject_admin_error = ""
        self.subject_admin_notice = ""
        if not self.upload_subject:
            self.subject_admin_error = "Pick a subject to delete."
            return
        try:
            if auth_service.get_current_user().get("role") != "admin":
                self.subject_admin_error = "Only admins can manage subjects."
                return
            semester_number = int(self.upload_semester)
            subjects_repo.delete_subject(
                semester_number, subjects_repo.slugify(self.upload_subject)
            )
        except Exception as exc:
            self.subject_admin_error = str(exc)
            return
        self.subject_admin_notice = f"Deleted '{self.upload_subject}'."
        self.upload_subject = ""
        await self.load_upload_subjects()

    # ---- actions ----
    async def handle_signup(self):
        self.signup_error = ""

        if not all([
            self.signup_full_name,
            self.signup_srn,
            self.signup_email,
            self.signup_password,
        ]):
            self.signup_error = "Fill in all fields."
            return

        email = self.signup_email.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            self.signup_error = "Enter a valid email address."
            return

        if len(self.signup_password) < 8:
            self.signup_error = "Password must be at least 8 characters."
            return

        self.signup_loading = True
        await asyncio.sleep(0.01)

        try:
            result = auth_service.signup_student(
                email=email,
                password=self.signup_password,
                full_name=self.signup_full_name,
                srn=self.signup_srn,
            )
        except Exception as e:
            self.signup_loading = False
            self.signup_error = str(e)
            return

        self.signup_loading = False

        # When email confirmation is on, the account exists but can't sign in
        # until the link is clicked -- say so instead of dropping them on a
        # login form that will just reject them.
        if result.get("needs_confirmation"):
            self.signup_notice = (
                f"Almost there — we sent a confirmation link to {email}. "
                "Click it, then sign in with your SRN."
            )
            return

        return rx.redirect("/login")

    @rx.event
    def handle_login_key(self, key: str):
        """Let Enter submit the login form from either field."""
        if key == "Enter":
            return UserState.handle_login

    async def handle_login(self):
        self.login_error = ""

        if not self.login_srn or not self.login_password:
            self.login_error = "Enter your SRN and password."
            return

        self.login_loading = True
        await asyncio.sleep(0.01)

        try:
            result = auth_service.login(
                srn=self.login_srn,
                password=self.login_password,
            )
        except Exception:
            self.login_loading = False
            self.login_error = "Invalid SRN or password."
            return

        self.user_id = result["user_id"]
        self.email = result["email"]
        self.srn = result["srn"]
        self.full_name = result["full_name"]
        self.role = result["role"]
        # Held per session; every later request re-binds from here rather than
        # relying on a shared client's ambient session.
        self.access_token = result.get("access_token", "")
        self.refresh_token = result.get("refresh_token", "")

        self.login_loading = False
        self.login_password = ""
        return rx.redirect("/dashboard")

    def clear_auth_errors(self):
        """Call this in on_load for /login and /signup.

        State persists across page navigation within a session, so an
        error left over from a previous failed attempt on either page
        would otherwise still be showing the next time that page loads.
        """
        self.login_error = ""
        self.signup_error = ""
        self.signup_notice = ""
        self.reset_error = ""
        self.reset_notice = ""

    # ---- password reset setters ----
    def set_reset_email(self, value: str):
        self.reset_email = value

    def set_reset_password_value(self, value: str):
        self.reset_password_value = value

    def set_reset_confirm_value(self, value: str):
        self.reset_confirm_value = value

    async def handle_forgot_password(self):
        """Email a reset link. Deliberately does not reveal whether the
        address is registered."""
        self.reset_error = ""
        self.reset_notice = ""

        email = self.reset_email.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            self.reset_error = "Enter a valid email address."
            return

        self.reset_loading = True
        await asyncio.sleep(0.01)

        auth_service.request_password_reset(
            email=email,
            redirect_to=f"{config.APP_BASE_URL}/reset-password",
        )

        self.reset_loading = False
        self.reset_notice = (
            f"If {email} has an Etude account, a reset link is on its way. "
            "Check spam if it doesn't arrive in a few minutes."
        )

    async def handle_reset_password(self):
        """Set a new password using the recovery session from the email link."""
        self.reset_error = ""
        self.reset_notice = ""

        if len(self.reset_password_value) < 8:
            self.reset_error = "Password must be at least 8 characters."
            return

        if self.reset_password_value != self.reset_confirm_value:
            self.reset_error = "Passwords do not match."
            return

        self.reset_loading = True
        await asyncio.sleep(0.01)

        try:
            auth_service.update_password(self.reset_password_value)
        except Exception:
            self.reset_loading = False
            self.reset_error = (
                "That reset link is invalid or has expired. Request a new one."
            )
            return

        self.reset_loading = False
        self.reset_password_value = ""
        self.reset_confirm_value = ""
        return rx.redirect("/login")

    def logout(self):
        auth_service.logout()
        db_client.clear_access_token()
        self.reset()
        return rx.redirect("/login")

    async def load_profile(self):
        """Call this in on_load for /dashboard, /leaderboard, /profile."""
        # Identity must come from THIS session's token. Reading it from a
        # shared client is what made an admin's profile turn into a student's
        # (and vice versa) as soon as someone else signed in.
        db_client.set_access_token(self.access_token or None)

        try:
            user = auth_service.get_current_user()
        except Exception:
            return rx.redirect("/login")

        self.user_id = user["user_id"]
        self.email = user["email"]
        self.full_name = user.get("full_name") or ""
        self.srn = user.get("srn") or ""
        self.role = user["role"]

        self.points = stats_repo.get_user_points(self.user_id)
        self.rank = stats_repo.get_user_rank(self.user_id) or 0
        self.streak = stats_repo.get_user_streak(self.user_id)
        self.subjects_active = stats_repo.get_subjects_active(self.user_id)
        self.leaderboard_rows = stats_repo.get_leaderboard(limit=20)
        self._load_activity_and_tracker()

    def _load_activity_and_tracker(self):
        """Derive the profile's activity feed and syllabus tracker.

        Both panels shipped as hardcoded mock rows. They now read the
        user's real quiz attempts -- the only per-user progress signal the
        schema actually records.
        """
        self.activity_rows = []
        self.tracker_rows = []
        try:
            attempts = quiz_attempts_repo.get_user_attempts(self.user_id, limit=50)
        except Exception:
            return

        now = datetime.now(timezone.utc)
        for a in attempts[:5]:
            total = a.get("total_questions") or 0
            topic = a.get("topic_name") or "Quiz"
            self.activity_rows.append({
                "label": f"Quiz · {topic} · {a.get('score', 0)}/{total}",
                "when": _relative_time(a.get("attempted_at"), now),
            })

        # Tracker shows best score per topic -- the closest thing to
        # "how well do I know this unit" that we can honestly compute.
        best: dict[str, int] = {}
        for a in attempts:
            total = a.get("total_questions") or 0
            if not total:
                continue
            topic = a.get("topic_name") or "Quiz"
            pct = round((a.get("score") or 0) * 100 / total)
            best[topic] = max(best.get(topic, 0), pct)
        self.tracker_rows = [
            {"label": k, "pct": v}
            for k, v in sorted(best.items(), key=lambda kv: -kv[1])[:5]
        ]

    def require_admin_role(self):
        """Chain after load_profile in on_load for admin-only routes."""
        if self.role != "admin":
            return rx.redirect("/dashboard")

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Upload + ingest PDFs, reporting progress as it goes.

        This is a generator: every ``yield`` flushes the current status to the
        browser. The upload/ingest calls are synchronous and slow (embedding a
        deck takes tens of seconds), so they run via ``asyncio.to_thread`` --
        left inline they would block the event loop, no status would ever
        paint, and the page would just look frozen.
        """
        self.upload_error = ""
        self.upload_success = False
        self.upload_status = ""
        self.upload_done_count = 0
        self.upload_total_count = 0

        db_client.set_access_token(self.access_token or None)

        # Re-check the role server-side against this session's own token
        # rather than trusting client state, so a stale/spoofed role can't
        # get an upload through.
        try:
            if auth_service.get_current_user()["role"] != "admin":
                yield rx.redirect("/dashboard")
                return
        except Exception:
            yield rx.redirect("/login")
            return

        if not self.upload_subject:
            self.upload_error = "Pick a subject."
            return

        try:
            semester_number = int(self.upload_semester)
        except (TypeError, ValueError):
            self.upload_error = "Enter a valid semester."
            return

        if not files:
            self.upload_error = "Choose at least one file."
            return

        slug = subjects_repo.slugify(self.upload_subject)
        total = len(files)
        # The Title box is a pure override now -- always optional. It used to
        # be required for single uploads, but since it auto-clears after each
        # success, a follow-up single upload hit "Give the document a title"
        # and silently refused (looked like the upload just didn't fire).
        title_override = self.upload_title.strip()
        self.upload_loading = True
        self.upload_total_count = total
        yield

        try:
            for index, file in enumerate(files, start=1):
                label = file.filename or "file " + str(index)
                # Each PDF becomes its own deck tab titled from its filename
                # (e.g. "Unit 3.pdf" -> "Unit 3"). A single upload may override
                # that with whatever's in the Title box.
                if total == 1 and title_override:
                    deck_title = title_override
                else:
                    deck_title = (file.filename or label).rsplit(".", 1)[0].strip()
                counter = " (" + str(index) + "/" + str(total) + ")"

                self.upload_status = "Reading " + label + counter
                yield

                data = await file.read()
                dest = rx.get_upload_dir() / file.filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

                self.upload_status = "Uploading " + label + " to storage" + counter
                yield

                doc_res = await asyncio.to_thread(
                    document_service.upload_document,
                    file_path=str(dest),
                    title=deck_title,
                    document_type=self.upload_document_type,
                    subject=slug,
                    semester=semester_number,
                )

                self.upload_status = (
                    "Extracting text and building embeddings for "
                    + label + counter + " - this is the slow step"
                )
                yield

                await asyncio.to_thread(
                    ingestion_service.ingest_document,
                    pdf_path=str(dest),
                    document_type=self.upload_document_type,
                    subject=slug,
                    semester=semester_number,
                )

                # Slides/textbook content also backs the resources-browsing
                # UI and the quiz/flashcard/notes unit picker -- neither of
                # those read from Qdrant, so sync them here too. Syllabus
                # docs skip this: they go through syllabus_service instead,
                # which extracts a real "Unit N:" outline rather than
                # inferring one from running headers.
                if (
                    self.upload_document_type in ("slides", "textbook")
                    and doc_res.get("success")
                    and doc_res.get("document_id")
                ):
                    self.upload_status = "Indexing slides for " + label + counter
                    yield

                    existing_subject = subjects_repo.get_subject(
                        semester=semester_number, slug=slug
                    )
                    subject_name = (
                        existing_subject.get("subject_name")
                        if existing_subject
                        else None
                    ) or self.upload_subject

                    await asyncio.to_thread(
                        catalog_service.sync_catalog,
                        pdf_path=str(dest),
                        document_uuid=doc_res["document_id"],
                        subject_name=subject_name,
                        semester=semester_number,
                    )

                self.upload_done_count = index
                yield
        except Exception as e:
            self.upload_loading = False
            self.upload_status = ""
            self.upload_error = str(e)
            return

        self.upload_loading = False
        self.upload_status = ""
        self.upload_success = True
        self.upload_title = ""
        self.upload_done_count = 0
        self.upload_total_count = 0
        # Reset the dropzone. Without this the previous file stays selected in
        # the widget, so the next upload re-sends it (or the box looks stuck)
        # and you have to reload the page to pick another -- which is exactly
        # what made bulk uploading painful.
        yield rx.clear_selected_files("document_upload")
