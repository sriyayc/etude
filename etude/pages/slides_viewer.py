"""Slide viewer with pinned AI sidebar.

Route:
    /resources/[semester]/[subject_code]/slides
"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.state import ResourceState, UserState


ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def toolbar_item(icon: str, label: str) -> rx.Component:
    """Render one toolbar action."""

    return rx.hstack(
        rx.icon(
            icon,
            size=14,
            color=ACCENT_LIGHT,
        ),
        rx.text(
            label,
            color=ACCENT_LIGHT,
            font_family="monospace",
            font_size="12px",
            letter_spacing="0.05em",
        ),
        spacing="2",
        padding="8px 14px",
        cursor="pointer",
        _hover={
            "color": "white",
        },
    )


def slides_viewer_page() -> rx.Component:
    """Render the slide viewer page."""

    return rx.box(
        topbar(
            breadcrumb="slides",
            active="resources",
            srn=UserState.srn,
        ),

        # ---------------- Toolbar ----------------
        rx.hstack(
            rx.link(
                toolbar_item("download", "DOWNLOAD"),
                href=ResourceState.pdf_url,
                is_external=True,
                text_decoration="none",
            ),

            rx.link(
                toolbar_item("layers", "FLASHCARDS"),
                href=(
                    f"/resources/{ResourceState.semester}/"
                    f"{ResourceState.subject_code}/flashcards"
                ),
                text_decoration="none",
            ),

            rx.link(
                toolbar_item(
                    "clipboard-check",
                    "QUIZ",
                ),
                href=ResourceState.quiz_url,
                text_decoration="none",
            ),

            rx.spacer(),

            rx.hstack(
                rx.icon(
                    "sparkles",
                    size=14,
                    color=ACCENT,
                ),
                rx.text(
                    "ETUDE AI · ON",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="12px",
                ),
                spacing="1",
                border=f"1px solid {ACCENT}",
                padding="8px 14px",
            ),

            width="100%",
            padding="10px 24px",
            border_bottom=f"1px solid {BORDER}",
            align_items="center",
        ),

        # ---------------- Main content ----------------
        rx.hstack(
            # ============================================================
            # Slide area
            # ============================================================
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "LECTURE SLIDES",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),

                    rx.text(
                        ResourceState.current_subject[
                            "subject_name"
                        ],
                        color="white",
                        font_size="13px",
                    ),

                    rx.spacer(),

                    rx.text(
                        ResourceState.current_subject["page_count"],
                        " pages",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),

                    width="100%",
                    padding="14px 24px",
                    border_bottom=f"1px solid {BORDER}",
                    align_items="center",
                ),

                # The original PDF, rendered as-is via the browser's
                # native viewer -- page navigation, zoom and search are
                # all built in, so there's no custom PREV/NEXT here.
                rx.cond(
                    ResourceState.pdf_url != "",
                    rx.el.iframe(
                        src=ResourceState.pdf_url,
                        width="100%",
                        height="calc(100vh - 140px)",
                        style={"border": "none"},
                    ),
                    rx.center(
                        rx.text(
                            "No slide PDF available for this subject.",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="13px",
                        ),
                        width="100%",
                        height="calc(100vh - 140px)",
                    ),
                ),

                flex="1",
                align_items="start",
                spacing="0",
                min_width="0",
                min_height="0",
            ),

            # ============================================================
            # AI sidebar
            # ============================================================
            ai_sidebar(
                context_suffix="slides",
                welcome_text=(
                    "I'm Etude AI — strictly grounded in your syllabus. "
                    "Ask me anything about this subject. I'll always cite "
                    "the source I'm drawing from."
                ),
                suggestions=[
                    (
                        "Summarise this subject",
                        f"Summarize the key concepts covered in "
                        f"{ResourceState.current_subject['subject_name']}",
                    ),
                    (
                        "Common pitfalls?",
                        f"What are common pitfalls or misconceptions "
                        f"students have when studying "
                        f"{ResourceState.current_subject['subject_name']}?",
                    ),
                ],
            ),

            width="100%",
            spacing="0",
            align_items="stretch",
            height="calc(100vh - 140px)",
        ),

        background=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_slides,
    )