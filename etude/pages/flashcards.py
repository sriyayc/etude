"""Flashcards Page — /resources/[semester]/[subject_code]/flashcards"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.state import FlashcardState, ResourceState, UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PANEL_BG = "#0A2647"


def unit_card(unit: rx.Var) -> rx.Component:
    """Render one unit card for selection."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    f"UNIT {unit['unit_number']}",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="11px",
                    letter_spacing="0.1em",
                ),
                rx.spacer(),
                rx.icon("chevron-right", size=14, color=ACCENT_LIGHT),
                width="100%",
            ),
            rx.heading(
                unit["unit_title"],
                color="white",
                font_family="'Space Grotesk', sans-serif",
                font_weight="700",
                font_size="20px",
                margin_top="10px",
                line_height="1.2",
            ),
            rx.text(
                f"{unit['topic_count']} topics defined in syllabus",
                color=ACCENT_LIGHT,
                font_family="monospace",
                font_size="12px",
                margin_top="16px",
            ),
            align_items="start",
            width="100%",
        ),
        on_click=FlashcardState.generate_flashcards(unit["unit_number"], unit["unit_title"]),
        padding="24px",
        border=f"1px solid {BORDER}",
        cursor="pointer",
        _hover={
            "background": "rgba(93,138,168,0.06)",
            "border_color": ACCENT,
        },
        height="180px",
    )


def flashcard_view() -> rx.Component:
    """Render the active flashcard viewing area."""
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=14, color=ACCENT_LIGHT),
                rx.text(
                    "BACK TO UNITS",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="12px",
                ),
                spacing="1",
                on_click=FlashcardState.back_to_units,
                cursor="pointer",
                _hover={"color": "white"},
            ),
            rx.spacer(),
            rx.text(
                FlashcardState.progress_label,
                color=ACCENT,
                font_family="monospace",
                font_size="12px",
                letter_spacing="0.1em",
            ),
            width="100%",
            padding="14px 24px",
            border_bottom=f"1px solid {BORDER}",
            align_items="center",
        ),

        rx.vstack(
            rx.text(
                f"CARD {FlashcardState.current_index + 1} OF {FlashcardState.cards.length()}",
                color=ACCENT,
                font_family="monospace",
                font_size="11px",
                letter_spacing="0.2em",
                margin_top="30px",
            ),

            # Flip Card Wrapper
            rx.center(
                rx.box(
                    rx.vstack(
                        rx.text(
                            rx.cond(FlashcardState.is_flipped, "REVEAL · BACK", "QUESTION · FRONT"),
                            color=ACCENT,
                            font_family="monospace",
                            font_size="10px",
                            letter_spacing="0.1em",
                        ),
                        rx.heading(
                            rx.cond(
                                FlashcardState.is_flipped,
                                FlashcardState.current_card["back"],
                                FlashcardState.current_card["front"],
                            ),
                            color="white",
                            font_family="'Space Grotesk', sans-serif",
                            font_weight="800",
                            font_size="24px",
                            text_align="center",
                            line_height="1.4",
                            margin_top="20px",
                        ),
                        rx.spacer(),
                        rx.text(
                            "click card to flip",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="10px",
                            opacity="0.6",
                        ),
                        align_items="center",
                        height="100%",
                        width="100%",
                    ),
                    on_click=FlashcardState.flip_card,
                    border=f"1px solid {ACCENT}",
                    background="rgba(10, 38, 71, 0.2)",
                    padding="48px",
                    width="100%",
                    max_width="600px",
                    height="320px",
                    cursor="pointer",
                    transition="transform 0.4s ease",
                    _hover={
                        "background": "rgba(10, 38, 71, 0.3)",
                        "box_shadow": f"0 0 15px {BORDER}",
                    },
                ),
                width="100%",
                padding_y="40px",
            ),

            # Card navigation
            rx.hstack(
                rx.hstack(
                    rx.icon("chevron-left", size=14),
                    rx.text("PREV", font_family="monospace", font_size="12px"),
                    spacing="1",
                    on_click=FlashcardState.prev_card,
                    cursor="pointer",
                    color=rx.cond(FlashcardState.current_index > 0, ACCENT_LIGHT, "rgba(255,255,255,0.15)"),
                ),

                rx.spacer(),

                rx.hstack(
                    rx.text("NEXT", font_family="monospace", font_size="12px"),
                    rx.icon("chevron-right", size=14),
                    spacing="1",
                    on_click=FlashcardState.next_card,
                    cursor="pointer",
                    color=rx.cond(
                        FlashcardState.current_index < FlashcardState.cards.length() - 1,
                        ACCENT_LIGHT,
                        "rgba(255,255,255,0.15)"
                    ),
                ),
                width="100%",
                max_width="600px",
                padding_top="20px",
            ),
            width="100%",
            align_items="center",
            padding_x="40px",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
    )


def flashcards_page() -> rx.Component:
    """Render the flashcards page."""
    return rx.box(
        topbar(
            breadcrumb="flashcards",
            active="resources",
            srn=UserState.srn,
        ),

        rx.hstack(
            # Left panel - picker or active card viewer
            rx.cond(
                FlashcardState.has_cards,
                flashcard_view(),
                rx.vstack(
                    rx.vstack(
                        rx.text(
                            f"// {ResourceState.subject_code} · ACTIVE RECALL",
                            color=ACCENT,
                            font_family="monospace",
                            font_size="11px",
                            letter_spacing="0.2em",
                        ),
                        rx.heading(
                            "Flashcards.",
                            color="white",
                            font_family="'Space Grotesk', sans-serif",
                            font_weight="800",
                            font_size="44px",
                        ),
                        rx.text(
                            "Select a syllabus unit below to generate study flashcards to test your knowledge.",
                            color=ACCENT_LIGHT,
                            font_size="15px",
                        ),
                        align_items="start",
                        spacing="2",
                        padding="48px 48px 24px",
                    ),

                    rx.cond(
                        FlashcardState.cards_loading,
                        rx.center(
                            rx.vstack(
                                rx.text(
                                    "GENERATING FLASHCARDS...",
                                    color=ACCENT,
                                    font_family="monospace",
                                    font_size="13px",
                                    letter_spacing="0.1em",
                                ),
                                rx.text(
                                    "Parsing key concepts from syllabus. This might take up to 20 seconds...",
                                    color=ACCENT_LIGHT,
                                    font_size="12px",
                                ),
                                rx.spinner(color=ACCENT, size="3"),
                                spacing="3",
                                align_items="center",
                            ),
                            width="100%",
                            height="400px",
                        ),
                        rx.cond(
                            FlashcardState.units_error != "",
                            rx.center(
                                rx.vstack(
                                    rx.icon("alert-triangle", size=24, color="#FF8A8A"),
                                    rx.text(
                                        FlashcardState.units_error,
                                        color="#FF8A8A",
                                        font_family="monospace",
                                        font_size="13px",
                                    ),
                                    spacing="2",
                                    align_items="center",
                                ),
                                width="100%",
                                height="300px",
                            ),
                            rx.grid(
                                rx.foreach(
                                    FlashcardState.units,
                                    unit_card,
                                ),
                                columns="2",
                                spacing="3",
                                padding="0 48px 48px",
                                width="100%",
                            ),
                        ),
                    ),
                    flex="1",
                    align_items="start",
                    spacing="0",
                    width="100%",
                    overflow_y="auto",
                ),
            ),

            # Right panel - Grounded AI Sidebar
            ai_sidebar(
                context_suffix="flashcards",
                welcome_text=(
                    "I'm Etude AI — strictly grounded in your syllabus. "
                    "Ask me anything about the flashcard terms or concepts. "
                    "I'll explain any topic step by step."
                ),
                suggestions=[
                    (
                        "Help me with this unit",
                        rx.cond(
                            FlashcardState.selected_unit_title != "",
                            f"Explain the key terms in "
                            f"{FlashcardState.selected_unit_title} for "
                            f"{ResourceState.current_subject['subject_name']}",
                            f"Explain the key concepts covered in "
                            f"{ResourceState.current_subject['subject_name']}",
                        ),
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
            height="calc(100vh - 72px)", # Height minus topbar
        ),

        background=BACKGROUND,
        min_height="100vh",
        on_mount=FlashcardState.load_units,
    )
