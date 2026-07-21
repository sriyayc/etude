"""Request a password-reset email — /forgot-password"""

import reflex as rx

from etude.state import UserState
from etude.styles import theme as t
from etude.components import ui
from etude.pages.login import brand_panel, field


def forgot_password_page() -> rx.Component:
    return rx.hstack(
        brand_panel(),
        rx.center(
            rx.box(
                ui.eyebrow("Account recovery"),
                ui.heading("Reset your password", size="32px", margin_top="10px", margin_bottom="6px"),
                rx.text(
                    "Enter the personal email you signed up with and we'll send "
                    "you a reset link.",
                    color=t.TEXT_BODY,
                    font_size="15px",
                    margin_bottom="30px",
                ),
                rx.vstack(
                    field(
                        "Email", None,
                        placeholder="you@example.com",
                        type="email",
                        value=UserState.reset_email,
                        on_change=UserState.set_reset_email,
                    ),
                    rx.cond(
                        UserState.reset_notice != "",
                        rx.hstack(
                            rx.icon("mail-check", size=15, color=t.SUCCESS),
                            rx.text(UserState.reset_notice, color=t.SUCCESS, font_size="13px"),
                            spacing="2",
                            align_items="start",
                            background=t.SUCCESS_SOFT,
                            border_radius=t.RADIUS_SM,
                            padding="10px 12px",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        UserState.reset_error != "",
                        rx.hstack(
                            rx.icon("circle-alert", size=15, color=t.ERROR),
                            rx.text(UserState.reset_error, color=t.ERROR, font_size="13px"),
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
                        "Send reset link",
                        icon="mail",
                        on_click=UserState.handle_forgot_password,
                        disabled=UserState.reset_loading,
                        width="100%",
                        padding="13px",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Remembered it?", color=t.TEXT_MUTED, font_size="14px"),
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
                width="100%",
                max_width="400px",
            ),
            width=["100%", "100%", "50%", "50%"],
            height="100vh",
            background=t.BG_PAGE,
        ),
        width="100%",
        spacing="0",
        background=t.BG_PAGE,
        font_family=t.FONT_BODY,
        on_mount=UserState.clear_auth_errors,
    )
