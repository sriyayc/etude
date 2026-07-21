"""Compiled Notes Page — /resources/[semester]/[subject_code]/notes"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.components import ui
from etude.state import NotesState, ResourceState, UserState
from etude.styles import theme as t


MD_STYLE = {
    "h1": {"color": t.TEXT, "fontSize": "24px", "fontWeight": "700", "marginTop": "24px", "marginBottom": "12px", "fontFamily": t.FONT_DISPLAY},
    "h2": {"color": t.TEXT, "fontSize": "20px", "fontWeight": "700", "marginTop": "22px", "marginBottom": "10px", "fontFamily": t.FONT_DISPLAY},
    "h3": {"color": t.TEXT, "fontSize": "16px", "fontWeight": "600", "marginTop": "16px", "marginBottom": "8px"},
    "p": {"color": t.TEXT_BODY, "fontSize": "15px", "lineHeight": "1.75", "marginBottom": "16px"},
    "ul": {"color": t.TEXT_BODY, "fontSize": "15px", "paddingLeft": "22px", "marginBottom": "16px", "listStyleType": "disc"},
    "ol": {"color": t.TEXT_BODY, "fontSize": "15px", "paddingLeft": "22px", "marginBottom": "16px"},
    "li": {"marginBottom": "6px"},
    "strong": {"color": t.TEXT, "fontWeight": "600"},
    "code": {"background": t.ACCENT_SOFT, "color": t.ACCENT_STRONG, "padding": "2px 6px", "borderRadius": "6px", "fontFamily": t.FONT_MONO, "fontSize": "13px"},
}


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
        on_click=NotesState.generate_notes(unit["unit_number"], unit["unit_title"]),
        hover=True,
        cursor="pointer",
        height="100%",
    )


def notes_viewer() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=16, color=t.TEXT_MUTED),
                rx.text("Back to units", color=t.TEXT_BODY, font_size="13px", font_weight="500"),
                spacing="1",
                on_click=NotesState.back_to_units,
                cursor="pointer",
                align_items="center",
                _hover={"color": t.ACCENT_STRONG},
            ),
            rx.spacer(),
            ui.badge("Compiled revision notes", tone="accent"),
            width="100%",
            padding="14px 32px",
            border_bottom=f"1px solid {t.BORDER}",
            align_items="center",
            background=t.BG_CARD,
        ),
        rx.box(
            rx.vstack(
                ui.eyebrow("Unit study guide · " + ResourceState.subject_code),
                ui.heading(NotesState.selected_unit_title, size="30px", margin_top="6px"),
                ui.subtext(
                    "A linear narrative compiled from your syllabus. Every statement stays grounded in the source.",
                    font_size="14px",
                    margin_top="6px",
                ),
                align_items="start",
                spacing="0",
                margin_bottom="8px",
            ),
            ui.card(
                rx.markdown(NotesState.notes_md, style=MD_STYLE),
                margin_top="20px",
                width="100%",
            ),
            rx.cond(
                NotesState.notes_sources.length() > 0,
                rx.box(
                    rx.text("Sources & citations", color=t.TEXT, font_weight="600", font_size="15px", margin_bottom="12px"),
                    rx.grid(
                        rx.foreach(
                            NotesState.notes_sources,
                            lambda src: rx.hstack(
                                rx.icon("file-text", size=14, color=t.ACCENT_STRONG),
                                rx.text(
                                    src["source_file"].to(str), " (p.", src["page_number"].to_string(), ")",
                                    color=t.TEXT_BODY,
                                    font_size="13px",
                                ),
                                spacing="2",
                                align_items="center",
                                background=t.BG_CARD,
                                border=f"1px solid {t.BORDER}",
                                border_radius=t.RADIUS_SM,
                                padding="9px 12px",
                            ),
                        ),
                        columns=rx.breakpoints(initial="1", sm="2"),
                        spacing="2",
                        width="100%",
                    ),
                    margin_top="24px",
                    width="100%",
                ),
                rx.fragment(),
            ),
            width="100%",
            max_width="820px",
            padding="32px 40px 56px",
        ),
        flex="1",
        align_items="start",
        spacing="0",
        min_width="0",
        overflow_y="auto",
    )


def unit_picker() -> rx.Component:
    return rx.box(
        rx.vstack(
            ui.eyebrow(ResourceState.subject_code + " · revision guide"),
            ui.heading("Compiled notes", size="34px", margin_top="6px"),
            ui.subtext(
                "Pick a syllabus unit to generate unified revision notes.",
                margin_top="8px",
            ),
            align_items="start",
            spacing="0",
            margin_bottom="28px",
        ),
        rx.cond(
            NotesState.notes_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(color=t.ACCENT, size="3"),
                    rx.text("Compiling notes…", color=t.TEXT, font_weight="600", font_size="15px"),
                    rx.text("Merging syllabus content — up to 30 seconds.", color=t.TEXT_MUTED, font_size="13px"),
                    spacing="3",
                    align_items="center",
                ),
                width="100%",
                height="360px",
            ),
            rx.cond(
                NotesState.notes_error != "",
                rx.center(
                    rx.vstack(
                        rx.icon("triangle-alert", size=26, color=t.ERROR),
                        rx.text(NotesState.notes_error, color=t.ERROR, font_size="14px"),
                        spacing="2",
                        align_items="center",
                    ),
                    width="100%",
                    height="280px",
                ),
                rx.grid(
                    rx.foreach(NotesState.units, unit_card),
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


def notes_page() -> rx.Component:
    return rx.box(
        topbar(breadcrumb="Notes", active="resources", srn=UserState.srn),
        rx.hstack(
            rx.cond(NotesState.has_notes, notes_viewer(), unit_picker()),
            ai_sidebar(
                context_suffix="notes",
                welcome_text=(
                    "I'm Etude AI — grounded in your syllabus. Ask me about these "
                    "compiled notes and I'll cite the source I'm drawing from."
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
                            f"{ResourceState.current_subject['subject_name']} in detail",
                        ),
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
        on_mount=NotesState.load_units,
    )
