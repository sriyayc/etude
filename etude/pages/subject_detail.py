"""Subject detail — /resources/[semester]/[subject_slug]"""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import UserState, ResourceState
from etude.styles import theme as t


def mode_card(icon: str, title: str, description: str, href: str) -> rx.Component:
    return rx.link(
        ui.card(
            rx.box(
                rx.icon(icon, size=22, color=t.ACCENT_STRONG),
                background=t.ACCENT_SOFT,
                border_radius=t.RADIUS_SM,
                padding="12px",
                display="inline-flex",
                align_self="flex-start",
            ),
            rx.text(
                title,
                color=t.TEXT,
                font_family=t.FONT_DISPLAY,
                font_weight="700",
                font_size="20px",
                margin_top="18px",
            ),
            ui.subtext(description, font_size="14px", margin_top="8px"),
            rx.hstack(
                rx.text("Open", color=t.ACCENT_STRONG, font_size="14px", font_weight="600"),
                rx.icon("arrow-right", size=16, color=t.ACCENT_STRONG),
                spacing="1",
                align_items="center",
                margin_top="18px",
            ),
            hover=True,
            height="100%",
            display="flex",
            flex_direction="column",
        ),
        href=href,
        display="block",
        text_decoration="none",
        height="100%",
    )


def subject_detail_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_slug = ResourceState.router.page.params.get("subject_slug", "")

    return ui.page(
        topbar(
            trail=[
                ("Resources", "/dashboard"),
                (f"Semester {semester}", f"/resources/{semester}"),
                (ResourceState.current_subject["subject_name"], None),
            ],
            active="resources",
            srn=UserState.srn,
        ),
        ui.container(
            rx.vstack(
                ui.heading(
                    ResourceState.current_subject["subject_name"],
                    size="40px",
                    margin_top="6px",
                ),
                rx.hstack(
                    ui.badge(
                        rx.cond(
                            ResourceState.current_subject["syllabus_status"] == "current",
                            "Current syllabus",
                            "Stale syllabus",
                        ),
                        background=rx.cond(
                            ResourceState.current_subject["syllabus_status"] == "current",
                            t.SUCCESS_SOFT, t.BG_SUBTLE,
                        ),
                        color=rx.cond(
                            ResourceState.current_subject["syllabus_status"] == "current",
                            t.SUCCESS, t.TEXT_MUTED,
                        ),
                    ),
                    ui.badge(
                        rx.cond(
                            ResourceState.current_subject["slide_count"].to(int) > 0,
                            ResourceState.current_subject["slide_count"].to_string()
                            + " slides",
                            "syllabus only",
                        ),
                        tone="muted",
                    ),
                    ui.badge("AI tutor grounded", tone="accent"),
                    spacing="2",
                    margin_top="16px",
                    wrap="wrap",
                ),
                align_items="start",
                spacing="0",
                margin_bottom="32px",
            ),

            rx.grid(
                mode_card(
                    "presentation",
                    "Lecture slides",
                    "The original deck rendered as-is, with an AI tutor pinned alongside.",
                    f"/resources/{semester}/{subject_slug}/slides",
                ),
                mode_card(
                    "file-text",
                    "Compiled notes",
                    "Slides and textbook merged into one linear, cited narrative per unit.",
                    f"/resources/{semester}/{subject_slug}/notes",
                ),
                mode_card(
                    "layers",
                    "Flashcards",
                    "Active-recall cards generated once per unit and shared by everyone.",
                    f"/resources/{semester}/{subject_slug}/flashcards",
                ),
                mode_card(
                    "clipboard-check",
                    "Quiz",
                    "A syllabus-bound self-assessment for each unit, ready to take.",
                    f"/resources/{semester}/{subject_slug}/quiz",
                ),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="4",
                align_items="stretch",
            ),
        ),
        on_mount=ResourceState.load_subject,
    )
