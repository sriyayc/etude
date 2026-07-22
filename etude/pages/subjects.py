"""Subjects grid — /resources/[semester]."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import ResourceState, UserState
from etude.styles import theme as t


def filter_tab(label: str, value: str) -> rx.Component:
    active = ResourceState.filter_status == value
    return rx.box(
        label,
        on_click=ResourceState.set_filter(value),
        cursor="pointer",
        padding="7px 14px",
        font_size="13px",
        font_weight="600",
        border_radius=t.RADIUS_PILL,
        color=rx.cond(active, t.ACCENT_TEXT_ON, t.TEXT_BODY),
        background=rx.cond(active, t.ACCENT, t.BG_CARD),
        border=f"1px solid {rx.cond(active, t.ACCENT, t.BORDER)}",
        transition="all .15s ease",
    )


def subject_card(subject: rx.Var) -> rx.Component:
    return rx.link(
        ui.card(
            rx.hstack(
                ui.badge(
                    rx.cond(
                        subject["syllabus_status"] == "current",
                        "Current",
                        "Stale syllabus",
                    ),
                    background=rx.cond(
                        subject["syllabus_status"] == "current",
                        t.SUCCESS_SOFT, t.BG_SUBTLE,
                    ),
                    color=rx.cond(
                        subject["syllabus_status"] == "current",
                        t.SUCCESS, t.TEXT_MUTED,
                    ),
                ),
                rx.spacer(),
                rx.icon("arrow-up-right", size=17, color=t.TEXT_MUTED),
                width="100%",
                align_items="center",
            ),
            rx.text(
                subject["subject_name"],
                color=t.TEXT,
                font_family=t.FONT_DISPLAY,
                font_weight="700",
                font_size="19px",
                line_height="1.25",
                margin_top="4px",
            ),
            rx.hstack(
                rx.text(
                    "Open",
                    color=t.ACCENT_STRONG,
                    font_size="13px",
                    font_weight="600",
                ),
                rx.icon("arrow-right", size=15, color=t.ACCENT_STRONG),
                spacing="1",
                align_items="center",
                margin_top="18px",
                padding_top="16px",
                border_top=f"1px solid {t.BORDER}",
                width="100%",
            ),
            hover=True,
            height="100%",
            display="flex",
            flex_direction="column",
        ),
        href=f"/resources/{ResourceState.semester}/{subject['slug']}",
        display="block",
        text_decoration="none",
        height="100%",
    )


def subjects_page() -> rx.Component:
    return ui.page(
        topbar(
            trail=[
                ("Resources", "/dashboard"),
                ("Semester " + ResourceState.semester, None),
            ],
            active="resources",
            srn=UserState.srn,
        ),
        ui.container(
            rx.hstack(
                rx.vstack(
                    ui.eyebrow("Semester " + ResourceState.semester),
                    ui.heading("Subjects", size="38px", margin_top="6px"),
                    rx.text(
                        ResourceState.subjects.length(),
                        " subjects available",
                        color=t.TEXT_MUTED,
                        font_size="15px",
                        margin_top="6px",
                    ),
                    rx.cond(
                        ResourceState.resource_error != "",
                        rx.text(
                            ResourceState.resource_error,
                            color=t.ERROR,
                            font_size="13px",
                        ),
                        rx.fragment(),
                    ),
                    align_items="start",
                    spacing="0",
                ),
                rx.spacer(),
                rx.hstack(
                    filter_tab("All", "all"),
                    filter_tab("Current", "current"),
                    filter_tab("Stale", "stale"),
                    spacing="2",
                    align_items="center",
                    wrap="wrap",
                ),
                width="100%",
                align_items="center",
                margin_bottom="28px",
                wrap="wrap",
                gap="16px",
            ),
            rx.cond(
                ResourceState.filtered_subjects.length() > 0,
                rx.grid(
                    rx.foreach(ResourceState.filtered_subjects, subject_card),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="4",
                    align_items="stretch",
                ),
                ui.card(
                    rx.vstack(
                        rx.icon("book-open", size=28, color=t.TEXT_MUTED),
                        rx.text(
                            "No subjects found for this semester yet.",
                            color=t.TEXT_BODY,
                            font_size="15px",
                            font_weight="500",
                        ),
                        rx.text(
                            "Content is added as it gets ingested.",
                            color=t.TEXT_MUTED,
                            font_size="13px",
                        ),
                        spacing="2",
                        align_items="center",
                    ),
                    padding="56px",
                ),
            ),
        ),
        on_mount=ResourceState.load_subjects,
    )
