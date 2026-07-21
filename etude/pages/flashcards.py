"""Flashcards Page — /resources/[semester]/[subject_code]/flashcards"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.components import ui
from etude.state import FlashcardState, ResourceState, UserState
from etude.styles import theme as t


def unit_card(unit: rx.Var) -> rx.Component:
    return ui.card(
        rx.hstack(
            ui.badge("Unit " + unit["unit_number"].to_string(), tone="accent"),
            rx.spacer(),
            rx.icon("chevron-right", size=16, color=t.TEXT_MUTED),
            width="100%",
            align_items="center",
        ),
        rx.text(
            unit["unit_title"],
            color=t.TEXT,
            font_family=t.FONT_DISPLAY,
            font_weight="700",
            font_size="18px",
            margin_top="12px",
            line_height="1.25",
        ),
        rx.text(
            unit["topic_count"].to_string() + " syllabus topics",
            color=t.TEXT_MUTED,
            font_size="13px",
            margin_top="12px",
        ),
        on_click=FlashcardState.generate_flashcards(unit["unit_number"], unit["unit_title"]),
        hover=True,
        cursor="pointer",
        height="100%",
    )


def flashcard_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=16, color=t.TEXT_MUTED),
                rx.text("Back to units", color=t.TEXT_BODY, font_size="13px", font_weight="500"),
                spacing="1",
                on_click=FlashcardState.back_to_units,
                cursor="pointer",
                align_items="center",
                _hover={"color": t.ACCENT_STRONG},
            ),
            rx.spacer(),
            ui.badge(FlashcardState.progress_label, tone="accent"),
            width="100%",
            padding="14px 32px",
            border_bottom=f"1px solid {t.BORDER}",
            align_items="center",
            background=t.BG_CARD,
        ),
        rx.center(
            rx.vstack(
                ui.eyebrow(
                    "Card " + (FlashcardState.current_index + 1).to_string()
                    + " of " + FlashcardState.cards.length().to_string()
                ),
                rx.box(
                    rx.vstack(
                        ui.badge(
                            rx.cond(FlashcardState.is_flipped, "Answer", "Question"),
                            tone=rx.cond(FlashcardState.is_flipped, "success", "accent"),
                        ),
                        rx.center(
                            rx.heading(
                                rx.cond(
                                    FlashcardState.is_flipped,
                                    FlashcardState.current_card["back"],
                                    FlashcardState.current_card["front"],
                                ),
                                color=t.TEXT,
                                font_family=t.FONT_DISPLAY,
                                font_weight="700",
                                font_size="24px",
                                text_align="center",
                                line_height="1.4",
                            ),
                            flex="1",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.icon("mouse-pointer-click", size=13, color=t.TEXT_MUTED),
                            rx.text("Click to flip", color=t.TEXT_MUTED, font_size="12px"),
                            spacing="1",
                            align_items="center",
                        ),
                        align_items="center",
                        height="100%",
                        width="100%",
                        spacing="4",
                    ),
                    on_click=FlashcardState.flip_card,
                    background=t.BG_CARD,
                    border=f"1px solid {t.BORDER}",
                    border_radius=t.RADIUS,
                    box_shadow=t.SHADOW_CARD,
                    padding="40px",
                    width="100%",
                    max_width="580px",
                    height="320px",
                    cursor="pointer",
                    margin_top="20px",
                    transition="box-shadow .18s ease, transform .18s ease",
                    _hover={"box_shadow": t.SHADOW_HOVER, "transform": "translateY(-2px)"},
                ),
                rx.hstack(
                    rx.hstack(
                        rx.icon("chevron-left", size=16),
                        rx.text("Prev", font_size="14px", font_weight="500"),
                        spacing="1",
                        on_click=FlashcardState.prev_card,
                        cursor="pointer",
                        align_items="center",
                        color=rx.cond(FlashcardState.current_index > 0, t.TEXT_BODY, t.BORDER_STRONG),
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.text("Next", font_size="14px", font_weight="600"),
                        rx.icon("chevron-right", size=16),
                        spacing="1",
                        on_click=FlashcardState.next_card,
                        cursor="pointer",
                        align_items="center",
                        color=rx.cond(
                            FlashcardState.current_index < FlashcardState.cards.length() - 1,
                            t.ACCENT_STRONG,
                            t.BORDER_STRONG,
                        ),
                    ),
                    width="100%",
                    max_width="580px",
                    margin_top="24px",
                ),
                align_items="center",
                spacing="0",
            ),
            width="100%",
            flex="1",
            padding="48px 40px",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
    )


def unit_picker() -> rx.Component:
    return rx.box(
        rx.vstack(
            ui.eyebrow(ResourceState.subject_code + " · active recall"),
            ui.heading("Flashcards", size="34px", margin_top="6px"),
            ui.subtext(
                "Pick a syllabus unit to generate study flashcards for active recall.",
                margin_top="8px",
            ),
            align_items="start",
            spacing="0",
            margin_bottom="28px",
        ),
        rx.cond(
            FlashcardState.cards_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(color=t.ACCENT, size="3"),
                    rx.text("Generating flashcards…", color=t.TEXT, font_weight="600", font_size="15px"),
                    rx.text("Parsing key concepts — up to 20 seconds.", color=t.TEXT_MUTED, font_size="13px"),
                    spacing="3",
                    align_items="center",
                ),
                width="100%",
                height="360px",
            ),
            rx.cond(
                FlashcardState.units_error != "",
                rx.center(
                    rx.vstack(
                        rx.icon("triangle-alert", size=26, color=t.ERROR),
                        rx.text(FlashcardState.units_error, color=t.ERROR, font_size="14px"),
                        spacing="2",
                        align_items="center",
                    ),
                    width="100%",
                    height="280px",
                ),
                rx.grid(
                    rx.foreach(FlashcardState.units, unit_card),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    align_items="stretch",
                ),
            ),
        ),
        width="100%",
        max_width="820px",
        padding="40px",
        overflow_y="auto",
        flex="1",
    )


def flashcards_page() -> rx.Component:
    return rx.box(
        topbar(breadcrumb="Flashcards", active="resources", srn=UserState.srn),
        rx.hstack(
            rx.cond(FlashcardState.has_cards, flashcard_view(), unit_picker()),
            ai_sidebar(
                context_suffix="flashcards",
                welcome_text=(
                    "I'm Etude AI — grounded in your syllabus. Ask me about any "
                    "flashcard term or concept and I'll explain it step by step."
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
            height="calc(100vh - 61px)",
        ),
        background=t.BG_PAGE,
        min_height="100vh",
        font_family=t.FONT_BODY,
        on_mount=FlashcardState.load_units,
    )
