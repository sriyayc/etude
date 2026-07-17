"""Application state."""

import reflex as rx
import asyncio

from services import auth_service, document_service
from db import stats_repo, subjects_repo 


import reflex as rx


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
    current_slide_index: int = 0

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
    def current_slide(self) -> dict:
        """Return the currently selected slide safely."""

        if not self.slides:
            return {
                "title": "No slides available",
                "content": (
                    "No slide content has been loaded for this subject."
                ),
                "module_number": 0,
                "slide_number": 0,
            }

        index = min(
            max(self.current_slide_index, 0),
            len(self.slides) - 1,
        )

        slide = self.slides[index]

        return {
            **slide,
            "title": slide.get("title") or "Untitled slide",
            "content": slide.get("content") or "",
            "module_number": slide.get("module_number") or 0,
            "slide_number": slide.get("slide_number") or index + 1,
        }

    @rx.var
    def slide_number_padded(self) -> str:
        """Return a two-digit slide number."""

        if not self.slides:
            return "00"

        return str(self.current_slide_index + 1).zfill(2)

    @rx.var
    def slide_counter(self) -> str:
        """Return a safe slide counter label."""

        if not self.slides:
            return "slide 0 / 0"

        return (
            f"slide {self.current_slide_index + 1} "
            f"/ {len(self.slides)}"
        )

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
                        row.get("document_id") or ""
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
                subject.get("document_id") or ""
            ),
        }

    # ---------------------------------------------------------
    # Slide events
    # ---------------------------------------------------------

    @rx.event
    def load_slides(self):
        """Load the active subject and its slides."""

        self.resource_error = ""
        self.current_slide_index = 0
        self.chat_messages = []
        self.chat_input = ""

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
                subject.get("document_id") or ""
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

    @rx.event
    def prev_slide(self):
        """Move to the previous slide."""

        if self.current_slide_index > 0:
            self.current_slide_index -= 1

    @rx.event
    def next_slide(self):
        """Move to the next slide."""

        if (
            self.slides
            and self.current_slide_index
            < len(self.slides) - 1
        ):
            self.current_slide_index += 1

    # ---------------------------------------------------------
    # Chat events
    # ---------------------------------------------------------

    @rx.event
    def set_chat_input(self, value: str):
        """Update the sidebar chat input."""

        self.chat_input = value

    @rx.event
    def ask_ai(self, preset_question: str = ""):
        """Temporarily handle a question about the current slide."""

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

        try:
            slide_title = self.current_slide.get(
                "title",
                "the current slide",
            )

            response = (
                "AI integration is not connected yet. "
                f"You asked about {slide_title}: {question}"
            )

            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

        except Exception:
            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "I could not process that question."
                    ),
                }
            )

        finally:
            self.ai_thinking = False


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

    # ---- teacher upload form fields ----
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

    def require_teacher_role(self):
        """Chain after load_profile in on_load for teacher-only routes."""
        if self.role != "teacher":
            return rx.redirect("/dashboard")

    async def handle_upload(self, files: list[rx.UploadFile]):
        self.upload_error = ""
        self.upload_success = False

        if self.role != "teacher":
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

                document_service.upload_document(
                    file_path=str(dest),
                    title=self.upload_title,
                    document_type=self.upload_document_type,
                    subject=self.upload_subject,
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
