import reflex as rx

from etude.components.button import primary_button
from etude.components.input import text_input
from etude.state import UserState


ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def stat_card(title: str, value: str):
    return rx.box(
        rx.text(
            title,
            font_size="9px",
            text_transform="uppercase",
            letter_spacing="0.25em",
            color=ACCENT,
            font_family="monospace",
        ),
        rx.text(
            value,
            color="white",
            font_size="12px",
            margin_top="6px",
            font_family="monospace",
        ),
        bg=BACKGROUND,
        padding="14px",
        border=f"1px solid {BORDER}",
    )


def left_panel():

    return rx.box(

        rx.image(
            src="https://images.pexels.com/photos/8452381/pexels-photo-8452381.jpeg",
            position="absolute",
            inset="0",
            width="100%",
            height="100%",
            object_fit="cover",
            opacity="0.65",
        ),

        rx.box(
            position="absolute",
            inset="0",
            background="""
            linear-gradient(
                135deg,
                rgba(0,0,0,.95),
                rgba(0,33,71,.82),
                rgba(31,58,61,.65)
            )
            """,
        ),

        rx.box(
            position="absolute",
            inset="0",
            background_image="url('/grid.svg')",
            background_repeat="repeat",
            opacity="0.18",
        ),

        rx.vstack(

            rx.vstack(
                rx.image(
                    src="/logo.png",
                    height="52px",
                    width="auto",
                ),

                rx.text(
                    "PESU · syllabus-bound AI",
                    color=ACCENT,
                    font_size="10px",
                    letter_spacing="0.3em",
                    text_transform="uppercase",
                    margin_top="-6px",
                ),

                spacing="1",
                align_items="start",
            ),

            rx.spacer(),

            rx.vstack(

                rx.text(
                    "// a study OS for PESU",
                    color=ACCENT,
                    font_size="10px",
                    letter_spacing="0.3em",
                    text_transform="uppercase",
                    font_family="monospace",
                ),

                rx.heading(
                    rx.fragment(
                        "stop switching between ",
                        rx.text.span(
                            "slides",
                            color=ACCENT,
                        ),
                        " & ",
                        rx.text.span(
                            "textbooks",
                            color=ACCENT_LIGHT,
                        ),
                        ".",
                    ),
                    color="white",
                    font_size="60px",
                    font_weight="800",
                    line_height="0.95",
                    max_width="620px",

                ),

                rx.text(
                    "Etude compiles your unit's slides and textbook into one queryable surface. "
                    "The AI answers only from your syllabus while citing every page.",
                    color=ACCENT_LIGHT,
                    font_size="16px",
                    max_width="620px",
                    line_height="1.5",
                ),

                rx.grid(

                    stat_card(
                        "RAG",
                        "syllabus-bound",
                    ),

                    stat_card(
                        "CITATIONS",
                        "always-on",
                    ),

                    stat_card(
                        "QUIZZES",
                        "auto-generated",
                    ),

                    stat_card(
                        "RANK",
                        "leaderboard",
                    ),

                    columns="2",
                    spacing="1",
                    width="360px",
                    margin_top="12px",
                ),

                spacing="3",
                align_items="start",
            ),

            rx.text(
                "© 2026 ETUDE · Built for PES University",
                color=ACCENT,
                font_size="10px",
                font_family="monospace",
                margin_top="14px",
            ),

            width="100%",
            min_height="100%",
            padding="24px 48px 32px",
            align_items="start",
            # FIX 1: without this, the absolute-positioned image/gradient/grid
            # boxes above paint ON TOP of this text (CSS paints positioned
            # elements after static ones, regardless of source order).
            position="relative",
            z_index="1",
            overflow_y="auto",
        ),

        position="relative",
        width="50%",
        height="100vh",
        display=["none", "none", "flex", "flex"],
        overflow="hidden",
    )
def right_panel():
    return rx.center(

        rx.box(

            rx.text(
                "// PESU Academy Sign In",
                color=ACCENT,
                font_family="monospace",
                font_size="10px",
                letter_spacing="0.3em",
                text_transform="uppercase",
                margin_bottom="10px",
            ),

            rx.heading(
                # FIX 2: was hardcoded "Sign in to ETUDE." — lowercase to match brand
                "Sign in to etude.",
                color="white",
                font_size="42px",
                margin_bottom="36px",
            ),

            rx.vstack(

                rx.text(
                    "SRN",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="10px",
                    letter_spacing="0.2em",
                    text_transform="uppercase",
                    align_self="start",
                ),

                text_input(
                    placeholder="PES2UG24CS510",
                    value=UserState.login_srn,
                    on_change=UserState.set_login_srn,
                ),

                rx.text(
                    "Format: PES2UG24CS510",
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

                rx.text(
                    "Password",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="10px",
                    letter_spacing="0.2em",
                    text_transform="uppercase",
                    align_self="start",
                ),

                text_input(
                    placeholder="••••••••",
                    input_type="password",
                    value=UserState.login_password,
                    on_change=UserState.set_login_password,
                ),

                spacing="2",
                width="100%",
                align_items="start",
            ),

            rx.cond(
                UserState.login_error != "",
                rx.text(
                    UserState.login_error,
                    color="#EF4444",
                    font_family="monospace",
                    font_size="12px",
                    margin_top="12px",
                ),
            ),

            rx.box(height="28px"),

            # FIX 3: was primary_button("Sign In →") — primary_button already
            # appends its own arrow-right icon, so this caused a double arrow.
            primary_button(
                "Sign In",
                on_click=UserState.handle_login,
            ),

            rx.hstack(

                rx.link(
                    "→ Create account",
                    href="/signup",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="11px",
                ),

                rx.spacer(),

                # FIX 5: added icon + lowercased to match reference ("verified via PESU")
                rx.hstack(
                    rx.icon("shield", size=13, color=ACCENT),
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

            # FIX 6: added shield icon + bolded clause, restored second line
            rx.hstack(
                rx.icon("shield-check", size=14, color=ACCENT_LIGHT, margin_top="2px"),
                rx.text(
                    "Etude only accepts PESU SRNs. ",
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
def login_page():

    return rx.hstack(

        left_panel(),

        right_panel(),

        width="100%",
        height="100vh",
        spacing="0",
        bg="#000000",
    )
