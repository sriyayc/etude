"""Quiz page — /resources/[semester]/[subject_code]/quiz"""

import reflex as rx
from etude.components.topbar import topbar
from etude.state import UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


class QuizState(rx.State):
    topic: str = ""
    questions: list[dict] = []
    loading: bool = False
    error: str = ""
    answers: dict[int, str] = {}
    submitted: bool = False
    score: int = 0

    def set_topic(self, value: str):
        self.topic = value

    def select_answer(self, idx: int, answer: str):
        self.answers[idx] = answer

    @rx.event
    async def generate_quiz(self):
        if not self.topic.strip():
            self.error = "Enter a topic first."
            return

        self.loading = True
        self.error = ""
        self.questions = []
        self.answers = {}
        self.submitted = False

        try:
            from services.quiz_service import get_quiz
            result = get_quiz(
                topic=self.topic,
                subject=self.current_subject["subject_code"],
                semester=int(self.semester),
            )
            if result["success"]:
                self.questions = result["questions"]
            else:
                self.error = result.get("message", "Failed to generate quiz.")
        except Exception as e:
            self.error = str(e)
        finally:
            self.loading = False

    @rx.event
    def submit_quiz(self):
        if not self.questions:
            return
        correct = sum(
            1 for i, q in enumerate(self.questions)
            if self.answers.get(i) == q.get("answer")
        )
        self.score = correct
        self.submitted = True


def question_card(question: rx.Var, idx: int):
    return rx.box(
        rx.text(
            f"Q{idx + 1}. ",
            rx.text.span(question["question"]),
            color="white",
            font_size="15px",
            font_weight="600",
            margin_bottom="12px",
        ),
        rx.vstack(
            rx.foreach(
                question["options"],
                lambda opt: rx.box(
                    rx.text(opt, color="white", font_size="14px"),
                    padding="10px 16px",
                    border=f"1px solid {BORDER}",
                    cursor="pointer",
                    width="100%",
                    _hover={"border_color": ACCENT, "background": "rgba(93,138,168,0.1)"},
                    on_click=QuizState.select_answer(idx, opt),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        padding="24px",
        border=f"1px solid {BORDER}",
        margin_bottom="16px",
        width="100%",
    )


def quiz_page():
    semester = ResourceState.router.page.params.get("semester", "1")
    subject_code = ResourceState.router.page.params.get("subject_code", "")

    return rx.box(
        topbar(
            breadcrumb="quiz",
            active="resources",
            srn=UserState.srn,
            back_href=f"/resources/{semester}/{subject_code}",
        ),

        rx.box(
            rx.text("// AI QUIZ", color=ACCENT, font_family="monospace",
                    font_size="11px", letter_spacing="0.2em", padding="40px 48px 0"),
            rx.heading("Test yourself.", color="white",
                       font_family="'Space Grotesk', sans-serif",
                       font_weight="800", font_size="42px", padding="8px 48px 24px"),

            rx.box(
                rx.hstack(
                    rx.input(
                        placeholder="Enter a topic e.g. TCP Sliding Window",
                        value=QuizState.topic,
                        on_change=QuizState.set_topic,
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
                        on_click=QuizState.generate_quiz,
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
                QuizState.error != "",
                rx.text(QuizState.error, color="#EF4444",
                        font_family="monospace", font_size="13px", padding="0 48px"),
            ),

            rx.cond(
                QuizState.loading,
                rx.text("Generating quiz...", color=ACCENT_LIGHT,
                        font_family="monospace", padding="0 48px"),
            ),

            rx.cond(
                QuizState.questions.length() > 0,
                rx.box(
                    rx.foreach(
                        QuizState.questions,
                        lambda q, i: question_card(q, i),
                    ),
                    rx.cond(
                        ~QuizState.submitted,
                        rx.button(
                            "SUBMIT QUIZ",
                            on_click=QuizState.submit_quiz,
                            background=ACCENT,
                            color="black",
                            font_family="monospace",
                            font_weight="700",
                            height="52px",
                            padding="0 32px",
                            cursor="pointer",
                            border_radius="0px",
                            type="button",
                            margin_top="16px",
                        ),
                        rx.box(
                            rx.text(
                                f"Score: {QuizState.score} / {QuizState.questions.length()}",
                                color="white",
                                font_family="'Space Grotesk', sans-serif",
                                font_weight="800",
                                font_size="28px",
                            ),
                            padding="24px",
                            border=f"1px solid {ACCENT}",
                            margin_top="16px",
                        ),
                    ),
                    padding="0 48px 60px",
                ),
            ),

            max_width="900px",
            margin="0 auto",
        ),

        background=BACKGROUND,
        min_height="100vh",
    )
