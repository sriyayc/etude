"""Dashboard — 'Choose a semester' page."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import UserState
from etude.styles import theme as t

# Semesters 7 and 8 are capstone/internship only -- no coursework syllabus to
# browse, so they are deliberately not listed.
SEMESTERS = [1, 2, 3, 4, 5, 6]


def semester_tile(number: int):
    return rx.link(
        ui.card(
            rx.hstack(
                ui.badge(f"Semester {number}", tone="accent"),
                rx.spacer(),
                rx.box(
                    rx.icon("arrow-up-right", size=18, color=t.ACCENT_STRONG),
                    class_name="tile-arrow",
                    opacity="0.55",
                    transition="opacity .18s ease, transform .18s ease",
                ),
                width="100%",
                align_items="center",
            ),
            rx.text(
                str(number),
                color=t.ACCENT,
                font_family=t.FONT_DISPLAY,
                font_weight="700",
                font_size="72px",
                line_height="1",
                margin_top="18px",
                class_name="tile-number",
                transition="color .18s ease",
            ),
            rx.text(
                "View subjects",
                color=t.TEXT_MUTED,
                font_size="13px",
                font_weight="500",
                margin_top="10px",
            ),
            hover=True,
            height="200px",
            padding="22px",
            _hover={
                "box_shadow": t.SHADOW_HOVER,
                "transform": "translateY(-3px)",
                "border_color": t.ACCENT,
                "& .tile-number": {"color": t.ACCENT_STRONG},
                "& .tile-arrow": {"opacity": "1", "transform": "translate(2px,-2px)"},
            },
        ),
        href=f"/resources/{number}",
        display="block",
        text_decoration="none",
    )


def stat_tile(icon: str, label: str, value, sub) -> rx.Component:
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
                rx.text(
                    value,
                    color=t.TEXT,
                    font_family=t.FONT_DISPLAY,
                    font_weight="700",
                    font_size="26px",
                    line_height="1.1",
                ),
                rx.text(sub, color=t.TEXT_MUTED, font_size="12px"),
                align_items="start",
                spacing="0",
            ),
            spacing="3",
            align_items="center",
        ),
        padding="18px 20px",
    )


def dashboard_page():
    return ui.page(
        topbar(breadcrumb="Resources", active="resources", srn=UserState.srn),
        ui.container(
            rx.hstack(
                rx.vstack(
                    ui.eyebrow("Welcome back"),
                    ui.heading("Choose a semester", size="42px", margin_top="8px"),
                    ui.subtext(
                        "Slides, textbook and an AI tutor for every unit — all in one place.",
                        margin_top="8px",
                    ),
                    align_items="start",
                    spacing="0",
                ),
                rx.spacer(),
                rx.vstack(
                    ui.badge(UserState.srn, tone="muted", font_family=t.FONT_MONO),
                    align_items="end",
                    spacing="1",
                    display=["none", "none", "flex"],
                ),
                width="100%",
                align_items="center",
                margin_bottom="28px",
            ),

            rx.grid(
                *[semester_tile(n) for n in SEMESTERS],
                columns=rx.breakpoints(initial="2", lg="4"),
                spacing="4",
            ),

            rx.grid(
                stat_tile("trophy", "Your rank", f"#{UserState.rank}", "class leaderboard"),
                stat_tile("sparkles", "Points", UserState.points, "keep it up"),
                stat_tile("flame", "Streak", f"{UserState.streak} days", "current streak"),
                columns=rx.breakpoints(initial="1", lg="3"),
                spacing="4",
                margin_top="28px",
            ),
        ),
    )
