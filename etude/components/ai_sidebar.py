"""Shared Etude AI chat sidebar, pinned on the slides/notes/quiz/flashcards pages."""

import reflex as rx

from etude.state import ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"


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
        background=rx.cond(is_user, "rgba(93, 138, 168, 0.12)", "transparent"),
        border=rx.cond(is_user, f"1px solid {BORDER}", "none"),
        padding="12px",
        margin_bottom="10px",
        width="100%",
    )


def _suggestion_chip(label: str, query) -> rx.Component:
    return rx.box(
        rx.text(label),
        on_click=ResourceState.ask_ai(query),
        cursor="pointer",
        border=f"1px solid {BORDER}",
        color=ACCENT_LIGHT,
        font_family="monospace",
        font_size="12px",
        padding="8px 12px",
        _hover={"border_color": ACCENT, "color": "white"},
    )


def ai_sidebar(
    context_suffix: str,
    welcome_text: str,
    suggestions: list[tuple[str, object]],
) -> rx.Component:
    """The pinned Etude AI chat panel.

    suggestions is a list of (chip_label, query_text) pairs. query_text must
    carry real subject/unit context (not just the chip's short label) --
    the retriever matches on the query text itself, so a bare phrase like
    "Summarise this slide" has nothing to match against and always comes
    back "not covered in the provided material".
    """

    return rx.vstack(
        rx.hstack(
            rx.icon("sparkles", size=14, color=ACCENT),
            rx.text("ETUDE AI", color="white", font_weight="700", font_size="14px"),
            rx.box(
                "grounded",
                background="rgba(93, 138, 168, 0.2)",
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
            f" · {context_suffix}",
            color="white",
            font_family="monospace",
            font_size="13px",
            padding="0 14px 14px",
        ),

        rx.vstack(
            rx.foreach(ResourceState.chat_messages, chat_bubble),

            rx.cond(
                ResourceState.chat_messages.length() == 0,
                rx.box(
                    rx.text(
                        welcome_text,
                        color="white",
                        font_size="13px",
                        line_height="1.6",
                    ),
                    background="rgba(93, 138, 168, 0.1)",
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
            *[_suggestion_chip(label, query) for label, query in suggestions],
            spacing="2",
            padding="10px 14px",
            flex_wrap="wrap",
        ),

        rx.hstack(
            rx.input(
                placeholder="Ask anything from your syllabus…",
                value=ResourceState.chat_input,
                on_change=ResourceState.set_chat_input,
                on_key_down=ResourceState.handle_chat_key,
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
        height="100%",
    )
