"""Dashboard — 'Choose a semester' page."""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"

SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

# NOTE: "compiled notes" and "slides ingested" aren't per-user schema
# fields yet (they'd come from a documents/ingestion pipeline that
# doesn't exist in your current tables) — still static placeholders.
STATIC_STATS = [
    ("COMPILED NOTES", "312", "pages indexed"),
    ("SLIDES INGESTED", "1,824", "across 32 subjects"),
]


def semester_tile(number: int):
    return rx.link(
        rx.box(
        rx.hstack(
            rx.text(
                f"SEM {number:02d}",
                color=ACCENT,
                font_family="monospace",
                font_size="11px",
                letter_spacing="0.15em",
                class_name="tile-label",
            ),
            rx.spacer(),
            rx.icon("arrow-up-right", size=16, color=ACCENT_LIGHT),
            width="100%",
        ),
        rx.text(
            str(number),
            color="#12262b",
            font_family="'Space Grotesk', sans-serif",
            font_weight="800",
            font_size="120px",
            line_height="1",
            margin_top="30px",
            class_name="tile-number",
        ),
        rx.text(
            f"→ SEMESTER {number}",
            color=ACCENT_LIGHT,
            font_family="monospace",
            font_size="12px",
            class_name="tile-reveal",
            opacity="0",
            position="absolute",
            bottom="24px",
            left="24px",
            transition="opacity .2s ease",
        ),
        padding="24px",
        height="220px",
        border=f"1px solid {BORDER}",
        cursor="pointer",
        overflow="hidden",
        position="relative",
        transition="background .2s ease",
        _hover={
            "bg": "#0A2647",
            "& .tile-number": {"color": "#1E4A6B"},
            "& .tile-reveal": {"opacity": "1"},
        },
        ),
        href=f"/resources/{number}",
        display="block",
    )


def stat_block(label: str, value: str, sub: str):
    return rx.vstack(
        rx.text(
            label,
            color=ACCENT,
            font_family="monospace",
            font_size="11px",
            letter_spacing="0.15em",
        ),
        rx.text(
            value,
            color="white",
            font_family="'Space Grotesk', sans-serif",
            font_weight="800",
            font_size="34px",
        ),
        rx.text(
            sub,
            color=ACCENT_LIGHT,
            font_family="monospace",
            font_size="12px",
        ),
        align_items="start",
        spacing="1",
        padding="0 32px",
        border_left=f"1px solid {BORDER}",
        height="100%",
        justify_content="center",
    )


def dashboard_page():
    return rx.box(

        topbar(breadcrumb="resources", active="resources", srn=UserState.srn),

        rx.box(

            rx.hstack(
                rx.vstack(
                    rx.text(
                        "// HELLO, BATCH 24",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="11px",
                        letter_spacing="0.2em",
                    ),
                    rx.heading(
                        "Choose a semester.",
                        color="white",
                        font_family="'Space Grotesk', sans-serif",
                        font_weight="800",
                        font_size="52px",
                    ),
                    rx.text(
                        "Eight semesters. Compiled slides + textbook + AI tutor in one surface.",
                        color=ACCENT_LIGHT,
                        font_size="16px",
                        margin_top="8px",
                    ),
                    align_items="start",
                    spacing="2",
                ),

                rx.spacer(),

                rx.vstack(
                    rx.text(
                        UserState.srn,
                        color="white",
                        font_family="monospace",
                        font_size="13px",
                    ),
                    rx.text(
                        "8 units · syllabus-bound",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),
                    align_items="end",
                    spacing="1",
                ),

                width="100%",
                align_items="start",
                padding="60px 48px 40px",
            ),

            rx.grid(
                *[semester_tile(n) for n in SEMESTERS],
                columns="4",
                spacing="0",
                border_top=f"1px solid {BORDER}",
                border_left=f"1px solid {BORDER}",
                style={
                    "& > div": {
                        "border-right": f"1px solid {BORDER}",
                        "border-bottom": f"1px solid {BORDER}",
                    }
                },
                padding="0 48px",
            ),

            rx.hstack(
                *[stat_block(*s) for s in STATIC_STATS],
                rx.vstack(
                    rx.text(
                        "YOUR RANK",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="11px",
                        letter_spacing="0.15em",
                    ),
                    rx.text(
                        f"#{UserState.rank}",
                        color="white",
                        font_family="'Space Grotesk', sans-serif",
                        font_weight="800",
                        font_size="34px",
                    ),
                    rx.text(
                        f"{UserState.points} pts · {UserState.streak} day streak",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),
                    align_items="start",
                    spacing="1",
                    padding="0 32px",
                    border_left=f"1px solid {BORDER}",
                    height="100%",
                    justify_content="center",
                ),
                width="100%",
                padding="40px 48px 60px",
                height="100px",
                margin_top="20px",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
    )
