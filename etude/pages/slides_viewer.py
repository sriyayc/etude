"""Slide viewer with pinned AI sidebar — /resources/[semester]/[subject_code]/slides"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PANEL_BG = "#0A2647"


def toolbar_item(icon: str, label: str):
    return rx.hstack(
        rx.icon(icon, size=14, color=ACCENT_LIGHT),
        rx.text(label, color=ACCENT_LIGHT, font_family="monospace", font_size="12px", letter_spacing="0.05em"),
        spacing="2",
        padding="8px 14px",
        cursor="pointer",
        _hover={"color": "white"},
    )


def chat_bubble(msg: rx.Var):
    is_user = msg["role"] == "user"
    return rx.box(
        rx.text(msg["content"], color="white", font_size="14px", line_height="1.5"),
        bg=rx.cond(is_user, "rgba(93,138,168,0.12)", "transparent"),
        border=rx.cond(is_user, f"1px solid {BORDER}", "none"),
        padding="12px",
        margin_bottom="10px",
    )


def suggestion_chip(text: str):
    return rx.box(
        text,
        on_click=lambda: ResourceState.ask_ai(text),
        cursor="pointer",
        border=f"1px solid {BORDER}",
        color=ACCENT_LIGHT,
        font_family="monospace",
        font_size="12px",
        padding="8px 12px",
        _hover={"border_color": ACCENT, "color": "white"},
    )


def slides_viewer_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_code = ResourceState.router.page.params.get("subject_code", "")

    return rx.box(

        topbar(breadcrumb="slides", active="resources", srn=UserState.srn),

        rx.hstack(
            toolbar_item("download", "DOWNLOAD"),
            toolbar_item("eye", "VIEW IN APP"),
            toolbar_item("square-mouse-pointer", "SELECT & ASK"),
            toolbar_item("layers", "FLASHCARDS"),
            rx.link(toolbar_item("clipboard-check", "QUIZ"),
                    href=f"/resources/{semester}/{subject_code}/quiz"),
            rx.spacer(),
            rx.hstack(
                rx.icon("sparkles", size=14, color=ACCENT),
                rx.text("ETUDE AI · ON", color=ACCENT, font_family="monospace", font_size="12px"),
                spacing="1",
                border=f"1px solid {ACCENT}",
                padding="8px 14px",
            ),
            width="100%",
            padding="10px 24px",
            border_bottom=f"1px solid {BORDER}",
            align_items="center",
        ),

        rx.hstack(

            # ---- slide area ----
            rx.vstack(
                rx.hstack(
                    rx.text("LECTURE SLIDES", color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
                    rx.text(ResourceState.current_subject["subject_name"], color="white", font_size="13px"),
                    rx.spacer(),
                    rx.text(
                        f"slide {ResourceState.current_slide_index + 1} / {ResourceState.slides.length()}",
                        color=ACCENT_LIGHT, font_family="monospace", font_size="12px",
                    ),
                    width="100%",
                    padding="14px 24px",
                    border_bottom=f"1px solid {BORDER}",
                ),

                rx.vstack(
                    rx.text(
                        f"SLIDE {ResourceState.slide_number_padded} · MOD-{ResourceState.current_slide['module_number']}",
                        color=ACCENT, font_family="monospace", font_size="12px",
                    ),
                    rx.heading(
                        ResourceState.current_slide["title"],
                        color="white", font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="28px",
                    ),
                    rx.box(
                        rx.text(ResourceState.current_slide["content"], color="white", font_size="16px", line_height="1.6"),
                        border=f"1px solid {PANEL_BG}",
                        bg="rgba(10,38,71,0.3)",
                        padding="32px",
                        margin_top="20px",
                        min_height="200px",
                        width="100%",
                    ),
                    align_items="start",
                    padding="40px",
                    width="100%",
                ),

                rx.hstack(
                    rx.hstack(rx.icon("chevron-left", size=14), rx.text("PREV", font_family="monospace", font_size="12px"),
                              spacing="1", on_click=ResourceState.prev_slide, cursor="pointer", color=ACCENT_LIGHT),
                    rx.spacer(),
                    rx.hstack(rx.text("NEXT", font_family="monospace", font_size="12px"), rx.icon("chevron-right", size=14),
                              spacing="1", on_click=ResourceState.next_slide, cursor="pointer", color=ACCENT_LIGHT),
                    width="100%",
                    padding="16px 40px",
                    border_top=f"1px solid {BORDER}",
                ),

                flex="1",
                align_items="start",
                spacing="0",
            ),

            # ---- AI sidebar (pinned) ----
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=14, color=ACCENT),
                    rx.text("ETUDE AI", color="white", font_weight="700", font_size="14px"),
                    rx.box("grounded", bg="rgba(93,138,168,0.2)", color=ACCENT,
                           font_family="monospace", font_size="10px", padding="2px 6px", margin_left="6px"),
                    width="100%",
                    padding="14px",
                    border_bottom=f"1px solid {BORDER}",
                ),

                rx.text(
                    "CONTEXT", color=ACCENT_LIGHT, font_family="monospace", font_size="10px",
                    padding="14px 14px 0",
                ),
                rx.text(
                    f"{subject_code} · slides", color="white", font_family="monospace", font_size="13px",
                    padding="0 14px 14px",
                ),

                rx.vstack(
                    rx.foreach(ResourceState.chat_messages, chat_bubble),
                    rx.cond(
                        ResourceState.chat_messages.length() == 0,
                        rx.box(
                            rx.text(
                                "I'm Etude AI — strictly grounded in your syllabus. "
                                "Ask me anything about the current slide. I'll always "
                                "cite the slide I'm drawing from.",
                                color="white", font_size="13px", line_height="1.6",
                            ),
                            bg="rgba(93,138,168,0.1)",
                            border=f"1px solid {BORDER}",
                            padding="14px",
                        ),
                    ),
                    rx.cond(ResourceState.ai_thinking, rx.text("thinking…", color=ACCENT_LIGHT, font_family="monospace", font_size="12px")),
                    width="100%",
                    padding="0 14px",
                    flex="1",
                    overflow_y="auto",
                    align_items="start",
                ),

                rx.hstack(
                    suggestion_chip("Summarise this slide"),
                    suggestion_chip("Common pitfalls?"),
                    spacing="2",
                    padding="10px 14px",
                    flex_wrap="wrap",
                ),

                rx.hstack(
                    rx.input(
                        placeholder="Ask anything from your syllabus…",
                        value=ResourceState.chat_input,
                        on_change=ResourceState.set_chat_input,
                        bg="black",
                        border=f"1px solid {BORDER}",
                        color="white",
                        font_family="monospace",
                        font_size="13px",
                        flex="1",
                    ),
                    rx.icon("send", size=16, color=ACCENT, cursor="pointer",
                            on_click=lambda: ResourceState.ask_ai()),
                    width="100%",
                    padding="14px",
                    border_top=f"1px solid {BORDER}",
                    align_items="center",
                ),

                width="420px",
                bg="#050d18",
                border_left=f"1px solid {BORDER}",
                align_items="start",
                spacing="0",
            ),

            width="100%",
            spacing="0",
            align_items="stretch",
        ),

        bg=BACKGROUND,
        min_height="100vh",
        on_mount=ResourceState.load_slides,
    )
