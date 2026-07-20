"""Notes page — /resources/[semester]/[subject_code]/notes"""

import reflex as rx
from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


class NotesState(rx.State):
    topic: str = ""
    notes_md: str = ""
    sources: list[dict] = []
    loading: bool = False
    error: str = ""

    def set_topic(self, value: str):
        self.topic = value

    @rx.event
    async def generate_notes(self):
        if not self.topic.strip():
            self.error = "Enter a topic first."
            return

        self.loading = True
        self.error = ""
        self.notes_md = ""
        self.sources = []

        try:
            from services.notes_service import get_revision_notes
            result = get_revision_notes(
                topic=self.topic,
                subject=ResourceState.current_subject["subject_code"],
                semester=int(ResourceState.semester),
            )
            if result["success"]:
                self.notes_md = result["notes_md"]
                self.sources = result.get("sources", [])
            else:
                self.error = result.get("message", "Failed to generate notes.")
        except Exception as e:
            self.error = str(e)
        finally:
            self.loading = False


def notes_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_code = ResourceState.router.page.params.get("subject_code", "")

    return rx.box(
        topbar(
            breadcrumb="notes",
            active="resources",
            srn=UserState.srn,
            back_href=f"/resources/{semester}/{subject_code}",
        ),
        rx.box(
            rx.text("// AI COMPILED NOTES", color=ACCENT, font_family="monospace",
                    font_size="11px", letter_spacing="0.2em", padding="40px 48px 0"),
            rx.heading("Study notes.", color="white",
                       font_family="'Space Grotesk', sans-serif",
                       font_weight="800", font_size="42px", padding="8px 48px 24px"),

            rx.box(
                rx.hstack(
                    rx.input(
                        placeholder="Enter a topic e.g. Memory Management",
                        value=NotesState.topic,
                        on_change=NotesState.set_topic,
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
                        on_click=NotesState.generate_notes,
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
                NotesState.error != "",
                rx.text(NotesState.error, color="#EF4444",
                        font_family="monospace", font_size="13px", padding="0 48px"),
            ),

            rx.cond(
                NotesState.loading,
                rx.text("Generating notes...", color=ACCENT_LIGHT,
                        font_family="monospace", padding="0 48px"),
            ),

            rx.cond(
                NotesState.notes_md != "",
                rx.box(
                    rx.markdown(NotesState.notes_md),
                    padding="32px 48px",
                    color="white",
                    border_top=f"1px solid {BORDER}",
                ),
            ),

            max_width="900px",
            margin="0 auto",
        ),
        background=BACKGROUND,
        min_height="100vh",
    )
