import reflex as rx

from .pages.login import login_page
from .pages.signup import signup_page
from .pages.dashboard import dashboard_page
from .pages.leaderboard import leaderboard_page
from .pages.profile import profile_page
from etude.styles.theme import FONT_STYLESHEET
from etude.state import UserState

app = rx.App(
    stylesheets=[FONT_STYLESHEET],
)

app.add_page(login_page, route="/login")
app.add_page(signup_page, route="/signup")
app.add_page(dashboard_page, route="/dashboard", on_load=UserState.load_profile)
app.add_page(leaderboard_page, route="/leaderboard", on_load=UserState.load_profile)
app.add_page(profile_page, route="/profile", on_load=UserState.load_profile)
