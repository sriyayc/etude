"""Per-unit AI-compiled notes — /resources/[semester]/[subject_code]/notes"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import NotesState, UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


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
            rx.text("COMPILE NOTES", font_family="monospace", font_size="12px"),
            rx.icon("arrow-right", size=14),
            spacing="1", color=ACCENT, margin_top="20px",
        ),
        on_click=NotesState.generate_notes(unit["unit_title"]),
        border=f"1px solid {BORDER}",
        padding="24px",
        cursor="pointer",
        _hover={"bg": "#0A2647", "border_color": ACCENT},
        transition="background .15s ease",
    )


def unit_picker() -> rx.Component:
    return rx.vstack(
        rx.text(
            "// pick a unit to compile notes for",
            color=ACCENT_LIGHT, font_family="monospace", font_size="12px", padding="0 48px",
        ),
        rx.cond(
            NotesState.units_error != "",
            rx.center(
                rx.text(NotesState.units_error, color=ACCENT_LIGHT, font_family="monospace"),
                padding="80px 0", width="100%",
            ),
            rx.grid(
                rx.foreach(NotesState.units, unit_card),
                columns="3", spacing="4", width="100%", padding="24px 48px 60px",
            ),
        ),
        align_items="start", width="100%", padding_top="24px",
    )


def source_chip(source: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.icon("file-text", size=12),
        rx.text(source["source_file"], " · p.", source["page_number"], font_family="monospace", font_size="11px"),
        spacing="1",
        color=ACCENT_LIGHT,
        border=f"1px solid {BORDER}",
        padding="6px 10px",
    )


def notes_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(NotesState.selected_unit_title, color="white", font_size="15px", font_weight="600"),
            rx.spacer(),
            rx.box(
                rx.text("← UNITS", font_family="monospace", font_size="12px"),
                on_click=NotesState.back_to_units, cursor="pointer", color=ACCENT_LIGHT,
                _hover={"color": "white"},
            ),
            width="100%", padding="20px 48px", border_bottom=f"1px solid {BORDER}", align_items="center",
        ),
        rx.box(
            rx.markdown(NotesState.notes_md),
            max_width="820px",
            padding="40px 48px",
            color="white",
            class_name="notes-markdown",
        ),
        rx.cond(
            NotesState.notes_sources.length() > 0,
            rx.vstack(
                rx.text("SOURCES", color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em"),
                rx.hstack(
                    rx.foreach(NotesState.notes_sources, source_chip),
                    spacing="2", flex_wrap="wrap",
                ),
                align_items="start", padding="0 48px 48px", spacing="2",
            ),
            rx.fragment(),
        ),
        align_items="start", width="100%",
    )


def notes_page() -> rx.Component:
    return rx.box(
        topbar(breadcrumb="notes", active="resources", srn=UserState.srn),
        rx.box(
            rx.vstack(
                rx.text(
                    ResourceState.subject_code, color=ACCENT, font_family="monospace",
                    font_size="12px", letter_spacing="0.1em",
                ),
                rx.heading(
                    "Compiled notes.", color="white",
                    font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="40px",
                ),
                align_items="start", padding="48px 48px 0",
            ),
            rx.cond(
                NotesState.notes_loading,
                rx.center(
                    rx.text("compiling notes…", color=ACCENT_LIGHT, font_family="monospace"),
                    padding="120px 0", width="100%",
                ),
                rx.cond(
                    NotesState.notes_error != "",
                    rx.vstack(
                        rx.center(
                            rx.text(NotesState.notes_error, color="#F87171", font_family="monospace"),
                            padding="60px 0", width="100%",
                        ),
                        rx.box(
                            rx.text("← BACK TO UNITS", font_family="monospace", font_size="12px"),
                            on_click=NotesState.back_to_units, cursor="pointer", color=ACCENT,
                        ),
                        align_items="center", width="100%",
                    ),
                    rx.cond(NotesState.has_notes, notes_view(), unit_picker()),
                ),
            ),
            max_width="1600px", margin="0 auto",
        ),
        bg=BACKGROUND, min_height="100vh",
        on_mount=[ResourceState.load_subject, NotesState.load_units],
    )
