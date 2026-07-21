"""Upload page — admin-only, pushes a PDF into Supabase storage + documents table."""

import reflex as rx

from etude.components.topbar import topbar
from etude.components import ui
from etude.state import UserState
from etude.styles import theme as t

UPLOAD_ID = "document_upload"
DOCUMENT_TYPES = ["textbook", "slides", "syllabus"]


def type_option(value: str):
    is_selected = UserState.upload_document_type == value
    return rx.box(
        rx.text(value.capitalize(), font_size="13px", font_weight="600"),
        on_click=lambda: UserState.set_upload_document_type(value),
        padding="9px 16px",
        border_radius=t.RADIUS_PILL,
        border=f"1px solid {rx.cond(is_selected, t.ACCENT, t.BORDER)}",
        background=rx.cond(is_selected, t.ACCENT, t.BG_CARD),
        color=rx.cond(is_selected, t.ACCENT_TEXT_ON, t.TEXT_BODY),
        cursor="pointer",
        transition="all .15s ease",
    )


def field_label(text: str):
    return rx.text(text, color=t.TEXT, font_size="13px", font_weight="600")


def upload_page():
    return ui.page(
        topbar(breadcrumb="Upload", active="upload", srn=UserState.srn),
        ui.container(
            rx.vstack(
                ui.eyebrow("Admin · add material"),
                ui.heading("Upload a document", size="34px", margin_top="6px"),
                ui.subtext(
                    "Add slides, a textbook or a syllabus. It's stored, ingested and made searchable by the AI tutor.",
                    margin_top="8px",
                ),
                align_items="start",
                spacing="0",
                margin_bottom="24px",
            ),
            ui.card(
                rx.vstack(
                    rx.vstack(
                        field_label("Title"),
                        ui.text_input(
                            placeholder="e.g. Computer Networks — Unit 3 Slides",
                            value=UserState.upload_title,
                            on_change=UserState.set_upload_title,
                        ),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                    rx.hstack(
                        rx.vstack(
                            field_label("Subject code"),
                            ui.text_input(
                                placeholder="e.g. UE23CS252B",
                                value=UserState.upload_subject,
                                on_change=UserState.set_upload_subject,
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),
                        rx.vstack(
                            field_label("Semester"),
                            rx.select(
                                [str(n) for n in range(1, 9)],
                                value=UserState.upload_semester,
                                on_change=UserState.set_upload_semester,
                                width="100%",
                            ),
                            spacing="2",
                            width="150px",
                            align_items="start",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        field_label("Document type"),
                        rx.hstack(
                            *[type_option(dt) for dt in DOCUMENT_TYPES],
                            spacing="2",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                    rx.upload(
                        rx.vstack(
                            rx.box(
                                rx.icon("upload-cloud", size=24, color=t.ACCENT_STRONG),
                                background=t.ACCENT_SOFT,
                                border_radius=t.RADIUS_PILL,
                                padding="14px",
                                display="flex",
                            ),
                            rx.text(
                                "Drag a PDF here, or click to browse",
                                color=t.TEXT_BODY,
                                font_size="14px",
                                font_weight="500",
                            ),
                            rx.foreach(
                                rx.selected_files(UPLOAD_ID),
                                lambda f: rx.text(f, color=t.ACCENT_STRONG, font_size="13px", font_weight="600"),
                            ),
                            align_items="center",
                            spacing="3",
                        ),
                        id=UPLOAD_ID,
                        accept={"application/pdf": [".pdf"]},
                        max_files=1,
                        border=f"1.5px dashed {t.BORDER_STRONG}",
                        border_radius=t.RADIUS_MD,
                        background=t.BG_SUBTLE,
                        padding="40px",
                        width="100%",
                    ),
                    rx.cond(
                        UserState.upload_error != "",
                        rx.hstack(
                            rx.icon("circle-alert", size=15, color=t.ERROR),
                            rx.text(UserState.upload_error, color=t.ERROR, font_size="13px"),
                            spacing="2", align_items="center",
                            background=t.ERROR_SOFT, border_radius=t.RADIUS_SM, padding="10px 12px", width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        UserState.upload_success,
                        rx.hstack(
                            rx.icon("circle-check", size=15, color=t.SUCCESS),
                            rx.text("Uploaded and ingested.", color=t.SUCCESS, font_size="13px"),
                            spacing="2", align_items="center",
                            background=t.SUCCESS_SOFT, border_radius=t.RADIUS_SM, padding="10px 12px", width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        UserState.upload_loading,
                        rx.hstack(
                            rx.spinner(size="1", color=t.ACCENT),
                            rx.text("Uploading & ingesting…", color=t.TEXT_MUTED, font_size="13px"),
                            spacing="2", align_items="center",
                        ),
                        ui.primary_button(
                            "Upload document",
                            icon="upload",
                            on_click=UserState.handle_upload(rx.upload_files(upload_id=UPLOAD_ID)),
                        ),
                    ),
                    spacing="5",
                    width="100%",
                ),
                max_width="620px",
            ),
        ),
    )
