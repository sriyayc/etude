"""Slide viewer with pinned AI sidebar.

Route:
    /resources/[semester]/[subject_slug]/slides
"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.state import ResourceState, UserState
from etude.styles import theme as t


def toolbar_link(icon: str, label: str, href: str, external: bool = False) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=15, color=t.TEXT_BODY),
            rx.text(label, color=t.TEXT_BODY, font_size="13px", font_weight="500"),
            spacing="2",
            padding="7px 12px",
            border_radius=t.RADIUS_SM,
            align_items="center",
            transition="background .15s ease, color .15s ease",
            _hover={"background": t.BG_SUBTLE, "color": t.ACCENT_STRONG},
        ),
        href=href,
        is_external=external,
        text_decoration="none",
    )


def slides_viewer_page() -> rx.Component:
    """Render the slide viewer page."""

    return rx.box(
        topbar(
            trail=[
                ("Resources", "/dashboard"),
                ("Semester " + ResourceState.semester, f"/resources/{ResourceState.semester}"),
                (
                    ResourceState.current_subject["subject_name"],
                    f"/resources/{ResourceState.semester}/{ResourceState.subject_slug}",
                ),
                ("Slides", None),
            ],
            active="resources",
            srn=UserState.srn,
        ),

        # ---------------- Toolbar ----------------
        rx.hstack(
            rx.hstack(
                rx.text(
                    ResourceState.current_subject["subject_name"],
                    color=t.TEXT,
                    font_weight="600",
                    font_size="15px",
                ),
                rx.text(
                    "lecture slides",
                    color=t.TEXT_MUTED,
                    font_size="13px",
                    font_family=t.FONT_MONO,
                ),
                spacing="3",
                align_items="center",
            ),
            rx.spacer(),
            toolbar_link("download", "Download", ResourceState.pdf_url, external=True),
            toolbar_link(
                "layers", "Flashcards",
                f"/resources/{ResourceState.semester}/{ResourceState.subject_slug}/flashcards",
            ),
            toolbar_link("clipboard-check", "Quiz", ResourceState.quiz_url),
            width="100%",
            padding="10px 24px",
            border_bottom=f"1px solid {t.BORDER}",
            align_items="center",
            background=t.BG_CARD,
        ),

        # ---------------- Main content ----------------
        rx.hstack(
            # Slide area
            rx.box(
                rx.cond(
                    ResourceState.pdf_url != "",
                    rx.el.iframe(
                        src=ResourceState.pdf_url,
                        width="100%",
                        height="calc(100vh - 118px)",
                        style={"border": "none"},
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("file-x", size=30, color=t.TEXT_MUTED),
                            rx.text(
                                "No slide PDF available for this subject yet.",
                                color=t.TEXT_BODY,
                                font_size="15px",
                                font_weight="500",
                            ),
                            rx.text(
                                "You can still use the AI tutor on the right.",
                                color=t.TEXT_MUTED,
                                font_size="13px",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        width="100%",
                        height="calc(100vh - 118px)",
                    ),
                ),
                flex="1",
                min_width="0",
                background=t.BG_SUBTLE,
            ),

            # AI sidebar
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
            height="calc(100vh - 118px)",
        ),

        background=t.BG_PAGE,
        min_height="100vh",
        font_family=t.FONT_BODY,
        on_mount=ResourceState.load_slides,
    )