import reflex as rx

from .pages.login import login_page
from .pages.signup import signup_page
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
from etude.styles.theme import FONT_STYLESHEET
from etude.state import UserState

app = rx.App(
    stylesheets=[FONT_STYLESHEET],
)


def index():
    return rx.fragment(rx.script("window.location.href = '/login'"))


app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(signup_page, route="/signup")
app.add_page(dashboard_page, route="/dashboard", on_load=UserState.load_profile)
app.add_page(leaderboard_page, route="/leaderboard", on_load=UserState.load_profile)
app.add_page(profile_page, route="/profile", on_load=UserState.load_profile)
app.add_page(
    upload_page,
    route="/upload",
    on_load=[UserState.load_profile, UserState.require_teacher_role],
)

# Dynamic routes — one file handles ALL semesters (1-8) and ALL subjects,
# via the [semester] / [subject_code] URL parameters
app.add_page(subjects_page, route="/resources/[semester]")
app.add_page(subject_detail_page, route="/resources/[semester]/[subject_code]")
app.add_page(slides_viewer_page, route="/resources/[semester]/[subject_code]/slides")
app.add_page(quiz_page, route="/resources/[semester]/[subject_code]/quiz")
app.add_page(flashcards_page, route="/resources/[semester]/[subject_code]/flashcards")
app.add_page(notes_page, route="/resources/[semester]/[subject_code]/notes")