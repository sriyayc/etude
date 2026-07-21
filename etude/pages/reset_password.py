"""Set a new password from an email reset link — /reset-password

Supabase puts a recovery token in the URL fragment and the JS client exchanges
it for a short-lived session automatically on page load. So by the time the
user submits, update_user({"password": ...}) applies to the right account
without us ever handling the token ourselves.
"""

import reflex as rx

from etude.state import UserState
from etude.styles import theme as t
from etude.components import ui
from etude.pages.login import brand_panel, field


def reset_password_page() -> rx.Component:
    return rx.hstack(
        brand_panel(),
        rx.center(
            rx.box(
                ui.eyebrow("Account recovery"),
                ui.heading("Choose a new password", size="32px", margin_top="10px", margin_bottom="6px"),
                rx.text(
                    "Pick something you haven't used before. You'll sign in with "
                    "your SRN as usual.",
                    color=t.TEXT_BODY,
                    font_size="15px",
                    margin_bottom="30px",
                ),
                rx.vstack(
                    field(
                        "New password", "At least 8 characters",
                        placeholder="••••••••",
                        type="password",
                        value=UserState.reset_password_value,
                        on_change=UserState.set_reset_password_value,
                    ),
                    field(
                        "Confirm password", None,
                        placeholder="••••••••",
                        type="password",
                        value=UserState.reset_confirm_value,
                        on_change=UserState.set_reset_confirm_value,
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
                        "Update password",
                        icon="check",
                        on_click=UserState.handle_reset_password,
                        disabled=UserState.reset_loading,
                        width="100%",
                        padding="13px",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Link expired?", color=t.TEXT_MUTED, font_size="14px"),
                    rx.link(
                        "Request a new one",
                        href="/forgot-password",
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
