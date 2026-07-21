import reflex as rx

from etude.components import ui
from etude.pages.login import brand_panel, field
from etude.state import UserState
from etude.styles import theme as t


def signup_form_panel() -> rx.Component:
    return rx.center(
        rx.box(
            ui.eyebrow("New account"),
            ui.heading("Create your account", size="34px", margin_top="10px", margin_bottom="6px"),
            rx.text(
                "Sign up with your PES SRN to get started.",
                color=t.TEXT_BODY,
                font_size="15px",
                margin_bottom="30px",
            ),
            rx.vstack(
                field(
                    "Full name", None,
                    placeholder="Ada Lovelace",
                    value=UserState.signup_full_name,
                    on_change=UserState.set_signup_full_name,
                ),
                field(
                    "SRN", "Format: PES1UG25CS235",
                    placeholder="PES1UG25CS235",
                    value=UserState.signup_srn,
                    on_change=UserState.set_signup_srn,
                ),
                field(
                    "Password", None,
                    placeholder="••••••••",
                    type="password",
                    value=UserState.signup_password,
                    on_change=UserState.set_signup_password,
                ),
                rx.cond(
                    UserState.signup_error != "",
                    rx.hstack(
                        rx.icon("circle-alert", size=15, color=t.ERROR),
                        rx.text(UserState.signup_error, color=t.ERROR, font_size="13px"),
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
                    "Create account",
                    icon="arrow-right",
                    on_click=UserState.handle_signup,
                    width="100%",
                    padding="13px",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.text("Already have an account?", color=t.TEXT_MUTED, font_size="14px"),
                rx.link(
                    "Sign in",
                    href="/login",
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
        overflow_y="auto",
    )


def signup_page():
    return rx.hstack(
        brand_panel(),
        signup_form_panel(),
        width="100%",
        height="100vh",
        spacing="0",
        font_family=t.FONT_BODY,
    )
