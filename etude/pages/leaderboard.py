"""Leaderboard page — podium + full ranked table, real data."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import UserState
from etude.styles import theme as t


def podium_card(row: rx.Var, idx: int):
    accent = rx.match(
        idx,
        (0, "#E7B23D"),
        (1, "#9AA7B2"),
        (2, "#C08552"),
        t.ACCENT_STRONG,
    )
    return ui.card(
        rx.vstack(
            rx.box(
                rx.icon("trophy", size=22, color=accent),
                background=t.ACCENT_SOFT,
                border_radius=t.RADIUS_PILL,
                padding="12px",
                display="flex",
            ),
            rx.text(
                "#" + row["rank"].to_string(),
                color=t.TEXT,
                font_family=t.FONT_DISPLAY,
                font_weight="700",
                font_size="34px",
            ),
            rx.text(row["full_name"], color=t.TEXT, font_weight="600", font_size="16px"),
            rx.text(row["srn"], color=t.TEXT_MUTED, font_family=t.FONT_MONO, font_size="12px"),
            ui.badge(row["points"].to_string() + " pts", tone="accent"),
            spacing="2",
            align_items="center",
        ),
        flex="1",
        padding="28px 20px",
    )


def table_row(row: rx.Var):
    is_you = row["srn"] == UserState.srn
    return rx.hstack(
        rx.text("#" + row["rank"].to_string(), color=t.TEXT_BODY, font_family=t.FONT_MONO, font_size="14px", width="56px"),
        rx.hstack(
            rx.text(row["full_name"], color=t.TEXT, font_size="14px", font_weight="500"),
            rx.cond(is_you, ui.badge("You", tone="accent"), rx.fragment()),
            spacing="2",
            width="240px",
            align_items="center",
        ),
        rx.text(row["srn"], color=t.TEXT_MUTED, font_family=t.FONT_MONO, font_size="13px", flex="1"),
        rx.text(row["points"], color=t.TEXT, font_weight="700", font_size="14px", width="80px", text_align="right"),
        rx.hstack(
            rx.icon("flame", size=14, color=t.TEXT_MUTED),
            rx.text(row["streak"].to_string() + "d", color=t.TEXT_MUTED, font_size="13px"),
            spacing="1",
            width="70px",
            justify_content="end",
            align_items="center",
        ),
        width="100%",
        padding="14px 20px",
        border_bottom=f"1px solid {t.BORDER}",
        background=rx.cond(is_you, t.ACCENT_SOFT, "transparent"),
        align_items="center",
    )


def leaderboard_page():
    return ui.page(
        topbar(breadcrumb="Leaderboard", active="leaderboard", srn=UserState.srn),
        ui.container(
            rx.hstack(
                rx.vstack(
                    ui.eyebrow("Syllabus quizzes"),
                    ui.heading("Leaderboard", size="38px", margin_top="6px"),
                    align_items="start",
                    spacing="0",
                ),
                rx.spacer(),
                ui.badge("Weekly · resets Monday", tone="muted"),
                width="100%",
                align_items="center",
                margin_bottom="28px",
            ),

            rx.grid(
                rx.foreach(
                    UserState.leaderboard_rows[:3],
                    lambda row, idx: podium_card(row, idx),
                ),
                columns=rx.breakpoints(initial="1", sm="3"),
                spacing="4",
            ),

            ui.card(
                rx.hstack(
                    rx.text("Rank", color=t.TEXT_MUTED, font_size="12px", font_weight="600", width="56px"),
                    rx.text("Name", color=t.TEXT_MUTED, font_size="12px", font_weight="600", width="240px"),
                    rx.text("SRN", color=t.TEXT_MUTED, font_size="12px", font_weight="600", flex="1"),
                    rx.text("Points", color=t.TEXT_MUTED, font_size="12px", font_weight="600", width="80px", text_align="right"),
                    rx.text("Streak", color=t.TEXT_MUTED, font_size="12px", font_weight="600", width="70px", text_align="right"),
                    width="100%",
                    padding="14px 20px",
                    border_bottom=f"1px solid {t.BORDER}",
                ),
                rx.foreach(UserState.leaderboard_rows, table_row),
                padding="0",
                overflow="hidden",
                margin_top="24px",
            ),

            rx.text(
                "Complete quizzes to climb — +100 pts per correct answer, and streaks boost your weekly bonus.",
                color=t.TEXT_MUTED,
                font_size="13px",
                margin_top="20px",
            ),
        ),
    )
