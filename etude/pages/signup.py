import reflex as rx

from etude.components.button import primary_button
from etude.components.input import text_input
from etude.pages.login import left_panel
from etude.state import UserState


ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def field_label(text: str):
    return rx.text(
        text,
        color=ACCENT,
        font_family="monospace",
        font_size="10px",
        letter_spacing="0.2em",
        text_transform="uppercase",
        align_self="start",
    )


def signup_right_panel():
    return rx.center(

        rx.box(

            rx.text(
                "// NEW ACCOUNT",
                color=ACCENT,
                font_family="monospace",
                font_size="10px",
                letter_spacing="0.3em",
                text_transform="uppercase",
                margin_bottom="10px",
            ),

            rx.heading(
                "Claim your study OS.",
                color="white",
                font_size="42px",
                margin_bottom="36px",
            ),

            rx.vstack(
                field_label("Full Name"),
                text_input(
                    placeholder="Ada Lovelace",
                    value=UserState.signup_full_name,
                    on_change=UserState.set_signup_full_name,
                ),
                spacing="2",
                width="100%",
                align_items="start",
            ),

            rx.box(height="20px"),

            rx.vstack(
                field_label("SRN"),
                text_input(
                    placeholder="PES1UG25CS235",
                    value=UserState.signup_srn,
                    on_change=UserState.set_signup_srn,
                ),
                rx.text(
                    "format: PES1UG25CS235",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="10px",
                    align_self="start",
                ),
                spacing="2",
                width="100%",
                align_items="start",
            ),

            rx.box(height="20px"),

            rx.vstack(
                field_label("PESU Academy Password"),
                text_input(
                    placeholder="••••••••",
                    input_type="password",
                    value=UserState.signup_password,
                    on_change=UserState.set_signup_password,
                ),
                spacing="2",
                width="100%",
                align_items="start",
            ),

            rx.cond(
                UserState.signup_error != "",
                rx.text(
                    UserState.signup_error,
                    color="#EF4444",
                    font_family="monospace",
                    font_size="12px",
                    margin_top="12px",
                ),
            ),

            rx.box(height="28px"),

            primary_button(
                "Create account",
                on_click=UserState.handle_signup,
            ),

            rx.hstack(

                rx.link(
                    "→ Sign in instead",
                    href="/login",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="11px",
                ),

                rx.spacer(),

                rx.hstack(
                    rx.icon("lock", size=12, color=ACCENT),
                    rx.text(
                        "verified via PESU",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="10px",
                    ),
                    spacing="1",
                    align_items="center",
                ),

                width="100%",
                margin_top="20px",
            ),

            rx.divider(
                margin_y="34px",
                border_color=BORDER,
            ),

            rx.hstack(
                rx.icon("shield-check", size=14, color=ACCENT_LIGHT, margin_top="2px"),
                rx.text(
                    "Etude only accepts PESU SRNs (PES[1/2]UG__XX###). ",
                    rx.text.span(
                        "Your credentials are never used to access PESU Academy",
                        font_weight="700",
                        color="white",
                    ),
                    " — they're a local identity for ranking & sync.",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="10px",
                    line_height="1.8",
                ),
                align_items="start",
                spacing="2",
            ),

            width="520px",

        ),

        width="50%",
        height="100vh",
        bg="#000000",
        border_left="1px solid rgba(255,255,255,0.06)",
    )


def signup_page():
    return rx.hstack(

        left_panel(),

        signup_right_panel(),

        width="100%",
        height="100vh",
        spacing="0",
        bg="#000000",
    )
