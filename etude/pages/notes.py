"""Compiled Notes Page — /resources/[semester]/[subject_code]/notes"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.state import NotesState, ResourceState, UserState

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
        on_click=NotesState.generate_notes(unit["unit_number"], unit["unit_title"]),
        padding="24px",
        border=f"1px solid {BORDER}",
        cursor="pointer",
        _hover={
            "background": "rgba(93,138,168,0.06)",
            "border_color": ACCENT,
        },
        height="180px",
    )


def notes_viewer() -> rx.Component:
    """Display generated notes."""
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
                on_click=NotesState.back_to_units,
                cursor="pointer",
                _hover={"color": "white"},
            ),
            rx.spacer(),
            rx.text(
                "COMPILED REVISION NOTES",
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
            # Heading & Metadata
            rx.vstack(
                rx.text(
                    f"UNIT STUDY GUIDE · {ResourceState.subject_code}",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="12px",
                ),
                rx.heading(
                    NotesState.selected_unit_title,
                    color="white",
                    font_family="'Space Grotesk', sans-serif",
                    font_weight="800",
                    font_size="32px",
                ),
                rx.text(
                    "Linear narrative generated from slides and textbook. Every statement is grounded in syllabus.",
                    color=ACCENT_LIGHT,
                    font_size="14px",
                ),
                align_items="start",
                spacing="2",
                padding_x="40px",
                padding_top="30px",
            ),

            # Markdown Content
            rx.box(
                rx.markdown(
                    NotesState.notes_md,
                    style={
                        "h1": {"color": "white", "fontSize": "24px", "fontWeight": "800", "marginTop": "24px", "marginBottom": "12px", "fontFamily": "'Space Grotesk', sans-serif"},
                        "h2": {"color": "white", "fontSize": "20px", "fontWeight": "700", "marginTop": "20px", "marginBottom": "10px", "fontFamily": "'Space Grotesk', sans-serif"},
                        "h3": {"color": "white", "fontSize": "16px", "fontWeight": "600", "marginTop": "16px", "marginBottom": "8px"},
                        "p": {"color": "#B4C6D0", "fontSize": "15px", "lineHeight": "1.7", "marginBottom": "16px"},
                        "ul": {"color": "#B4C6D0", "fontSize": "15px", "paddingLeft": "20px", "marginBottom": "16px", "listStyleType": "square"},
                        "li": {"marginBottom": "6px"},
                        "code": {"background": "rgba(93,138,168,0.15)", "color": "white", "padding": "2px 6px", "fontFamily": "monospace", "fontSize": "13px"},
                    }
                ),
                padding="40px",
                width="100%",
            ),

            # Sources Section
            rx.vstack(
                rx.text(
                    "SOURCES & CITATIONS",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="12px",
                    letter_spacing="0.1em",
                ),
                rx.grid(
                    rx.foreach(
                        NotesState.notes_sources,
                        lambda src: rx.hstack(
                            rx.icon("file-text", size=14, color=ACCENT_LIGHT),
                            rx.text(
                                f"{src['source_file']} (p.{src['page_number']})",
                                color=ACCENT_LIGHT,
                                font_family="monospace",
                                font_size="12px",
                            ),
                            spacing="2",
                            border=f"1px solid {BORDER}",
                            padding="8px 12px",
                        )
                    ),
                    columns="2",
                    spacing="2",
                    width="100%",
                    margin_top="12px",
                ),
                align_items="start",
                padding="40px",
                border_top=f"1px solid {BORDER}",
                width="100%",
            ),
            align_items="start",
            width="100%",
        ),
        flex="1",
        align_items="start",
        spacing="0",
        min_width="0",
        overflow_y="auto",
    )


def notes_page() -> rx.Component:
    """Render the notes page."""
    return rx.box(
        topbar(
            breadcrumb="compiled notes",
            active="resources",
            srn=UserState.srn,
        ),

        rx.hstack(
            # Left panel - either Unit picker or Notes Viewer
            rx.cond(
                NotesState.has_notes,
                notes_viewer(),
                rx.vstack(
                    rx.vstack(
                        rx.text(
                            f"// {ResourceState.subject_code} · REVISION GUIDE",
                            color=ACCENT,
                            font_family="monospace",
                            font_size="11px",
                            letter_spacing="0.2em",
                        ),
                        rx.heading(
                            "Compiled Notes.",
                            color="white",
                            font_family="'Space Grotesk', sans-serif",
                            font_weight="800",
                            font_size="44px",
                        ),
                        rx.text(
                            "Select a syllabus unit below to generate unified revision notes.",
                            color=ACCENT_LIGHT,
                            font_size="15px",
                        ),
                        align_items="start",
                        spacing="2",
                        padding="48px 48px 24px",
                    ),

                    rx.cond(
                        NotesState.notes_loading,
                        rx.center(
                            rx.vstack(
                                rx.text(
                                    "COMPILING SYLLABUS...",
                                    color=ACCENT,
                                    font_family="monospace",
                                    font_size="13px",
                                    letter_spacing="0.1em",
                                ),
                                rx.text(
                                    "Merging textbook data and lecture slides. This might take up to 30 seconds...",
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
                            NotesState.notes_error != "",
                            rx.center(
                                rx.vstack(
                                    rx.icon("alert-triangle", size=24, color="#FF8A8A"),
                                    rx.text(
                                        NotesState.notes_error,
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
                                    NotesState.units,
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
                context_suffix="compiled notes",
                welcome_text=(
                    "I'm Etude AI — strictly grounded in your syllabus. "
                    "Ask me anything about the compiled notes. I'll always "
                    "cite the page and slide I'm drawing from."
                ),
                suggestions=[
                    (
                        "Summarise this unit",
                        rx.cond(
                            NotesState.selected_unit_title != "",
                            f"Summarize the key concepts of "
                            f"{NotesState.selected_unit_title} in "
                            f"{ResourceState.current_subject['subject_name']}",
                            f"Summarize the key concepts covered in "
                            f"{ResourceState.current_subject['subject_name']}",
                        ),
                    ),
                    (
                        "Explain a key topic",
                        rx.cond(
                            NotesState.selected_unit_title != "",
                            f"Explain an important topic from "
                            f"{NotesState.selected_unit_title} in detail",
                            f"Explain an important topic in "
                            f"{ResourceState.current_subject['subject_name']} "
                            f"in detail",
                        ),
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
        on_mount=NotesState.load_units,
    )
