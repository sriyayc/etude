"""Subjects grid — /resources/[semester]."""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import ResourceState, UserState


ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def filter_tab(
    label: str,
    value: str,
) -> rx.Component:
    """Render one subject-filter tab."""

    active = ResourceState.filter_status == value

    return rx.box(
        label,
        on_click=ResourceState.set_filter(value),
        cursor="pointer",
        padding="8px 14px",
        font_family="monospace",
        font_size="11px",
        letter_spacing="0.1em",
        color=rx.cond(
            active,
            "white",
            ACCENT_LIGHT,
        ),
        background=rx.cond(
            active,
            ACCENT,
            "transparent",
        ),
        border=f"1px solid {BORDER}",
    )


def subject_card(subject: rx.Var) -> rx.Component:
    """Render one subject card."""

    return rx.link(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.cond(
                        subject["syllabus_status"]
                        == "current",
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
                rx.icon(
                    "arrow-up-right",
                    size=15,
                    color=ACCENT_LIGHT,
                ),
                width="100%",
            ),

            rx.text(
                subject["subject_code"],
                color=ACCENT,
                font_family="monospace",
                font_size="12px",
                margin_top="20px",
            ),

            rx.text(
                subject["subject_name"],
                color="white",
                font_family="'Space Grotesk', sans-serif",
                font_weight="800",
                font_size="22px",
            ),

            rx.hstack(
                rx.hstack(
                    rx.icon(
                        "pencil",
                        size=13,
                        color=ACCENT_LIGHT,
                    ),
                    rx.text(
                        subject["slide_count"],
                        " slides",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),
                    spacing="1",
                ),

                rx.hstack(
                    rx.icon(
                        "file-text",
                        size=13,
                        color=ACCENT_LIGHT,
                    ),
                    rx.text(
                        subject["page_count"],
                        " pgs",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),
                    spacing="1",
                ),

                spacing="4",
                margin_top="16px",
                border_top=f"1px solid {BORDER}",
                padding_top="16px",
                width="100%",
            ),

            align_items="start",
            width="100%",
        ),

        href=(
            "/resources/"
            + ResourceState.semester
            + "/"
            + subject["subject_code"]
        ),

        padding="24px",
        border=f"1px solid {BORDER}",
        _hover={
            "background": "rgba(93,138,168,0.06)",
        },
        display="block",
        text_decoration="none",
    )


def subjects_page() -> rx.Component:
    """Render subjects belonging to the selected semester."""

    return rx.box(
        topbar(
            breadcrumb=(
                "semester " + ResourceState.semester
            ),
            active="resources",
            srn=UserState.srn,
        ),

        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "// SEMESTER ",
                        ResourceState.semester,
                        color=ACCENT,
                        font_family="monospace",
                        font_size="11px",
                        letter_spacing="0.2em",
                    ),

                    rx.heading(
                        "Subjects.",
                        color="white",
                        font_family=(
                            "'Space Grotesk', sans-serif"
                        ),
                        font_weight="800",
                        font_size="48px",
                    ),

                    rx.text(
                        ResourceState.subjects.length(),
                        (
                            " subjects loaded · syllabus "
                            "differentiator active"
                        ),
                        color=ACCENT_LIGHT,
                        font_size="15px",
                    ),

                    rx.cond(
                        ResourceState.resource_error != "",
                        rx.text(
                            ResourceState.resource_error,
                            color="#FF8A8A",
                            font_family="monospace",
                            font_size="12px",
                        ),
                        rx.fragment(),
                    ),

                    align_items="start",
                    spacing="2",
                ),

                rx.spacer(),

                rx.hstack(
                    rx.icon(
                        "filter",
                        size=14,
                        color=ACCENT_LIGHT,
                    ),
                    filter_tab("ALL", "all"),
                    filter_tab(
                        "CURRENT SYLLABUS",
                        "current",
                    ),
                    filter_tab("STALE", "stale"),
                    spacing="2",
                    align_items="center",
                ),

                width="100%",
                align_items="start",
                padding="48px 48px 32px",
            ),

            rx.cond(
                ResourceState.filtered_subjects.length()
                > 0,
                rx.grid(
                    rx.foreach(
                        ResourceState.filtered_subjects,
                        subject_card,
                    ),
                    columns="3",
                    spacing="0",
                    border_top=f"1px solid {BORDER}",
                    border_left=f"1px solid {BORDER}",
                    style={
                        "& > a": {
                            "border-right": (
                                f"1px solid {BORDER}"
                            ),
                            "border-bottom": (
                                f"1px solid {BORDER}"
                            ),
                        }
                    },
                    padding="0 48px 48px",
                ),
                rx.center(
                    rx.text(
                        "No subjects found for this semester.",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="13px",
                    ),
                    min_height="240px",
                ),
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        background=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_subjects,
    )