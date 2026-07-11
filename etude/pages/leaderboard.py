"""Leaderboard page — podium + full ranked table, real data."""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PODIUM_BG = "#0A2647"


def podium_card(row: rx.Var):
    return rx.vstack(
        rx.icon("trophy", size=26, color=ACCENT_LIGHT),
        rx.text(f"#{row['rank']}", color="white", font_family="'Space Grotesk', sans-serif",
                font_weight="800", font_size="40px"),
        rx.text(row["full_name"], color="white", font_weight="600", font_size="16px"),
        rx.text(row["srn"], color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
        rx.text(f"{row['points']} pts", color=ACCENT_LIGHT, font_family="monospace", font_size="13px"),
        bg=PODIUM_BG,
        padding="32px",
        spacing="1",
        align_items="center",
        flex="1",
        border_right=f"1px solid {BORDER}",
    )


def table_row(row: rx.Var):
    is_you = row["srn"] == UserState.srn
    return rx.hstack(
        rx.text(f"#{row['rank']}", color="white", font_family="monospace", font_size="13px", width="60px"),
        rx.hstack(
            rx.text(row["full_name"], color="white", font_size="14px"),
            rx.cond(
                is_you,
                rx.box("YOU", bg=ACCENT, color="black", font_family="monospace",
                       font_size="10px", font_weight="700", padding="2px 6px"),
            ),
            spacing="2",
            width="240px",
        ),
        rx.text(row["srn"], color=ACCENT_LIGHT, font_family="monospace", font_size="13px", flex="1"),
        rx.text(row["points"], color="white", font_weight="700", font_size="14px", width="80px", text_align="right"),
        rx.hstack(
            rx.icon("flame", size=13, color=ACCENT_LIGHT),
            rx.text(f"{row['streak']}d", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
            spacing="1",
            width="70px",
            justify_content="end",
        ),
        width="100%",
        padding="16px 20px",
        border_bottom=f"1px solid {BORDER}",
        border_left=rx.cond(is_you, f"3px solid {ACCENT}", "3px solid transparent"),
        bg=rx.cond(is_you, "rgba(93,138,168,0.08)", "transparent"),
        align_items="center",
    )


def leaderboard_page():
    return rx.box(

        topbar(breadcrumb="leaderboard", active="leaderboard", srn=UserState.srn),

        rx.box(

            rx.hstack(
                rx.vstack(
                    rx.text(
                        "// RANK UP · SYLLABUS QUIZZES",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="11px",
                        letter_spacing="0.2em",
                    ),
                    rx.heading(
                        "Leaderboard.",
                        color="white",
                        font_family="'Space Grotesk', sans-serif",
                        font_weight="800",
                        font_size="52px",
                    ),
                    align_items="start",
                    spacing="2",
                ),

                rx.spacer(),

                rx.text(
                    "weekly · resets monday 00:00 IST",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="12px",
                ),

                width="100%",
                align_items="start",
                padding="60px 48px 40px",
            ),

            rx.hstack(
                rx.foreach(UserState.leaderboard_rows[:3], podium_card),
                spacing="0",
                border=f"1px solid {BORDER}",
                margin="0 48px",
            ),

            rx.vstack(
                rx.hstack(
                    rx.text("RANK", color=ACCENT, font_family="monospace", font_size="11px", width="60px"),
                    rx.text("NAME", color=ACCENT, font_family="monospace", font_size="11px", width="240px"),
                    rx.text("SRN", color=ACCENT, font_family="monospace", font_size="11px", flex="1"),
                    rx.text("POINTS", color=ACCENT, font_family="monospace", font_size="11px", width="80px", text_align="right"),
                    rx.text("STREAK", color=ACCENT, font_family="monospace", font_size="11px", width="70px", text_align="right"),
                    width="100%",
                    padding="12px 20px",
                    border_bottom=f"1px solid {BORDER}",
                ),
                rx.foreach(UserState.leaderboard_rows, table_row),
                width="100%",
                margin="24px 48px 0",
                spacing="0",
            ),

            rx.text(
                "↑ complete quizzes to climb · +100 pts per correct answer · streak doubles weekly bonus",
                color=ACCENT_LIGHT,
                font_family="monospace",
                font_size="12px",
                padding="24px 48px 60px",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
    )
