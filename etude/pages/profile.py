"""Profile page — student record, stats, activity, syllabus tracker."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import UserState
from etude.styles import theme as t

# NOTE: these two feeds are still mock/static — no schema field tracks a
# merged "recent activity" feed or per-topic completion %. Kept (not deleted)
# and restyled; flagged to wire up to real data later.
ACTIVITY = [
    ("Submitted quiz · DBMS · 4/5", "2h ago"),
    ("Asked AI · OS · 6 citations", "yesterday"),
    ("Flashcards reviewed · ML · 18 cards", "yesterday"),
    ("Climbed to rank #6", "2d ago"),
]

TRACKER = [
    ("Computer Networks · Unit 3", 78),
    ("Machine Learning · Unit 2", 54),
    ("Software Engineering · Unit 1", 91),
]


def stat_tile(icon: str, label: str, value, sub: str):
    return ui.card(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=20, color=t.ACCENT_STRONG),
                background=t.ACCENT_SOFT,
                border_radius=t.RADIUS_SM,
                padding="10px",
                display="flex",
            ),
            rx.vstack(
                rx.text(label, color=t.TEXT_MUTED, font_size="13px", font_weight="500"),
                rx.text(value, color=t.TEXT, font_family=t.FONT_DISPLAY, font_weight="700", font_size="24px", line_height="1.1"),
                rx.text(sub, color=t.TEXT_MUTED, font_size="12px"),
                spacing="0",
                align_items="start",
            ),
            spacing="3",
            align_items="center",
        ),
        padding="18px 20px",
    )


def empty_hint(text: str):
    return rx.text(text, color=t.TEXT_MUTED, font_size="13px", padding="12px 0")


def activity_row(text, when):
    return rx.hstack(
        rx.box(width="7px", height="7px", border_radius=t.RADIUS_PILL, background=t.ACCENT),
        rx.text(text, color=t.TEXT_BODY, font_size="14px"),
        rx.spacer(),
        rx.text(when, color=t.TEXT_MUTED, font_size="12px"),
        width="100%",
        padding="12px 0",
        border_bottom=f"1px solid {t.BORDER}",
        align_items="center",
        spacing="3",
    )


def tracker_row(label, pct):
    return rx.vstack(
        rx.hstack(
            rx.text(label, color=t.TEXT_BODY, font_size="14px"),
            rx.spacer(),
            rx.text(pct.to_string() + "%", color=t.ACCENT_STRONG, font_size="13px", font_weight="600"),
            width="100%",
        ),
        rx.box(
            rx.box(width=pct.to_string() + "%", height="100%", bg=t.ACCENT, border_radius=t.RADIUS_PILL),
            width="100%",
            height="7px",
            bg=t.BG_SUBTLE,
            border_radius=t.RADIUS_PILL,
            margin_top="8px",
        ),
        width="100%",
        padding="10px 0",
        align_items="start",
        spacing="0",
    )


def profile_page():
    return ui.page(
        topbar(breadcrumb="Profile", srn=UserState.srn),
        ui.container(
            ui.card(
                rx.hstack(
                    rx.box(
                        rx.cond(
                            UserState.full_name != "",
                            UserState.full_name[0:2].upper(),
                            "—",
                        ),
                        background=t.ACCENT,
                        color=t.ACCENT_TEXT_ON,
                        font_family=t.FONT_DISPLAY,
                        font_weight="700",
                        font_size="24px",
                        width="66px",
                        height="66px",
                        border_radius=t.RADIUS_PILL,
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text(UserState.full_name, color=t.TEXT, font_family=t.FONT_DISPLAY, font_weight="700", font_size="24px"),
                        rx.text(UserState.srn, color=t.TEXT_MUTED, font_family=t.FONT_MONO, font_size="13px"),
                        align_items="start",
                        spacing="1",
                    ),
                    rx.spacer(),
                    ui.ghost_button("Sign out", icon="log-out", on_click=UserState.logout),
                    width="100%",
                    align_items="center",
                ),
            ),

            rx.grid(
                stat_tile("trophy", "Current rank", "#" + UserState.rank.to_string(), UserState.points.to_string() + " pts"),
                stat_tile("flame", "Streak", UserState.streak.to_string() + "d", "current streak"),
                stat_tile("book", "Active subjects", UserState.subjects_active, "this semester"),
                stat_tile("clock", "Hours studied", "—", "not tracked yet"),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                spacing="4",
                margin_top="20px",
            ),

            rx.grid(
                ui.card(
                    rx.text("Recent activity", color=t.TEXT, font_weight="600", font_size="16px", margin_bottom="8px"),
                    rx.cond(
                        UserState.activity_rows.length() > 0,
                        rx.foreach(
                            UserState.activity_rows,
                            lambda a: activity_row(a["label"], a["when"]),
                        ),
                        empty_hint("No activity yet — take a quiz to get started."),
                    ),
                ),
                ui.card(
                    rx.text("Syllabus tracker", color=t.TEXT, font_weight="600", font_size="16px", margin_bottom="8px"),
                    rx.cond(
                        UserState.tracker_rows.length() > 0,
                        rx.foreach(
                            UserState.tracker_rows,
                            lambda tr: tracker_row(tr["label"], tr["pct"]),
                        ),
                        empty_hint("Your best quiz score per unit will show up here."),
                    ),
                ),
                columns=rx.breakpoints(initial="1", lg="2"),
                spacing="4",
                margin_top="20px",
            ),
        ),
    )
