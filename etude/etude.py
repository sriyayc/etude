import reflex as rx

from .pages.login import login_page
from .pages.signup import signup_page
from .pages.forgot_password import forgot_password_page
from .pages.reset_password import reset_password_page
from .pages.dashboard import dashboard_page
from .pages.leaderboard import leaderboard_page
from .pages.profile import profile_page
from .pages.subjects import subjects_page
from .pages.subject_detail import subject_detail_page
from .pages.slides_viewer import slides_viewer_page
from .pages.upload import upload_page
from .pages.quiz import quiz_page
from .pages.flashcards import flashcards_page
from .pages.notes import notes_page
from etude.styles import theme as t
from etude.state import UserState, QuizState, FlashcardState, NotesState, ResourceState

app = rx.App(
    stylesheets=[t.FONT_STYLESHEET],
    # Radix dark theme is configured via RadixThemesPlugin in rxconfig.py --
    # rx.App(theme=...) is deprecated since Reflex 0.9.0.
    style={
        "font_family": t.FONT_BODY,
        "background": t.BG_PAGE,
        "color": t.TEXT,
        "-webkit-font-smoothing": "antialiased",
    },
)


def index():
    return rx.fragment(rx.script("window.location.href = '/login'"))


app.add_page(index, route="/")
app.add_page(login_page, route="/login", on_load=UserState.clear_auth_errors)
app.add_page(signup_page, route="/signup", on_load=UserState.clear_auth_errors)
app.add_page(
    forgot_password_page,
    route="/forgot-password",
    on_load=UserState.clear_auth_errors,
)
app.add_page(
    reset_password_page,
    route="/reset-password",
    on_load=UserState.clear_auth_errors,
)
app.add_page(dashboard_page, route="/dashboard", on_load=UserState.load_profile)
app.add_page(leaderboard_page, route="/leaderboard", on_load=UserState.load_profile)
app.add_page(profile_page, route="/profile", on_load=UserState.load_profile)
app.add_page(
    upload_page,
    route="/upload",
    on_load=[
        UserState.load_profile,
        UserState.require_admin_role,
        UserState.load_upload_subjects,
    ],
)

# Dynamic routes — handles semesters, subjects, slides, quizzes, flashcards, and notes
app.add_page(subjects_page, route="/resources/[semester]", on_load=ResourceState.load_subjects)
app.add_page(subject_detail_page, route="/resources/[semester]/[subject_slug]", on_load=ResourceState.load_subject)
app.add_page(slides_viewer_page, route="/resources/[semester]/[subject_slug]/slides", on_load=ResourceState.load_slides)
app.add_page(quiz_page, route="/resources/[semester]/[subject_slug]/quiz", on_load=QuizState.load_units)
app.add_page(flashcards_page, route="/resources/[semester]/[subject_slug]/flashcards", on_load=FlashcardState.load_units)
app.add_page(notes_page, route="/resources/[semester]/[subject_slug]/notes", on_load=NotesState.load_units)