"""Subjects grid — /resources/[semester]"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def filter_tab(label: str, value: str):
    active = ResourceState.filter_status == value
    return rx.box(
        label,
        on_click=lambda: ResourceState.set_filter(value),
        cursor="pointer",
        padding="8px 14px",
        font_family="monospace",
        font_size="11px",
        letter_spacing="0.1em",
        color=rx.cond(active, "white", ACCENT_LIGHT),
        bg=rx.cond(active, ACCENT, "transparent"),
        border=f"1px solid {BORDER}",
    )


def subject_card(subject: rx.Var):
    semester = ResourceState.router.page.params.get("semester", "1")
    return rx.link(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.cond(
                        subject["syllabus_status"] == "current",
                        "CURRENT",
                        "STALE SYLLABUS",
                    ),
                    border=f"1px solid {ACCENT}",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="10px",
                    padding="3px 8px",
                ),
                rx.spacer(),
                rx.icon("arrow-up-right", size=15, color=ACCENT_LIGHT),
                width="100%",
            ),
            rx.text(subject["subject_code"], color=ACCENT, font_family="monospace", font_size="12px", margin_top="20px"),
            rx.text(subject["subject_name"], color="white", font_family="'Space Grotesk', sans-serif",
                    font_weight="800", font_size="22px"),
            rx.hstack(
                rx.hstack(rx.icon("pencil", size=13, color=ACCENT_LIGHT),
                          rx.text(f"{subject['slide_count']} slides", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                          spacing="1"),
                rx.hstack(rx.icon("file-text", size=13, color=ACCENT_LIGHT),
                          rx.text(f"{subject['page_count']} pgs", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                          spacing="1"),
                spacing="4",
                margin_top="16px",
                border_top=f"1px solid {BORDER}",
                padding_top="16px",
                width="100%",
            ),
            align_items="start",
            width="100%",
        ),
        href=f"/resources/{semester}/{subject['subject_code']}",
        padding="24px",
        border=f"1px solid {BORDER}",
        _hover={"bg": "rgba(93,138,168,0.06)"},
        display="block",
    )


def subjects_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    return rx.box(

        topbar(breadcrumb=f"semester {semester}", active="resources", srn=UserState.srn),

        rx.box(

            rx.hstack(
                rx.vstack(
                    rx.text(f"// SEMESTER {semester}", color=ACCENT, font_family="monospace",
                            font_size="11px", letter_spacing="0.2em"),
                    rx.heading("Subjects.", color="white", font_family="'Space Grotesk', sans-serif",
                               font_weight="800", font_size="48px"),
                    rx.text(
                        f"{ResourceState.subjects.length()} subjects loaded · syllabus differentiator active",
                        color=ACCENT_LIGHT, font_size="15px",
                    ),
                    align_items="start",
                    spacing="2",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon("filter", size=14, color=ACCENT_LIGHT),
                    filter_tab("ALL", "all"),
                    filter_tab("CURRENT SYLLABUS", "current"),
                    filter_tab("STALE", "stale"),
                    spacing="2",
                    align_items="center",
                ),
                width="100%",
                align_items="start",
                padding="48px 48px 32px",
            ),

            rx.grid(
                rx.foreach(ResourceState.filtered_subjects, subject_card),
                columns="3",
                spacing="0",
                border_top=f"1px solid {BORDER}",
                border_left=f"1px solid {BORDER}",
                style={"& > a": {"border-right": f"1px solid {BORDER}", "border-bottom": f"1px solid {BORDER}"}},
                padding="0 48px 48px",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_subjects,
    )
