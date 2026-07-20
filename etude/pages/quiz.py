"""Quiz Page — /resources/[semester]/[subject_code]/quiz"""

import reflex as rx

from etude.components.topbar import topbar
from etude.state import QuizState, ResourceState, UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"
PANEL_BG = "#0A2647"


def chat_bubble(message: rx.Var) -> rx.Component:
    """Render one AI or user chat message."""
    is_user = message["role"] == "user"

    return rx.box(
        rx.text(
            message["content"],
            color="white",
            font_size="14px",
            line_height="1.5",
            white_space="pre-wrap",
        ),
        background=rx.cond(
            is_user,
            "rgba(93, 138, 168, 0.12)",
            "transparent",
        ),
        border=rx.cond(
            is_user,
            f"1px solid {BORDER}",
            "none",
        ),
        padding="12px",
        margin_bottom="10px",
        width="100%",
    )


def suggestion_chip(text: str) -> rx.Component:
    """Render a preset question button."""
    return rx.box(
        rx.text(text),
        on_click=ResourceState.ask_ai(text),
        cursor="pointer",
        border=f"1px solid {BORDER}",
        color=ACCENT_LIGHT,
        font_family="monospace",
        font_size="12px",
        padding="8px 12px",
        _hover={
            "border_color": ACCENT,
            "color": "white",
        },
    )


def unit_card(unit: rx.Var) -> rx.Component:
    """Render one unit card for selection."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    f"UNIT {unit['unit_number']}",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="11px",
                    letter_spacing="0.1em",
                ),
                rx.spacer(),
                rx.icon("chevron-right", size=14, color=ACCENT_LIGHT),
                width="100%",
            ),
            rx.heading(
                unit["unit_title"],
                color="white",
                font_family="'Space Grotesk', sans-serif",
                font_weight="700",
                font_size="20px",
                margin_top="10px",
                line_height="1.2",
            ),
            rx.text(
                f"{unit['topic_count']} topics defined in syllabus",
                color=ACCENT_LIGHT,
                font_family="monospace",
                font_size="12px",
                margin_top="16px",
            ),
            align_items="start",
            width="100%",
        ),
        on_click=QuizState.generate_quiz(unit["unit_title"]),
        padding="24px",
        border=f"1px solid {BORDER}",
        cursor="pointer",
        _hover={
            "background": "rgba(93,138,168,0.06)",
            "border_color": ACCENT,
        },
        height="180px",
    )


def option_button(option: rx.Var) -> rx.Component:
    """Render one MCQ option."""
    is_selected = QuizState.selected_answer == option

    return rx.box(
        rx.text(
            option,
            color=rx.cond(is_selected, "white", "#B4C6D0"),
            font_size="14px",
        ),
        on_click=QuizState.select_answer(option),
        border=f"1px solid {rx.cond(is_selected, ACCENT, BORDER)}",
        background=rx.cond(is_selected, "rgba(93, 138, 168, 0.12)", "transparent"),
        padding="16px",
        cursor="pointer",
        _hover={"border_color": ACCENT},
        width="100%",
        margin_bottom="10px",
    )


def result_question_card(item: rx.Var, idx: int) -> rx.Component:
    """Render one review question card. Avoids rx.foreach over Any-typed options."""
    correct_ans = item["answer"]

    return rx.vstack(
        rx.heading(
            rx.text.span("Q"),
            rx.text.span(idx + 1),
            rx.text.span(": "),
            rx.text.span(item["question"]),
            color="white",
            font_size="15px",
            font_family="'Space Grotesk', sans-serif",
            font_weight="700",
        ),
        # Static list of 4 labelled option slots — avoids foreach-over-Any
        rx.vstack(
            rx.box(
                rx.hstack(
                    rx.text("A: ", item["options"][0], color=rx.cond(item["options"][0] == correct_ans, "#22C55E", "#7393B3"), font_size="14px"),
                    rx.spacer(),
                    rx.cond(item["options"][0] == correct_ans, rx.icon("check", size=14, color="#22C55E"), rx.fragment()),
                    width="100%",
                ),
                border=rx.cond(item["options"][0] == correct_ans, "1px solid #22C55E", f"1px solid {BORDER}"),
                background=rx.cond(item["options"][0] == correct_ans, "rgba(34, 197, 94, 0.08)", "transparent"),
                padding="12px", width="100%",
            ),
            rx.box(
                rx.hstack(
                    rx.text("B: ", item["options"][1], color=rx.cond(item["options"][1] == correct_ans, "#22C55E", "#7393B3"), font_size="14px"),
                    rx.spacer(),
                    rx.cond(item["options"][1] == correct_ans, rx.icon("check", size=14, color="#22C55E"), rx.fragment()),
                    width="100%",
                ),
                border=rx.cond(item["options"][1] == correct_ans, "1px solid #22C55E", f"1px solid {BORDER}"),
                background=rx.cond(item["options"][1] == correct_ans, "rgba(34, 197, 94, 0.08)", "transparent"),
                padding="12px", width="100%",
            ),
            rx.box(
                rx.hstack(
                    rx.text("C: ", item["options"][2], color=rx.cond(item["options"][2] == correct_ans, "#22C55E", "#7393B3"), font_size="14px"),
                    rx.spacer(),
                    rx.cond(item["options"][2] == correct_ans, rx.icon("check", size=14, color="#22C55E"), rx.fragment()),
                    width="100%",
                ),
                border=rx.cond(item["options"][2] == correct_ans, "1px solid #22C55E", f"1px solid {BORDER}"),
                background=rx.cond(item["options"][2] == correct_ans, "rgba(34, 197, 94, 0.08)", "transparent"),
                padding="12px", width="100%",
            ),
            rx.box(
                rx.hstack(
                    rx.text("D: ", item["options"][3], color=rx.cond(item["options"][3] == correct_ans, "#22C55E", "#7393B3"), font_size="14px"),
                    rx.spacer(),
                    rx.cond(item["options"][3] == correct_ans, rx.icon("check", size=14, color="#22C55E"), rx.fragment()),
                    width="100%",
                ),
                border=rx.cond(item["options"][3] == correct_ans, "1px solid #22C55E", f"1px solid {BORDER}"),
                background=rx.cond(item["options"][3] == correct_ans, "rgba(34, 197, 94, 0.08)", "transparent"),
                padding="12px", width="100%",
            ),
            width="100%",
            margin_top="12px",
            spacing="1",
        ),
        rx.box(
            rx.text(
                "Explanation: ",
                rx.text.span(item["explanation"], color="#B4C6D0"),
                color=ACCENT,
                font_family="monospace",
                font_size="12px",
            ),
            margin_top="16px",
            border_top=f"1px solid {BORDER}",
            padding_top="12px",
            width="100%",
        ),
        width="100%",
        border=f"1px solid {BORDER}",
        padding="24px",
        margin_bottom="20px",
        align_items="start",
    )


def quiz_results_view() -> rx.Component:
    """Render the results of the completed quiz."""
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=14, color=ACCENT_LIGHT),
                rx.text(
                    "BACK TO UNITS",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="12px",
                ),
                spacing="1",
                on_click=QuizState.back_to_units,
                cursor="pointer",
                _hover={"color": "white"},
            ),
            rx.spacer(),
            rx.text(
                "QUIZ REVIEW",
                color=ACCENT,
                font_family="monospace",
                font_size="12px",
                letter_spacing="0.1em",
            ),
            width="100%",
            padding="14px 24px",
            border_bottom=f"1px solid {BORDER}",
            align_items="center",
        ),

        rx.vstack(
            # Result Score Banner
            rx.vstack(
                rx.text(
                    "SCORE ACHIEVED",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="12px",
                    letter_spacing="0.2em",
                ),
                rx.heading(
                    f"{QuizState.score} / {QuizState.questions.length()}",
                    color="white",
                    font_family="'Space Grotesk', sans-serif",
                    font_weight="800",
                    font_size="60px",
                    margin_y="10px",
                ),
                rx.hstack(
                    rx.box(
                        "completed",
                        border=f"1px solid {ACCENT}",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="11px",
                        padding="3px 8px",
                    ),
                    rx.text(
                        f"Attempt saved to leaderboard profile · +{QuizState.score * 100} points",
                        color=ACCENT_LIGHT,
                        font_family="monospace",
                        font_size="12px",
                    ),
                    spacing="3",
                    align_items="center",
                ),
                align_items="center",
                width="100%",
                padding="40px",
                border_bottom=f"1px solid {BORDER}",
                background="rgba(93, 138, 168, 0.04)",
            ),

            # Question Review list
            rx.vstack(
                rx.text(
                    "QUESTION BY QUESTION ANALYSIS",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="12px",
                    letter_spacing="0.1em",
                    margin_bottom="16px",
                ),
                # We can map each question in the list
                rx.foreach(
                    QuizState.questions,
                    lambda q, idx: result_question_card(q, idx)
                ),
                width="100%",
                align_items="start",
                padding="40px",
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    "Retake Quiz",
                    on_click=QuizState.retake_quiz,
                    background=ACCENT,
                    color="black",
                    font_family="monospace",
                    font_size="12px",
                    border_radius="0",
                    padding="12px 24px",
                    cursor="pointer",
                    _hover={"opacity": 0.8},
                ),
                rx.button(
                    "Choose Another Unit",
                    on_click=QuizState.back_to_units,
                    background="transparent",
                    border=f"1px solid {BORDER}",
                    color="white",
                    font_family="monospace",
                    font_size="12px",
                    border_radius="0",
                    padding="12px 24px",
                    cursor="pointer",
                    _hover={"background": "rgba(255,255,255,0.05)"},
                ),
                spacing="3",
                padding="0 40px 40px",
            ),
            width="100%",
            align_items="start",
            spacing="0",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
        overflow_y="auto",
    )


def quiz_view() -> rx.Component:
    """Render the active quiz viewer."""
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("chevron-left", size=14, color=ACCENT_LIGHT),
                rx.text(
                    "QUIT QUIZ",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="12px",
                ),
                spacing="1",
                on_click=QuizState.back_to_units,
                cursor="pointer",
                _hover={"color": "white"},
            ),
            rx.spacer(),
            rx.text(
                QuizState.progress_label,
                color=ACCENT,
                font_family="monospace",
                font_size="12px",
                letter_spacing="0.1em",
            ),
            width="100%",
            padding="14px 24px",
            border_bottom=f"1px solid {BORDER}",
            align_items="center",
        ),

        rx.vstack(
            rx.vstack(
                rx.text(
                    f"QUESTION {QuizState.current_index + 1} OF {QuizState.questions.length()}",
                    color=ACCENT,
                    font_family="monospace",
                    font_size="11px",
                    letter_spacing="0.2em",
                ),
                rx.heading(
                    QuizState.current_question["question"],
                    color="white",
                    font_family="'Space Grotesk', sans-serif",
                    font_weight="800",
                    font_size="28px",
                    margin_top="10px",
                ),
                align_items="start",
                padding="40px",
                width="100%",
            ),

            # Options
            rx.box(
                rx.foreach(
                    QuizState.current_question_options,
                    option_button
                ),
                padding_x="40px",
                width="100%",
            ),

            # Footer / Navigation
            rx.hstack(
                rx.hstack(
                    rx.icon("chevron-left", size=14),
                    rx.text("PREV", font_family="monospace", font_size="12px"),
                    spacing="1",
                    on_click=QuizState.prev_question,
                    cursor="pointer",
                    color=rx.cond(QuizState.current_index > 0, ACCENT_LIGHT, "rgba(255,255,255,0.15)"),
                ),

                rx.spacer(),

                rx.cond(
                    QuizState.is_last_question,
                    rx.button(
                        "SUBMIT QUIZ",
                        on_click=QuizState.submit_quiz,
                        background=ACCENT,
                        color="black",
                        font_family="monospace",
                        font_size="12px",
                        border_radius="0",
                        padding="8px 20px",
                        cursor="pointer",
                        _hover={"opacity": 0.8},
                    ),
                    rx.hstack(
                        rx.text("NEXT", font_family="monospace", font_size="12px"),
                        rx.icon("chevron-right", size=14),
                        spacing="1",
                        on_click=QuizState.next_question,
                        cursor="pointer",
                        color=ACCENT_LIGHT,
                    ),
                ),
                width="100%",
                padding="30px 40px",
                border_top=f"1px solid {BORDER}",
                margin_top="40px",
                align_items="center",
            ),
            width="100%",
            align_items="start",
            spacing="0",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
        overflow_y="auto",
    )


def quiz_page() -> rx.Component:
    """Render the quiz page."""
    return rx.box(
        topbar(
            breadcrumb="quiz",
            active="resources",
            srn=UserState.srn,
        ),

        rx.hstack(
            # Left panel - picker, active quiz, or results
            rx.cond(
                QuizState.has_quiz,
                rx.cond(
                    QuizState.submitted,
                    quiz_results_view(),
                    quiz_view()
                ),
                rx.vstack(
                    rx.vstack(
                        rx.text(
                            f"// {ResourceState.subject_code} · SELF ASSESSMENT",
                            color=ACCENT,
                            font_family="monospace",
                            font_size="11px",
                            letter_spacing="0.2em",
                        ),
                        rx.heading(
                            "Jump to Quiz.",
                            color="white",
                            font_family="'Space Grotesk', sans-serif",
                            font_weight="800",
                            font_size="44px",
                        ),
                        rx.text(
                            "Select a syllabus unit below to generate a dynamic 5-question test bound to your syllabus.",
                            color=ACCENT_LIGHT,
                            font_size="15px",
                        ),
                        align_items="start",
                        spacing="2",
                        padding="48px 48px 24px",
                    ),

                    rx.cond(
                        QuizState.quiz_loading,
                        rx.center(
                            rx.vstack(
                                rx.text(
                                    "GENERATING QUIZ QUESTIONS...",
                                    color=ACCENT,
                                    font_family="monospace",
                                    font_size="13px",
                                    letter_spacing="0.1em",
                                ),
                                rx.text(
                                    "Using syllabus topics to ground questions. This might take up to 20 seconds...",
                                    color=ACCENT_LIGHT,
                                    font_size="12px",
                                ),
                                rx.spinner(color=ACCENT, size="3"),
                                spacing="3",
                                align_items="center",
                            ),
                            width="100%",
                            height="400px",
                        ),
                        rx.cond(
                            QuizState.units_error != "",
                            rx.center(
                                rx.vstack(
                                    rx.icon("alert-triangle", size=24, color="#FF8A8A"),
                                    rx.text(
                                        QuizState.units_error,
                                        color="#FF8A8A",
                                        font_family="monospace",
                                        font_size="13px",
                                    ),
                                    spacing="2",
                                    align_items="center",
                                ),
                                width="100%",
                                height="300px",
                            ),
                            rx.grid(
                                rx.foreach(
                                    QuizState.units,
                                    unit_card,
                                ),
                                columns="2",
                                spacing="3",
                                padding="0 48px 48px",
                                width="100%",
                            ),
                        ),
                    ),
                    flex="1",
                    align_items="start",
                    spacing="0",
                    width="100%",
                    overflow_y="auto",
                ),
            ),

            # Right panel - Grounded AI Sidebar
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=14, color=ACCENT),
                    rx.text(
                        "ETUDE AI",
                        color="white",
                        font_weight="700",
                        font_size="14px",
                    ),
                    rx.box(
                        "grounded",
                        background="rgba(93, 138, 168, 0.2)",
                        color=ACCENT,
                        font_family="monospace",
                        font_size="10px",
                        padding="2px 6px",
                        margin_left="6px",
                    ),
                    width="100%",
                    padding="14px",
                    border_bottom=f"1px solid {BORDER}",
                    align_items="center",
                ),

                rx.text(
                    "CONTEXT",
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="10px",
                    padding="14px 14px 0",
                ),

                rx.text(
                    ResourceState.subject_code,
                    " · quiz",
                    color="white",
                    font_family="monospace",
                    font_size="13px",
                    padding="0 14px 14px",
                ),

                rx.vstack(
                    rx.foreach(
                        ResourceState.chat_messages,
                        chat_bubble,
                    ),

                    rx.cond(
                        ResourceState.chat_messages.length() == 0,
                        rx.box(
                            rx.text(
                                "I'm Etude AI — strictly grounded in your syllabus. Ask me anything about the quiz or questions. I'll explain any topic step by step.",
                                color="white",
                                font_size="13px",
                                line_height="1.6",
                            ),
                            background="rgba(93, 138, 168, 0.1)",
                            border=f"1px solid {BORDER}",
                            padding="14px",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),

                    rx.cond(
                        ResourceState.ai_thinking,
                        rx.text(
                            "thinking…",
                            color=ACCENT_LIGHT,
                            font_family="monospace",
                            font_size="12px",
                        ),
                        rx.fragment(),
                    ),

                    width="100%",
                    padding="0 14px",
                    flex="1",
                    overflow_y="auto",
                    align_items="start",
                ),

                rx.hstack(
                    suggestion_chip("Help me with MCQ"),
                    suggestion_chip("Explain concepts"),
                    spacing="2",
                    padding="10px 14px",
                    flex_wrap="wrap",
                ),

                rx.hstack(
                    rx.input(
                        placeholder="Ask anything from your syllabus…",
                        value=ResourceState.chat_input,
                        on_change=ResourceState.set_chat_input,
                        background="black",
                        border=f"1px solid {BORDER}",
                        color="white",
                        font_family="monospace",
                        font_size="13px",
                        flex="1",
                    ),
                    rx.icon(
                        "send",
                        size=16,
                        color=ACCENT,
                        cursor="pointer",
                        on_click=ResourceState.ask_ai(""),
                    ),
                    width="100%",
                    padding="14px",
                    border_top=f"1px solid {BORDER}",
                    align_items="center",
                ),

                width="420px",
                min_width="420px",
                background="#050D18",
                border_left=f"1px solid {BORDER}",
                align_items="start",
                spacing="0",
                height="100%",
            ),

            width="100%",
            spacing="0",
            align_items="stretch",
            height="calc(100vh - 72px)", # Height minus topbar
        ),

        background=BACKGROUND,
        min_height="100vh",
        on_mount=QuizState.load_units,
    )
