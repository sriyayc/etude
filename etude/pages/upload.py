"""Upload page — admin-only, pushes a PDF into Supabase storage + documents table."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components.button import primary_button
from etude.components.input import text_input
from etude.state import UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"

UPLOAD_ID = "document_upload"

DOCUMENT_TYPES = ["textbook", "slides", "syllabus"]


def type_option(value: str):
    is_selected = UserState.upload_document_type == value
    return rx.box(
        rx.text(
            value.upper(),
            font_family="monospace",
            font_size="11px",
            letter_spacing="0.1em",
        ),
        on_click=lambda: UserState.set_upload_document_type(value),
        padding="10px 16px",
        border=f"1px solid {rx.cond(is_selected, ACCENT, BORDER)}",
        bg=rx.cond(is_selected, "rgba(93,138,168,0.15)", "transparent"),
        color=rx.cond(is_selected, "white", ACCENT_LIGHT),
        cursor="pointer",
    )


def upload_page():
    return rx.box(

        topbar(breadcrumb="upload", srn=UserState.srn),

        rx.box(

            rx.text(
                "// ADMIN · ADD MATERIAL",
                color=ACCENT,
                font_family="monospace",
                font_size="11px",
                letter_spacing="0.2em",
                padding="40px 48px 0",
            ),

            rx.heading(
                "Upload a document.",
                color="white",
                font_family="'Space Grotesk', sans-serif",
                font_weight="800",
                font_size="42px",
                padding="8px 48px 32px",
            ),

            rx.box(

                rx.vstack(
                    rx.text(
                        "TITLE",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="10px",
                        letter_spacing="0.2em",
                        align_self="start",
                    ),
                    text_input(
                        placeholder="e.g. Computer Networks — Unit 3 Slides",
                        value=UserState.upload_title,
                        on_change=UserState.set_upload_title,
                    ),
                    spacing="2",
                    width="100%",
                    align_items="start",
                ),

                rx.box(height="20px"),

                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "SUBJECT CODE",
                            color=ACCENT,
                            font_family="monospace",
                            font_size="10px",
                            letter_spacing="0.2em",
                            align_self="start",
                        ),
                        text_input(
                            placeholder="e.g. CS301",
                            value=UserState.upload_subject,
                            on_change=UserState.set_upload_subject,
                        ),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                    rx.vstack(
                        rx.text(
                            "SEMESTER",
                            color=ACCENT,
                            font_family="monospace",
                            font_size="10px",
                            letter_spacing="0.2em",
                            align_self="start",
                        ),
                        rx.select(
                            [str(n) for n in range(1, 9)],
                            value=UserState.upload_semester,
                            on_change=UserState.set_upload_semester,
                            width="100%",
                        ),
                        spacing="2",
                        width="140px",
                        align_items="start",
                    ),
                    spacing="4",
                    width="100%",
                ),

                rx.box(height="20px"),

                rx.vstack(
                    rx.text(
                        "DOCUMENT TYPE",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="10px",
                        letter_spacing="0.2em",
                        align_self="start",
                    ),
                    rx.hstack(
                        *[type_option(t) for t in DOCUMENT_TYPES],
                        spacing="2",
                    ),
                    spacing="2",
                    width="100%",
                    align_items="start",
                ),

                rx.box(height="20px"),

                rx.upload(
                    rx.vstack(
                        rx.icon("upload", size=22, color=ACCENT),
                        rx.text(
                            "Drag a PDF here, or click to browse",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="12px",
                        ),
                        rx.foreach(
                            rx.selected_files(UPLOAD_ID),
                            lambda f: rx.text(
                                f, color="white", font_family="monospace", font_size="12px"
                            ),
                        ),
                        align_items="center",
                        spacing="2",
                    ),
                    id=UPLOAD_ID,
                    accept={"application/pdf": [".pdf"]},
                    max_files=1,
                    border=f"1px dashed {BORDER}",
                    padding="40px",
                    width="100%",
                ),

                rx.cond(
                    UserState.upload_error != "",
                    rx.text(
                        UserState.upload_error,
                        color="#EF4444",
                        font_family="monospace",
                        font_size="12px",
                        margin_top="12px",
                    ),
                ),

                rx.cond(
                    UserState.upload_success,
                    rx.text(
                        "Uploaded.",
                        color="#22C55E",
                        font_family="monospace",
                        font_size="12px",
                        margin_top="12px",
                    ),
                ),

                rx.box(height="28px"),

                primary_button(
                    "Upload",
                    on_click=UserState.handle_upload(
                        rx.upload_files(upload_id=UPLOAD_ID)
                    ),
                ),

                width="560px",
                padding="32px",
                border=f"1px solid {BORDER}",
                margin="0 48px 60px",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
    )
