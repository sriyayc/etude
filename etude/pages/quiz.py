"""Per-unit quiz — /resources/[semester]/[subject_code]/quiz"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import QuizState, UserState, ResourceState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
GOOD = "#4ADE80"
BAD = "#F87171"


def unit_card(unit: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(
            f"UNIT ", unit["unit_number"],
            color=ACCENT, font_family="monospace", font_size="11px", letter_spacing="0.15em",
        ),
        rx.heading(
            unit["unit_title"], color="white",
            font_family="'Space Grotesk', sans-serif", font_weight="700", font_size="20px",
            margin_top="8px",
        ),
        rx.text(
            unit["topic_count"], " topics",
            color=ACCENT_LIGHT, font_family="monospace", font_size="12px", margin_top="6px",
        ),
        rx.hstack(
            rx.text("GENERATE QUIZ", font_family="monospace", font_size="12px"),
            rx.icon("arrow-right", size=14),
            spacing="1",
            color=ACCENT,
            margin_top="20px",
        ),
        on_click=QuizState.generate_quiz(unit["unit_title"]),
        border=f"1px solid {BORDER}",
        padding="24px",
        cursor="pointer",
        _hover={"bg": "#0A2647", "border_color": ACCENT},
        transition="background .15s ease",
    )


def unit_picker() -> rx.Component:
    return rx.vstack(
        rx.text(
            "// pick a unit to quiz yourself on",
            color=ACCENT_LIGHT, font_family="monospace", font_size="12px",
            padding="0 48px",
        ),
        rx.cond(
            QuizState.units_error != "",
            rx.center(
                rx.text(QuizState.units_error, color=ACCENT_LIGHT, font_family="monospace"),
                padding="80px 0", width="100%",
            ),
            rx.grid(
                rx.foreach(QuizState.units, unit_card),
                columns="3", spacing="4", width="100%", padding="24px 48px 60px",
            ),
        ),
        align_items="start", width="100%", padding_top="24px",
    )


def option_button(option: rx.Var) -> rx.Component:
    is_selected = option == QuizState.selected_answer
    is_correct_option = option == QuizState.current_question["answer"]

    border_color = rx.cond(
        QuizState.submitted,
        rx.cond(is_correct_option, GOOD, rx.cond(is_selected, BAD, BORDER)),
        rx.cond(is_selected, ACCENT, BORDER),
    )
    bg_color = rx.cond(
        QuizState.submitted,
        rx.cond(is_correct_option, "rgba(74,222,128,0.12)", rx.cond(is_selected, "rgba(248,113,113,0.12)", "transparent")),
        rx.cond(is_selected, "rgba(93,138,168,0.15)", "transparent"),
    )

    return rx.box(
        rx.text(option, color="white", font_size="14px"),
        on_click=QuizState.select_answer(option),
        padding="14px 18px",
        border=f"1px solid {border_color}",
        background=bg_color,
        cursor=rx.cond(QuizState.submitted, "default", "pointer"),
        margin_bottom="10px",
        width="100%",
        transition="background .15s ease",
    )


def question_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(QuizState.selected_unit_title, color="white", font_size="15px", font_weight="600"),
            rx.spacer(),
            rx.text(QuizState.progress_label, color=ACCENT_LIGHT, font_family="monospace", font_size="12px"),
            width="100%", padding="20px 48px", border_bottom=f"1px solid {BORDER}", align_items="center",
        ),
        rx.vstack(
            rx.text(
                QuizState.current_question["question"],
                color="white", font_size="20px", font_weight="700", line_height="1.5",
                margin_bottom="24px",
            ),
            rx.foreach(QuizState.current_question_options, option_button),
            align_items="start", width="100%", max_width="720px", padding="40px 48px",
        ),
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=14), rx.text("PREV", font_family="monospace", font_size="12px"),
                spacing="1", on_click=QuizState.prev_question, cursor="pointer", color=ACCENT_LIGHT,
            ),
            rx.spacer(),
            rx.cond(
                QuizState.is_last_question,
                rx.button(
                    "SUBMIT QUIZ", on_click=QuizState.submit_quiz,
                    bg=ACCENT, color="black", font_family="monospace", font_size="12px",
                    border_radius="0", padding="10px 20px",
                ),
                rx.hstack(
                    rx.text("NEXT", font_family="monospace", font_size="12px"),
                    rx.icon("chevron-right", size=14),
                    spacing="1", on_click=QuizState.next_question, cursor="pointer", color=ACCENT_LIGHT,
                ),
            ),
            width="100%", max_width="720px", padding="16px 48px",
        ),
        align_items="start", width="100%",
    )


def review_row(question: rx.Var, index: int) -> rx.Component:
    user_answer = QuizState.answers[index]
    correct_answer = question["answer"]
    is_correct = user_answer == correct_answer

    return rx.box(
        rx.hstack(
            rx.icon(
                rx.cond(is_correct, "check-circle", "x-circle"),
                color=rx.cond(is_correct, GOOD, BAD), size=16,
            ),
            rx.text(question["question"], color="white", font_size="14px", font_weight="600"),
            spacing="2", align_items="start",
        ),
        rx.text(
            "your answer: ", user_answer,
            color=rx.cond(is_correct, GOOD, BAD), font_family="monospace", font_size="12px", margin_top="10px",
        ),
        rx.cond(
            ~is_correct,
            rx.text("correct answer: ", correct_answer, color=GOOD, font_family="monospace", font_size="12px"),
            rx.fragment(),
        ),
        rx.text(question["explanation"], color=ACCENT_LIGHT, font_size="13px", margin_top="10px", line_height="1.6"),
        border=f"1px solid {BORDER}", padding="20px", margin_bottom="12px", width="100%",
    )


def results_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("QUIZ COMPLETE", color=ACCENT, font_family="monospace", font_size="12px", letter_spacing="0.15em"),
                rx.heading(
                    QuizState.score, " / ", QuizState.questions.length(),
                    color="white", font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="44px",
                ),
                align_items="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.box(
                    rx.text("RETAKE", font_family="monospace", font_size="12px"),
                    on_click=QuizState.retake_quiz, cursor="pointer", color=ACCENT_LIGHT,
                    border=f"1px solid {BORDER}", padding="10px 16px", _hover={"color": "white"},
                ),
                rx.box(
                    rx.text("ANOTHER UNIT", font_family="monospace", font_size="12px"),
                    on_click=QuizState.back_to_units, cursor="pointer", color=ACCENT_LIGHT,
                    border=f"1px solid {BORDER}", padding="10px 16px", _hover={"color": "white"},
                ),
                spacing="3",
            ),
            width="100%", padding="32px 48px", border_bottom=f"1px solid {BORDER}", align_items="center",
        ),
        rx.vstack(
            rx.foreach(QuizState.questions, review_row),
            width="100%", max_width="800px", padding="32px 48px",
        ),
        align_items="start", width="100%",
    )


def quiz_page() -> rx.Component:
    return rx.box(
        topbar(breadcrumb="quiz", active="resources", srn=UserState.srn),
        rx.box(
            rx.vstack(
                rx.text(
                    ResourceState.subject_code, color=ACCENT, font_family="monospace",
                    font_size="12px", letter_spacing="0.1em",
                ),
                rx.heading(
                    "Quiz yourself.", color="white",
                    font_family="'Space Grotesk', sans-serif", font_weight="800", font_size="40px",
                ),
                align_items="start", padding="48px 48px 0",
            ),
            rx.cond(
                QuizState.quiz_loading,
                rx.center(
                    rx.text("generating quiz…", color=ACCENT_LIGHT, font_family="monospace"),
                    padding="120px 0", width="100%",
                ),
                rx.cond(
                    QuizState.quiz_error != "",
                    rx.vstack(
                        rx.center(
                            rx.text(QuizState.quiz_error, color=BAD, font_family="monospace"),
                            padding="60px 0", width="100%",
                        ),
                        rx.box(
                            rx.text("← BACK TO UNITS", font_family="monospace", font_size="12px"),
                            on_click=QuizState.back_to_units, cursor="pointer", color=ACCENT,
                        ),
                        align_items="center", width="100%",
                    ),
                    rx.cond(
                        QuizState.has_quiz,
                        rx.cond(QuizState.submitted, results_view(), question_view()),
                        unit_picker(),
                    ),
                ),
            ),
            max_width="1600px", margin="0 auto",
        ),
        bg=BACKGROUND, min_height="100vh",
        on_mount=[ResourceState.load_subject, QuizState.load_units],
    )
