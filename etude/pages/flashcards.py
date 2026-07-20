"""Per-unit flashcards — /resources/[semester]/[subject_code]/flashcards"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import FlashcardState, UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PANEL_BG = "#0A2647"


def unit_card(unit: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(
            f"UNIT ", unit["unit_number"],
            color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em",
        ),
        rx.heading(
            unit["unit_title"], color="white",
            font_family="'Space Grotesk', sans-serif", font_weight="700", font_size="20px",
            margin_top="8px",
        ),
        rx.text(
            unit["topic_count"], " topics",
            color=ACCENT_LIGHT, font_family="monospace", font_size="12px", margin_top="6px",
        ),
        rx.hstack(
            rx.text("GENERATE DECK", font_family="monospace", font_size="12px"),
            rx.icon("arrow-right", size=14),
            spacing="1", color=ACCENT, margin_top="20px",
        ),
        on_click=FlashcardState.generate_flashcards(unit["unit_title"]),
        border=f"1px solid {BORDER}",
        padding="24px",
        cursor="pointer",
        _hover={"bg": "#0A2647", "border_color": ACCENT},
        transition="background .15s ease",
    )


def unit_picker() -> rx.Component:
    return rx.vstack(
        rx.text(
            "// pick a unit to build flashcards from",
            color=ACCENT_LIGHT, font_family="monospace", font_size="12px", padding="0 48px",
        ),
        rx.cond(
            FlashcardState.units_error != "",
            rx.center(
                rx.text(FlashcardState.units_error, color=ACCENT_LIGHT, font_family="monospace"),
                padding="80px 0", width="100%",
            ),
            rx.grid(
                rx.foreach(FlashcardState.units, unit_card),
                columns="3", spacing="4", width="100%", padding="24px 48px 60px",
            ),
        ),
        align_items="start", width="100%", padding_top="24px",
    )


def deck_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(FlashcardState.selected_unit_title, color="white", font_size="15px", font_weight="600"),
            rx.spacer(),
            rx.text(FlashcardState.progress_label, color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
            rx.box(
                rx.text("← UNITS", font_family="monospace", font_size="12px"),
                on_click=FlashcardState.back_to_units, cursor="pointer", color=ACCENT_LIGHT,
                margin_left="24px", _hover={"color": "white"},
            ),
            width="100%", padding="20px 48px", border_bottom=f"1px solid {BORDER}", align_items="center",
        ),
        rx.center(
            rx.box(
                rx.cond(
                    FlashcardState.is_flipped,
                    rx.vstack(
                        rx.text("BACK", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em"),
                        rx.text(
                            FlashcardState.current_card["back"], color="white", font_size="18px",
                            line_height="1.6", text_align="center", margin_top="16px", white_space="pre-wrap",
                        ),
                        align_items="center",
                    ),
                    rx.vstack(
                        rx.text("FRONT", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em"),
                        rx.text(
                            FlashcardState.current_card["front"], color="white", font_size="22px",
                            font_weight="700", line_height="1.6", text_align="center", margin_top="16px",
                        ),
                        align_items="center",
                    ),
                ),
                rx.text(
                    "click to flip", color=ACCENT_LIGHT, font_family="monospace", font_size="11px",
                    position="absolute", bottom="20px", left="0", right="0", text_align="center",
                ),
                on_click=FlashcardState.flip_card,
                cursor="pointer",
                border=f"1px solid {BORDER}",
                background="rgba(10, 38, 71, 0.3)",
                width="600px",
                min_height="320px",
                padding="48px",
                position="relative",
                display="flex",
                align_items="center",
                justify_content="center",
                _hover={"border_color": ACCENT},
                transition="border-color .15s ease",
            ),
            width="100%", padding="60px 0",
        ),
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=14), rx.text("PREV", font_family="monospace", font_size="12px"),
                spacing="1", on_click=FlashcardState.prev_card, cursor="pointer", color=ACCENT_LIGHT,
            ),
            rx.spacer(),
            rx.hstack(
                rx.text("NEXT", font_family="monospace", font_size="12px"),
                rx.icon("chevron-right", size=14),
                spacing="1", on_click=FlashcardState.next_card, cursor="pointer", color=ACCENT_LIGHT,
            ),
            width="600px", margin="0 auto", padding="0 0 40px",
        ),
        align_items="center", width="100%",
    )


def flashcards_page() -> rx.Component:
    return rx.box(
        topbar(breadcrumb="flashcards", active="resources", srn=UserState.srn),
        rx.box(
            rx.vstack(
                rx.text(
                    ResourceState.subject_code, color=ACCENT, font_family="monospace",
                    font_size="12px", letter_spacing="0.1em",
                ),
                rx.heading(
                    "Flashcards.", color="white",
                    font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="40px",
                ),
                align_items="start", padding="48px 48px 0",
            ),
            rx.cond(
                FlashcardState.cards_loading,
                rx.center(
                    rx.text("generating flashcards…", color=ACCENT_LIGHT, font_family="monospace"),
                    padding="120px 0", width="100%",
                ),
                rx.cond(
                    FlashcardState.cards_error != "",
                    rx.vstack(
                        rx.center(
                            rx.text(FlashcardState.cards_error, color="#F87171", font_family="monospace"),
                            padding="60px 0", width="100%",
                        ),
                        rx.box(
                            rx.text("← BACK TO UNITS", font_family="monospace", font_size="12px"),
                            on_click=FlashcardState.back_to_units, cursor="pointer", color=ACCENT,
                        ),
                        align_items="center", width="100%",
                    ),
                    rx.cond(FlashcardState.has_cards, deck_view(), unit_picker()),
                ),
            ),
            max_width="1600px", margin="0 auto",
        ),
        bg=BACKGROUND, min_height="100vh",
        on_mount=[ResourceState.load_subject, FlashcardState.load_units],
    )
