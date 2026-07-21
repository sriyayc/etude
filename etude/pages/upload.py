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


def subject_admin_panel():
    """Add or remove subjects in the selected semester.

    Lives beside the upload form because that is where an admin discovers a
    subject is missing -- one place to fix it rather than a separate screen.
    """
    return rx.box(
        rx.hstack(
            rx.icon("folder-cog", size=15, color=t.TEXT_MUTED),
            rx.text(
                "Manage subjects in semester " + UserState.upload_semester,
                color=t.TEXT_MUTED,
                font_size="12px",
                font_weight="600",
            ),
            spacing="2",
            align_items="center",
            margin_bottom="10px",
        ),
        rx.hstack(
            ui.text_input(
                placeholder="New subject name — e.g. Operating Systems",
                value=UserState.new_subject_name,
                on_change=UserState.set_new_subject_name,
                flex="1",
            ),
            ui.ghost_button("Add", on_click=UserState.create_new_subject),
            ui.ghost_button("Delete selected", on_click=UserState.delete_selected_subject),
            spacing="2",
            width="100%",
            align_items="center",
        ),
        rx.cond(
            UserState.subject_admin_error != "",
            rx.text(
                UserState.subject_admin_error,
                color=t.ERROR,
                font_size="12px",
                margin_top="8px",
            ),
            rx.fragment(),
        ),
        rx.cond(
            UserState.subject_admin_notice != "",
            rx.text(
                UserState.subject_admin_notice,
                color=t.SUCCESS,
                font_size="12px",
                margin_top="8px",
            ),
            rx.fragment(),
        ),
        width="100%",
        padding="14px 16px",
        background=t.BG_SUBTLE,
        border=f"1px solid {t.BORDER}",
        border_radius=t.RADIUS_MD,
    )


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
                            field_label("Semester"),
                            rx.select(
                                [str(n) for n in range(1, 7)],
                                value=UserState.upload_semester,
                                on_change=UserState.set_upload_semester,
                                width="100%",
                            ),
                            spacing="2",
                            width="150px",
                            align_items="start",
                        ),
                        rx.vstack(
                            field_label("Subject"),
                            rx.select(
                                UserState.upload_subject_options,
                                value=UserState.upload_subject,
                                on_change=UserState.set_upload_subject,
                                placeholder="Choose a subject…",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),
                        spacing="4",
                        width="100%",
                        align_items="end",
                    ),
                    subject_admin_panel(),
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
                                rx.icon("cloud-upload", size=24, color=t.ACCENT_STRONG),
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
                        rx.vstack(
                            rx.hstack(
                                rx.spinner(size="1", color=t.ACCENT),
                                rx.text(
                                    UserState.upload_status,
                                    color=t.TEXT,
                                    font_size="13px",
                                    font_weight="500",
                                ),
                                spacing="2",
                                align_items="center",
                            ),
                            # Per-file progress. Embedding a deck runs tens of
                            # seconds, so a bare spinner reads as a hang.
                            rx.cond(
                                UserState.upload_total_count > 1,
                                rx.box(
                                    rx.box(
                                        width=UserState.upload_percent.to_string() + "%",
                                        height="100%",
                                        bg=t.ACCENT,
                                        border_radius=t.RADIUS_PILL,
                                        transition="width .3s ease",
                                    ),
                                    width="100%",
                                    height="6px",
                                    bg=t.BG_SUBTLE,
                                    border_radius=t.RADIUS_PILL,
                                ),
                                rx.fragment(),
                            ),
                            rx.text(
                                "Keep this tab open — leaving now cancels the ingest.",
                                color=t.TEXT_MUTED,
                                font_size="12px",
                            ),
                            spacing="3",
                            width="100%",
                            align_items="start",
                            background=t.BG_SUBTLE,
                            border=f"1px solid {t.BORDER}",
                            border_radius=t.RADIUS_MD,
                            padding="14px 16px",
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
