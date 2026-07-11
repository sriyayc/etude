"""Profile page — student record, stats, activity, syllabus tracker."""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PANEL_BG = "#0A1A24"

# NOTE: these two are still mock/static — no schema field tracks
# "recent activity" as a merged feed (would need combining
# quiz_attempts + query_logs by timestamp) or per-topic completion %
# for the syllabus tracker. Flagged, not yet wired to real data.
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
    ("Compiler Design (stale) · skip", 0),
]


def stat_card(icon: str, label: str, value: str, sub: str):
    return rx.vstack(
        rx.icon(icon, size=16, color=ACCENT_LIGHT),
        rx.text(label, color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.1em"),
        rx.text(value, color="white", font_family="'Space Grotesk', sans-serif",
                font_weight="800", font_size="30px"),
        rx.text(sub, color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
        align_items="start",
        spacing="1",
        padding="20px",
        border=f"1px solid {BORDER}",
        flex="1",
    )


def activity_row(text: str, when: str):
    return rx.hstack(
        rx.text(text, color="white", font_size="14px"),
        rx.spacer(),
        rx.text(when, color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
        width="100%",
        padding="14px 0",
        border_bottom=f"1px solid {BORDER}",
    )


def tracker_row(label: str, pct: int):
    return rx.vstack(
        rx.hstack(
            rx.text(label, color="white", font_size="14px"),
            rx.spacer(),
            rx.text(f"{pct}%", color=ACCENT, font_family="monospace", font_size="12px"),
            width="100%",
        ),
        rx.box(
            rx.box(width=f"{pct}%", height="100%", bg=ACCENT),
            width="100%",
            height="4px",
            bg=BORDER,
            margin_top="8px",
        ),
        width="100%",
        padding="14px 0",
        align_items="start",
    )


def profile_page():
    return rx.box(

        topbar(breadcrumb="profile", srn=UserState.srn),

        rx.box(

            rx.text(
                "// STUDENT RECORD",
                color=ACCENT,
                font_family="monospace",
                font_size="11px",
                letter_spacing="0.2em",
                padding="40px 48px 0",
            ),

            rx.box(

                rx.hstack(
                    rx.box(
                        rx.cond(
                            UserState.full_name != "",
                            UserState.full_name[0:2].upper(),
                            "—",
                        ),
                        bg=PANEL_BG,
                        border=f"1px solid {BORDER}",
                        color="white",
                        font_family="'Space Grotesk', sans-serif",
                        font_weight="800",
                        font_size="24px",
                        width="72px",
                        height="72px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text(UserState.full_name, color="white", font_family="'Space Grotesk', sans-serif",
                                font_weight="800", font_size="26px"),
                        rx.text(UserState.srn, color=ACCENT_LIGHT, font_family="monospace", font_size="13px"),
                        align_items="start",
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.icon("log-out", size=14, color=ACCENT_LIGHT),
                        rx.text("SIGN OUT", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                        on_click=UserState.logout,
                        cursor="pointer",
                        spacing="2",
                        border=f"1px solid {BORDER}",
                        padding="10px 16px",
                    ),
                    width="100%",
                    align_items="center",
                    padding="28px",
                ),

                rx.hstack(
                    rx.vstack(
                        rx.icon("trophy", size=16, color=ACCENT_LIGHT),
                        rx.text("CURRENT RANK", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.1em"),
                        rx.text(f"#{UserState.rank}", color="white", font_family="'Space Grotesk', sans-serif",
                                font_weight="800", font_size="30px"),
                        rx.text(f"{UserState.points} pts", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                        align_items="start", spacing="1", padding="20px", border=f"1px solid {BORDER}", flex="1",
                    ),
                    rx.vstack(
                        rx.icon("flame", size=16, color=ACCENT_LIGHT),
                        rx.text("STREAK", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.1em"),
                        rx.text(f"{UserState.streak}d", color="white", font_family="'Space Grotesk', sans-serif",
                                font_weight="800", font_size="30px"),
                        rx.text("current streak", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                        align_items="start", spacing="1", padding="20px", border=f"1px solid {BORDER}", flex="1",
                    ),
                    rx.vstack(
                        rx.icon("book", size=16, color=ACCENT_LIGHT),
                        rx.text("SUBJECTS ACTIVE", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.1em"),
                        rx.text(f"{UserState.subjects_active}", color="white", font_family="'Space Grotesk', sans-serif",
                                font_weight="800", font_size="30px"),
                        rx.text("this sem", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                        align_items="start", spacing="1", padding="20px", border=f"1px solid {BORDER}", flex="1",
                    ),
                    rx.vstack(
                        rx.icon("clock", size=16, color=ACCENT_LIGHT),
                        rx.text("HOURS STUDIED", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.1em"),
                        # NOTE: no table tracks study duration yet — honest
                        # placeholder shown to every user until that's built,
                        # rather than a fake per-user number.
                        rx.text("—", color="white", font_family="'Space Grotesk', sans-serif",
                                font_weight="800", font_size="30px"),
                        rx.text("not tracked yet", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                        align_items="start", spacing="1", padding="20px", border=f"1px solid {BORDER}", flex="1",
                    ),
                    spacing="0",
                    width="100%",
                ),

                bg="rgba(93,138,168,0.06)",
                border=f"1px solid {BORDER}",
                margin="20px 48px 0",
            ),

            rx.hstack(

                rx.vstack(
                    rx.text("RECENT ACTIVITY", color=ACCENT, font_family="monospace",
                            font_size="11px", letter_spacing="0.15em", margin_bottom="8px"),
                    *[activity_row(*a) for a in ACTIVITY],
                    align_items="start",
                    width="100%",
                    flex="1",
                ),

                rx.vstack(
                    rx.text("SYLLABUS TRACKER", color=ACCENT, font_family="monospace",
                            font_size="11px", letter_spacing="0.15em", margin_bottom="8px"),
                    *[tracker_row(*t) for t in TRACKER],
                    align_items="start",
                    width="100%",
                    flex="1",
                ),

                spacing="8",
                width="100%",
                align_items="start",
                padding="48px",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
    )
