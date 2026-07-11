"""Application state."""

import reflex as rx
import asyncio

from services import auth_service, document_service
from db import stats_repo, subjects_repo 


import reflex as rx


class ResourceState(rx.State):
    chat_input: str = ""
    chat_messages: list[dict[str, str]] = []
    ai_thinking: bool = False

    slides: list[dict] = []
    current_slide_index: int = 0

    @rx.var
    def semester(self) -> str:
        """Current semester route parameter."""

        return (
            self.router.page.params.get(
                "semester",
                "1",
            )
            or "1"
        )

    @rx.var
    def subject_code(self) -> str:
        """Current subject-code route parameter."""

        return (
            self.router.page.params.get(
                "subject_code",
                "",
            )
            or ""
        )

    @rx.var
    def quiz_url(self) -> str:
        """Quiz route for the current subject."""

        return (
            f"/resources/{self.semester}/"
            f"{self.subject_code}/quiz"
        )

    @rx.event
    def set_chat_input(self, value: str):
        """Update the AI chat input."""

        self.chat_input = value

    @rx.event
    def ask_ai(
        self,
        preset_question: str = "",
    ):
        """Ask about the current slide."""

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
            # Replace this temporary response with your
            # QA/service-layer call later.
            response = (
                "AI integration is not connected yet. "
                "Your question was: "
                f"{question}"
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

        derived_email = f"{self.signup_srn.strip().lower()}@etude.local"

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
                )
        except Exception as e:
            self.upload_loading = False
            self.upload_error = str(e)
            return

        self.upload_loading = False
        self.upload_success = True
        self.upload_title = ""