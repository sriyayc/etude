import reflex as rx

from etude.components import ui
from etude.state import UserState
from etude.styles import theme as t


def feature_row(icon: str, text: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(icon, size=16, color="white"),
            background="rgba(255,255,255,0.16)",
            border_radius=t.RADIUS_SM,
            padding="8px",
            display="flex",
        ),
        rx.text(text, color="rgba(255,255,255,0.92)", font_size="15px", font_weight="500"),
        spacing="3",
        align_items="center",
    )


def brand_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            # logo.png already contains the "etude" wordmark.
            rx.image(src="/logo.png", height="40px", width="auto"),
            rx.spacer(),
            rx.vstack(
                rx.heading(
                    "Your whole syllabus, in one place.",
                    color="white",
                    font_family=t.FONT_DISPLAY,
                    font_weight="700",
                    font_size="40px",
                    line_height="1.15",
                    max_width="460px",
                ),
                rx.text(
                    "Etude brings your slides, textbook and an AI tutor together — "
                    "and the tutor answers only from your syllabus, citing every source.",
                    color="rgba(255,255,255,0.82)",
                    font_size="16px",
                    line_height="1.6",
                    max_width="460px",
                    margin_top="4px",
                ),
                rx.vstack(
                    feature_row("book-open", "Slides & textbook, unified per unit"),
                    feature_row("sparkles", "Syllabus-grounded AI tutor with citations"),
                    feature_row("clipboard-check", "Auto-generated quizzes & flashcards"),
                    feature_row("trophy", "Class leaderboard to keep you going"),
                    spacing="4",
                    align_items="start",
                    margin_top="28px",
                ),
                spacing="3",
                align_items="start",
            ),
            rx.spacer(),
            rx.text(
                "Built for PES University",
                color="rgba(255,255,255,0.7)",
                font_size="13px",
            ),
            align_items="start",
            height="100%",
            padding="48px",
            spacing="0",
        ),
        width="50%",
        height="100vh",
        background=t.HERO_GRADIENT,
        display=["none", "none", "flex", "flex"],
    )


def field(label: str, hint: str | None, **input_props) -> rx.Component:
    children = [
        rx.text(label, color=t.TEXT, font_size="13px", font_weight="600"),
        ui.text_input(**input_props),
    ]
    if hint:
        children.append(rx.text(hint, color=t.TEXT_MUTED, font_size="12px"))
    return rx.vstack(*children, spacing="2", width="100%", align_items="start")


def form_panel() -> rx.Component:
    return rx.center(
        rx.box(
            ui.eyebrow("PESU sign in"),
            ui.heading("Welcome back", size="34px", margin_top="10px", margin_bottom="6px"),
            rx.text(
                "Sign in with your PES SRN to continue.",
                color=t.TEXT_BODY,
                font_size="15px",
                margin_bottom="30px",
            ),
            rx.vstack(
                field(
                    "SRN", "Format: PES2UG24CS510",
                    placeholder="PES2UG24CS510",
                    value=UserState.login_srn,
                    on_change=UserState.set_login_srn,
                    on_key_down=UserState.handle_login_key,
                ),
                field(
                    "Password", None,
                    placeholder="••••••••",
                    type="password",
                    value=UserState.login_password,
                    on_change=UserState.set_login_password,
                    on_key_down=UserState.handle_login_key,
                ),
                rx.cond(
                    UserState.login_error != "",
                    rx.hstack(
                        rx.icon("circle-alert", size=15, color=t.ERROR),
                        rx.text(UserState.login_error, color=t.ERROR, font_size="13px"),
                        spacing="2",
                        align_items="center",
                        background=t.ERROR_SOFT,
                        border_radius=t.RADIUS_SM,
                        padding="10px 12px",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                ui.primary_button(
                    "Sign in",
                    icon="arrow-right",
                    on_click=UserState.handle_login,
                    width="100%",
                    padding="13px",
                ),
                rx.link(
                    "Forgot your password?",
                    href="/forgot-password",
                    color=t.TEXT_MUTED,
                    font_size="13px",
                    _hover={"color": t.ACCENT_STRONG},
                    width="100%",
                    text_align="center",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.text("New here?", color=t.TEXT_MUTED, font_size="14px"),
                rx.link(
                    "Create an account",
                    href="/signup",
                    color=t.ACCENT_STRONG,
                    font_size="14px",
                    font_weight="600",
                ),
                spacing="1",
                margin_top="24px",
                justify="center",
                width="100%",
            ),
            rx.hstack(
                rx.icon("shield-check", size=15, color=t.TEXT_MUTED),
                rx.text(
                    "Etude only accepts PESU SRNs. Your password is a local identity "
                    "for ranking and sync — it is never used to access PESU Academy.",
                    color=t.TEXT_MUTED,
                    font_size="12px",
                    line_height="1.6",
                ),
                align_items="start",
                spacing="2",
                margin_top="28px",
            ),
            width="100%",
            max_width="420px",
            padding="40px",
        ),
        width=["100%", "100%", "50%", "50%"],
        height="100vh",
        background=t.BG_PAGE,
    )


def login_page():
    return rx.hstack(
        brand_panel(),
        form_panel(),
        width="100%",
        height="100vh",
        spacing="0",
        font_family=t.FONT_BODY,
    )
