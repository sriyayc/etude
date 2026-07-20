"""Subject detail — /resources/[semester]/[subject_code]"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def source_column(icon: str, label: str, title: str, description: str, count_label: str, href: str):
    return rx.vstack(
        rx.text(label, color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em"),
        rx.icon(icon, size=32, color=ACCENT_LIGHT, margin_top="24px", margin_bottom="16px"),
        rx.heading(title, color="white", font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="32px"),
        rx.text(description, color=ACCENT_LIGHT, font_size="15px", line_height="1.6", margin_top="12px", max_width="420px"),
        rx.hstack(
            rx.text(count_label, color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
            rx.spacer(),
            rx.link(
                rx.hstack(rx.text("OPEN", font_family="monospace", font_size="12px"),
                          rx.icon("arrow-right", size=14), spacing="1"),
                href=href, color=ACCENT,
            ),
            width="100%",
            margin_top="40px",
        ),
        align_items="start",
        padding="48px",
        flex="1",
        justify_content="space-between",
        min_height="360px",
    )


def subject_detail_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_code = ResourceState.router.page.params.get("subject_code", "")

    return rx.box(

        topbar(breadcrumb=subject_code, active="resources", srn=UserState.srn),

        rx.box(

            rx.vstack(
                rx.text(subject_code, color=ACCENT, font_family="monospace", font_size="12px", letter_spacing="0.1em"),
                rx.heading(
                    ResourceState.current_subject["subject_name"],
                    color="white", font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="44px",
                ),
                rx.hstack(
                    rx.box(
                        rx.cond(ResourceState.current_subject["syllabus_status"] == "current", "current syllabus", "stale syllabus"),
                        border=f"1px solid {ACCENT}", color=ACCENT, font_family="monospace",
                        font_size="12px", padding="4px 10px",
                    ),
                    rx.text(f"{ResourceState.current_subject['slide_count']} slides", color=ACCENT_LIGHT, font_family="monospace", font_size="13px"),
                    rx.text(f"{ResourceState.current_subject['page_count']} pages", color=ACCENT_LIGHT, font_family="monospace", font_size="13px"),
                    rx.text("AI grounded", color=ACCENT_LIGHT, font_family="monospace", font_size="13px"),
                    spacing="4",
                    align_items="center",
                    margin_top="16px",
                ),
                align_items="start",
                padding="48px",
            ),

            rx.hstack(
                source_column(
                    "pencil", "RAW SOURCE", "Lecture Slides",
                    "The original deck. Page-by-page slides with timestamps, callouts, and instructor annotations preserved.",
                    f"{ResourceState.current_subject['slide_count']} SLIDES",
                    f"/resources/{semester}/{subject_code}/slides",
                ),
                rx.box(width="1px", bg=BORDER),
                source_column(
                    "file-text", "AI COMPILED", "Compiled Notes",
                    "Slides + textbook merged into one linear narrative. Every sentence cites its origin (slide # or §).",
                    f"{ResourceState.current_subject['page_count']} PAGES",
                    f"/resources/{semester}/{subject_code}/notes",
                ),
                width="100%",
                spacing="0",
                border_top=f"1px solid {BORDER}",
            ),

            rx.hstack(
                rx.text(
                    "// tip — once inside, the AI sidebar stays pinned. Flashcards and quizzes never close it.",
                    color=ACCENT_LIGHT, font_family="monospace", font_size="12px",
                ),
                rx.spacer(),
                rx.link(
                    rx.hstack(rx.text("→ FLASHCARDS", font_family="monospace", font_size="12px"), spacing="1"),
                    href=f"/resources/{semester}/{subject_code}/flashcards", color=ACCENT,
                ),
                rx.link(
                    rx.hstack(rx.text("→ JUMP TO QUIZ", font_family="monospace", font_size="12px"), spacing="1"),
                    href=f"/resources/{semester}/{subject_code}/quiz", color=ACCENT,
                    margin_left="32px",
                ),
                width="100%",
                padding="20px 48px",
                border_top=f"1px solid {BORDER}",
            ),

            max_width="1600px",
            margin="0 auto",
        ),

        bg=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_subject,
    )
