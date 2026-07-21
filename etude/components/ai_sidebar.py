"""Shared Etude AI chat sidebar, pinned on the slides/notes/quiz/flashcards pages."""

import reflex as rx

from etude.state import ResourceState
from etude.styles import theme as t


def chat_bubble(message: rx.Var) -> rx.Component:
    """Render one AI or user chat message."""
    is_user = message["role"] == "user"
    return rx.box(
        rx.text(
            message["content"],
            color=rx.cond(is_user, t.ACCENT_TEXT_ON, t.TEXT_BODY),
            font_size="14px",
            line_height="1.55",
            white_space="pre-wrap",
        ),
        background=rx.cond(is_user, t.ACCENT, t.BG_SUBTLE),
        border_radius=t.RADIUS_MD,
        padding="11px 14px",
        margin_bottom="10px",
        max_width="92%",
        margin_left=rx.cond(is_user, "auto", "0"),
        border=rx.cond(is_user, "none", f"1px solid {t.BORDER}"),
    )


def _suggestion_chip(label: str, query) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="13px", font_weight="500"),
        on_click=ResourceState.ask_ai(query),
        cursor="pointer",
        border=f"1px solid {t.BORDER}",
        border_radius=t.RADIUS_PILL,
        color=t.ACCENT_STRONG,
        background=t.BG_CARD,
        padding="7px 13px",
        transition="all .15s ease",
        _hover={"background": t.ACCENT_SOFT, "border_color": t.ACCENT},
    )


def ai_sidebar(
    context_suffix: str,
    welcome_text: str,
    suggestions: list[tuple[str, object]],
) -> rx.Component:
    """The pinned Etude AI chat panel.

    suggestions is a list of (chip_label, query_text) pairs. query_text must
    carry real subject/unit context (not just the chip's short label) -- the
    retriever matches on the query text itself.
    """
    return rx.vstack(
        # Header
        rx.hstack(
            rx.box(
                rx.icon("sparkles", size=16, color=t.ACCENT_TEXT_ON),
                background=t.ACCENT,
                border_radius=t.RADIUS_SM,
                padding="7px",
                display="flex",
            ),
            rx.vstack(
                rx.text("Etude AI", color=t.TEXT, font_weight="700", font_size="15px"),
                rx.text(
                    ResourceState.current_subject["subject_name"].to(str) + " · " + context_suffix,
                    color=t.TEXT_MUTED,
                    font_size="12px",
                    font_family=t.FONT_MONO,
                ),
                spacing="0",
                align_items="start",
            ),
            rx.spacer(),
            rx.box(
                "grounded",
                background=t.SUCCESS_SOFT,
                color=t.SUCCESS,
                font_size="11px",
                font_weight="600",
                padding="3px 9px",
                border_radius=t.RADIUS_PILL,
            ),
            width="100%",
            padding="16px",
            border_bottom=f"1px solid {t.BORDER}",
            align_items="center",
        ),

        # Messages
        rx.vstack(
            rx.foreach(ResourceState.chat_messages, chat_bubble),
            rx.cond(
                ResourceState.chat_messages.length() == 0,
                rx.box(
                    rx.text(
                        welcome_text,
                        color=t.TEXT_BODY,
                        font_size="14px",
                        line_height="1.6",
                    ),
                    background=t.ACCENT_SOFT,
                    border_radius=t.RADIUS_MD,
                    padding="14px",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.cond(
                ResourceState.ai_thinking,
                rx.hstack(
                    rx.spinner(size="1", color=t.ACCENT),
                    rx.text("Thinking…", color=t.TEXT_MUTED, font_size="13px"),
                    spacing="2",
                    align_items="center",
                ),
                rx.fragment(),
            ),
            width="100%",
            padding="16px",
            flex="1",
            overflow_y="auto",
            align_items="start",
        ),

        # Suggestions
        rx.hstack(
            *[_suggestion_chip(label, query) for label, query in suggestions],
            spacing="2",
            padding="0 16px 12px",
            flex_wrap="wrap",
        ),

        # Input
        rx.hstack(
            rx.input(
                placeholder="Ask anything from your syllabus…",
                value=ResourceState.chat_input,
                on_change=ResourceState.set_chat_input,
                on_key_down=ResourceState.handle_chat_key,
                background=t.BG_CARD,
                border=f"1px solid {t.BORDER_STRONG}",
                border_radius=t.RADIUS_SM,
                color=t.TEXT,
                font_size="14px",
                flex="1",
                _placeholder={"color": t.TEXT_MUTED},
                _focus={"border_color": t.ACCENT, "outline": "none"},
            ),
            rx.box(
                rx.icon("send", size=17, color=t.ACCENT_TEXT_ON),
                on_click=ResourceState.ask_ai(""),
                background=t.ACCENT,
                border_radius=t.RADIUS_SM,
                padding="9px",
                cursor="pointer",
                display="flex",
                align_items="center",
                transition="background .15s ease",
                _hover={"background": t.ACCENT_HOVER},
            ),
            width="100%",
            padding="14px 16px",
            border_top=f"1px solid {t.BORDER}",
            align_items="center",
            spacing="2",
        ),

        width="400px",
        min_width="400px",
        background=t.BG_SIDEBAR,
        border_left=f"1px solid {t.BORDER}",
        align_items="start",
        spacing="0",
        height="100%",
    )
