"""Application state."""

import reflex as rx
import asyncio
from typing import TypedDict

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
from db import stats_repo, subjects_repo, syllabus_repo


def _load_units(subject: str, semester: int) -> list[dict]:
    """Group syllabus_topics rows into units for topic pickers.

    Shared by QuizState/FlashcardState/NotesState so "pick a unit, then
    generate" only has one implementation.
    """

    try:
        rows = syllabus_repo.list_current_topics(
            subject=subject, semester=semester
        )
    except Exception:
        return []

    units: dict[int, dict] = {}

    for row in rows:
        unit_number = row.get("unit_number") or 0

        if unit_number not in units:
            units[unit_number] = {
                "unit_number": unit_number,
                "unit_title": (
                    row.get("unit_title") or f"Unit {unit_number}"
                ),
                "topics": [],
            }

        topic = row.get("topic")

        if topic:
            units[unit_number]["topics"].append(topic)

    result = sorted(units.values(), key=lambda u: u["unit_number"])

    # Precompute topic_count server-side: indexing a generically-typed
    # dict Var client-side (unit["topics"].length()) produces an `Any`
    # type Reflex can't call .length() on -- only .foreach()-able/typed
    # Vars support that. Simplest fix is to never need it client-side.
    for unit in result:
        unit["topic_count"] = len(unit["topics"])

    return result


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

    current_subject: dict = {
        "subject_code": "",
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
            f"{self.subject_code}/quiz"
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
    def load_subjects(self):
        """Load all subjects for the current semester."""

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
                    "subject_code": (
                        row.get("subject_code") or ""
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
    def load_subject(self):
        """Load the subject selected by the dynamic route."""

        self.resource_error = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            subject = subjects_repo.get_subject(
                semester=semester_number,
                subject_code=str(self.subject_code),
            )
        except Exception as exc:
            self.resource_error = str(exc)
            subject = None

        if not subject:
            self.current_subject = {
                "subject_code": str(self.subject_code),
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
            "subject_code": (
                subject.get("subject_code")
                or str(self.subject_code)
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
    def load_slides(self):
        """Load the active subject and its slides."""

        self.resource_error = ""
        self.chat_messages = []
        self.chat_input = ""
        self.pdf_url = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        try:
            subject = subjects_repo.get_subject(
                semester=semester_number,
                subject_code=str(self.subject_code),
            )
        except Exception as exc:
            self.resource_error = str(exc)
            self.slides = []
            return

        if not subject:
            self.slides = []
            self.current_subject = {
                "subject_code": str(self.subject_code),
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
            "subject_code": (
                subject.get("subject_code")
                or str(self.subject_code)
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

        document_id = self.current_subject.get("document_id")

        if not document_id:
            self.slides = []
            self.resource_error = (
                "This subject has no slide document attached."
            )
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
    def ask_ai(self, preset_question: str = ""):
        """Ask the RAG-grounded AI about the current subject."""

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


class _QuizQuestion(TypedDict):
    question: str
    options: list[str]
    answer: str
    explanation: str


class _SyllabusUnit(TypedDict):
    unit_number: int
    unit_title: str
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
    def load_units(self):
        self.units_error = ""
        self.questions = []
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_code), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    def generate_quiz(self, unit_number: int, unit_title: str):
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
                subject=str(self.subject_code),
                semester=semester_number,
                unit_number=unit_number,
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
    def submit_quiz(self):
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
    def load_units(self):
        self.units_error = ""
        self.cards = []
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_code), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    def generate_flashcards(self, unit_number: int, unit_title: str):
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
                subject=str(self.subject_code),
                semester=semester_number,
                unit_number=unit_number,
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
    def load_units(self):
        self.units_error = ""
        self.notes_md = ""
        self.selected_unit_title = ""

        try:
            semester_number = int(self.semester)
        except (TypeError, ValueError):
            semester_number = 1

        self.units = _load_units(str(self.subject_code), semester_number)

        if not self.units:
            self.units_error = "No syllabus units found for this subject yet."

    @rx.event
    def generate_notes(self, unit_number: int, unit_title: str):
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
                subject=str(self.subject_code),
                semester=semester_number,
                unit_number=unit_number,
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

    # ---- derived stats (loaded on dashboard/profile) ----
    points: int = 0
    rank: int = 0
    streak: int = 0
    subjects_active: int = 0

    # ---- leaderboard (loaded on /leaderboard) ----
    leaderboard_rows: list[dict] = []

    # ---- signup form fields ----
    signup_full_name: str = ""
    signup_srn: str = ""
    signup_email: str = ""
    signup_password: str = ""
    signup_error: str = ""
    signup_loading: bool = False

    # ---- login form fields ----
    login_srn: str = ""
    login_password: str = ""
    login_error: str = ""
    login_loading: bool = False

    # ---- admin upload form fields ----
    upload_title: str = ""
    upload_document_type: str = "textbook"
    upload_subject: str = ""
    upload_semester: str = "1"
    upload_error: str = ""
    upload_success: bool = False
    upload_loading: bool = False

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

    def set_upload_semester(self, value: str):
        self.upload_semester = value

    # ---- actions ----
    async def handle_signup(self):
        self.signup_error = ""

        if not all([
            self.signup_full_name,
            self.signup_srn,
            self.signup_password,
        ]):
            self.signup_error = "Fill in all fields."
            return

        self.signup_loading = True
        await asyncio.sleep(0.01)

        derived_email = f"{self.signup_srn.strip().lower()}@stu.pes.edu"

        try:
            auth_service.signup_student(
                email=derived_email,
                password=self.signup_password,
                full_name=self.signup_full_name,
                srn=self.signup_srn,
            )
        except Exception as e:
            self.signup_loading = False
            self.signup_error = str(e)
            return

        self.signup_loading = False
        return rx.redirect("/login")

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

        self.login_loading = False
        return rx.redirect("/dashboard")

    def clear_auth_errors(self):
        """Call this in on_load for /login and /signup.

        State persists across page navigation within a session, so an
        error left over from a previous failed attempt on either page
        would otherwise still be showing the next time that page loads.
        """
        self.login_error = ""
        self.signup_error = ""

    def logout(self):
        auth_service.logout()
        self.reset()
        return rx.redirect("/login")

    def load_profile(self):
        """Call this in on_load for /dashboard, /leaderboard, /profile."""
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

    def require_admin_role(self):
        """Chain after load_profile in on_load for admin-only routes."""
        if self.role != "admin":
            return rx.redirect("/dashboard")

    async def handle_upload(self, files: list[rx.UploadFile]):
        self.upload_error = ""
        self.upload_success = False

        if self.role != "admin":
            return rx.redirect("/dashboard")

        if not self.upload_title:
            self.upload_error = "Give the document a title."
            return

        if not self.upload_subject:
            self.upload_error = "Enter the subject code."
            return

        try:
            semester_number = int(self.upload_semester)
        except (TypeError, ValueError):
            self.upload_error = "Enter a valid semester."
            return

        if not files:
            self.upload_error = "Choose a file first."
            return

        self.upload_loading = True
        await asyncio.sleep(0.01)

        try:
            for file in files:
                data = await file.read()
                dest = rx.get_upload_dir() / file.filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

                doc_res = document_service.upload_document(
                    file_path=str(dest),
                    title=self.upload_title,
                    document_type=self.upload_document_type,
                    subject=self.upload_subject,
                    semester=semester_number,
                )

                ingestion_service.ingest_document(
                    pdf_path=str(dest),
                    document_type=self.upload_document_type,
                    subject=self.upload_subject,
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
                    existing_subject = subjects_repo.get_subject(
                        semester=semester_number,
                        subject_code=self.upload_subject,
                    )
                    subject_name = (
                        existing_subject.get("subject_name")
                        if existing_subject
                        else None
                    ) or self.upload_title

                    catalog_service.sync_catalog(
                        pdf_path=str(dest),
                        document_uuid=doc_res["document_id"],
                        subject_code=self.upload_subject,
                        subject_name=subject_name,
                        semester=semester_number,
                    )
        except Exception as e:
            self.upload_loading = False
            self.upload_error = str(e)
            return

        self.upload_loading = False
        self.upload_success = True
        self.upload_title = ""
        self.upload_subject = ""
