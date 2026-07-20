"""Flashcards page — /resources/[semester]/[subject_code]/flashcards"""

import reflex as rx
from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


class FlashcardState(rx.State):
    topic: str = ""
    cards: list[dict] = []
    loading: bool = False
    error: str = ""
    current_index: int = 0
    flipped: bool = False

    def set_topic(self, value: str):
        self.topic = value

    def flip_card(self):
        self.flipped = not self.flipped

    def next_card(self):
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.flipped = False

    def prev_card(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.flipped = False

    @rx.event
    async def generate_flashcards(self):
        if not self.topic.strip():
            self.error = "Enter a topic first."
            return

        self.loading = True
        self.error = ""
        self.cards = []
        self.current_index = 0
        self.flipped = False

        try:
            from services.flashcard_service import get_flashcards
            result = get_flashcards(
                topic=self.topic,
                subject=self.current_subject["subject_code"],
                semester=int(self.semester),
            )
            if result["success"]:
                self.cards = result["cards"]
            else:
                self.error = result.get("message", "Failed to generate flashcards.")
        except Exception as e:
            self.error = str(e)
        finally:
            self.loading = False


def flashcards_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_code = ResourceState.router.page.params.get("subject_code", "")

    return rx.box(
        topbar(
            breadcrumb="flashcards",
            active="resources",
            srn=UserState.srn,
            back_href=f"/resources/{semester}/{subject_code}",
        ),

        rx.box(
            rx.text("// FLASHCARDS", color=ACCENT, font_family="monospace",
                    font_size="11px", letter_spacing="0.2em", padding="40px 48px 0"),
            rx.heading("Quick revision.", color="white",
                       font_family="'Space Grotesk', sans-serif",
                       font_weight="800", font_size="42px", padding="8px 48px 24px"),

            rx.box(
                rx.hstack(
                    rx.input(
                        placeholder="Enter a topic e.g. Semaphores",
                        value=FlashcardState.topic,
                        on_change=FlashcardState.set_topic,
                        background="black",
                        border=f"1px solid {BORDER}",
                        color="white",
                        font_family="monospace",
                        font_size="14px",
                        flex="1",
                        height="52px",
                        padding="0 16px",
                    ),
                    rx.button(
                        "GENERATE →",
                        on_click=FlashcardState.generate_flashcards,
                        background=ACCENT,
                        color="black",
                        font_family="monospace",
                        font_weight="700",
                        font_size="13px",
                        height="52px",
                        padding="0 24px",
                        cursor="pointer",
                        border_radius="0px",
                        type="button",
                    ),
                    spacing="3",
                    width="100%",
                ),
                padding="0 48px 32px",
            ),

            rx.cond(
                FlashcardState.error != "",
                rx.text(FlashcardState.error, color="#EF4444",
                        font_family="monospace", font_size="13px", padding="0 48px"),
            ),

            rx.cond(
                FlashcardState.loading,
                rx.text("Generating flashcards...", color=ACCENT_LIGHT,
                        font_family="monospace", padding="0 48px"),
            ),

            rx.cond(
                FlashcardState.cards.length() > 0,
                rx.box(
                    rx.text(
                        FlashcardState.current_index + 1,
                        " / ",
                        FlashcardState.cards.length(),
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="13px",
                        margin_bottom="16px",
                    ),
                    rx.box(
                        rx.cond(
                            ~FlashcardState.flipped,
                            rx.vstack(
                                rx.text("QUESTION", color=ACCENT, font_family="monospace",
                                        font_size="11px", letter_spacing="0.15em"),
                                rx.text(
                                    FlashcardState.cards[FlashcardState.current_index]["front"],
                                    color="white",
                                    font_size="20px",
                                    font_weight="600",
                                    text_align="center",
                                    margin_top="16px",
                                ),
                                rx.text("click to reveal answer", color=ACCENT_LIGHT,
                                        font_family="monospace", font_size="11px",
                                        margin_top="24px"),
                                align_items="center",
                                justify_content="center",
                                height="100%",
                                spacing="2",
                            ),
                            rx.vstack(
                                rx.text("ANSWER", color=ACCENT, font_family="monospace",
                                        font_size="11px", letter_spacing="0.15em"),
                                rx.text(
                                    FlashcardState.cards[FlashcardState.current_index]["back"],
                                    color="white",
                                    font_size="16px",
                                    line_height="1.6",
                                    text_align="center",
                                    margin_top="16px",
                                ),
                                align_items="center",
                                justify_content="center",
                                height="100%",
                                spacing="2",
                            ),
                        ),
                        on_click=FlashcardState.flip_card,
                        cursor="pointer",
                        border=f"1px solid {ACCENT}",
                        background="rgba(93,138,168,0.05)",
                        padding="48px",
                        min_height="280px",
                        width="100%",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        margin_bottom="24px",
                    ),
                    rx.hstack(
                        rx.button(
                            "← PREV",
                            on_click=FlashcardState.prev_card,
                            background="transparent",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="13px",
                            border=f"1px solid {BORDER}",
                            padding="10px 20px",
                            cursor="pointer",
                            border_radius="0px",
                            type="button",
                        ),
                        rx.button(
                            "NEXT →",
                            on_click=FlashcardState.next_card,
                            background="transparent",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="13px",
                            border=f"1px solid {BORDER}",
                            padding="10px 20px",
                            cursor="pointer",
                            border_radius="0px",
                            type="button",
                        ),
                        spacing="3",
                    ),
                    padding="0 48px 60px",
                ),
            ),

            max_width="800px",
            margin="0 auto",
        ),

        background=BACKGROUND,
        min_height="100vh",
    )
