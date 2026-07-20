"""Slide viewer with pinned AI sidebar.

Route:
    /resources/[semester]/[subject_code]/slides
"""

import reflex as rx

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


def chat_bubble(message: rx.Var) -> rx.Component:
    """Render one AI or user chat message."""

    is_user = message["role"] == "user"

    return rx.box(
        rx.text(
            message["content"],
            color="white",
            font_size="14px",
            line_height="1.5",
            white_space="pre-wrap",
        ),
        background=rx.cond(
            is_user,
            "rgba(93, 138, 168, 0.12)",
            "transparent",
        ),
        border=rx.cond(
            is_user,
            f"1px solid {BORDER}",
            "none",
        ),
        padding="12px",
        margin_bottom="10px",
        width="100%",
    )


def suggestion_chip(text: str) -> rx.Component:
    """Render a preset question button."""

    return rx.box(
        rx.text(text),
        # Pass the string argument explicitly.
        on_click=ResourceState.ask_ai(text),
        cursor="pointer",
        border=f"1px solid {BORDER}",
        color=ACCENT_LIGHT,
        font_family="monospace",
        font_size="12px",
        padding="8px 12px",
        _hover={
            "border_color": ACCENT,
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
            rx.vstack(
                rx.hstack(
                    rx.icon(
                        "sparkles",
                        size=14,
                        color=ACCENT,
                    ),
                    rx.text(
                        "ETUDE AI",
                        color="white",
                        font_weight="700",
                        font_size="14px",
                    ),
                    rx.box(
                        "grounded",
                        background=(
                            "rgba(93, 138, 168, 0.2)"
                        ),
                        color=ACCENT,
                        font_family="monospace",
                        font_size="10px",
                        padding="2px 6px",
                        margin_left="6px",
                    ),
                    width="100%",
                    padding="14px",
                    border_bottom=f"1px solid {BORDER}",
                    align_items="center",
                ),

                rx.text(
                    "CONTEXT",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="10px",
                    padding="14px 14px 0",
                ),

                rx.text(
                    ResourceState.subject_code,
                    " · slides",
                    color="white",
                    font_family="monospace",
                    font_size="13px",
                    padding="0 14px 14px",
                ),

                rx.vstack(
                    rx.foreach(
                        ResourceState.chat_messages,
                        chat_bubble,
                    ),

                    rx.cond(
                        ResourceState.chat_messages.length()
                        == 0,
                        rx.box(
                            rx.text(
                                (
                                    "I'm Etude AI — strictly "
                                    "grounded in your syllabus. "
                                    "Ask me anything about the "
                                    "current slide. I'll always "
                                    "cite the slide I'm drawing "
                                    "from."
                                ),
                                color="white",
                                font_size="13px",
                                line_height="1.6",
                            ),
                            background=(
                                "rgba(93, 138, 168, 0.1)"
                            ),
                            border=f"1px solid {BORDER}",
                            padding="14px",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),

                    rx.cond(
                        ResourceState.ai_thinking,
                        rx.text(
                            "thinking…",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="12px",
                        ),
                        rx.fragment(),
                    ),

                    width="100%",
                    padding="0 14px",
                    flex="1",
                    overflow_y="auto",
                    align_items="start",
                ),

                rx.hstack(
                    suggestion_chip(
                        "Summarise this slide"
                    ),
                    suggestion_chip(
                        "Common pitfalls?"
                    ),
                    spacing="2",
                    padding="10px 14px",
                    flex_wrap="wrap",
                ),

                rx.hstack(
                    rx.input(
                        placeholder=(
                            "Ask anything from your "
                            "syllabus…"
                        ),
                        value=ResourceState.chat_input,
                        on_change=(
                            ResourceState.set_chat_input
                        ),
                        background="black",
                        border=f"1px solid {BORDER}",
                        color="white",
                        font_family="monospace",
                        font_size="13px",
                        flex="1",
                    ),

                    rx.icon(
                        "send",
                        size=16,
                        color=ACCENT,
                        cursor="pointer",

                        # Explicitly pass an empty string.
                        # Reflex will not fill the parameter
                        # with PointerEventInfo.
                        on_click=ResourceState.ask_ai(""),
                    ),

                    width="100%",
                    padding="14px",
                    border_top=f"1px solid {BORDER}",
                    align_items="center",
                ),

                width="420px",
                min_width="420px",
                background="#050D18",
                border_left=f"1px solid {BORDER}",
                align_items="start",
                spacing="0",
            ),

            width="100%",
            spacing="0",
            align_items="stretch",
        ),

        background=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_slides,
    )