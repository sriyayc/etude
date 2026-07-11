"""Application state."""

import reflex as rx

from services import auth_service
from db import stats_repo


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

    @property
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

    # ---- actions ----
    def handle_signup(self):
        self.signup_error = ""

        if not all([
            self.signup_full_name,
            self.signup_srn,
            self.signup_password,
        ]):
            self.signup_error = "Fill in all fields."
            return

        self.signup_loading = True
        yield

        # No visible email field in the UI (matches the reference design) —
        # Supabase Auth still needs *some* email under the hood, so we
        # derive a stable one from the SRN. Not shown to the user, not
        # used for anything except satisfying Supabase Auth's requirement.
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

    def handle_login(self):
        self.login_error = ""

        if not self.login_srn or not self.login_password:
            self.login_error = "Enter your SRN and password."
            return

        self.login_loading = True
        yield

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
        """Call this in on_load for /dashboard, /leaderboard, /profile.
        Restores the session and (re)loads stats for whoever's logged in."""
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
