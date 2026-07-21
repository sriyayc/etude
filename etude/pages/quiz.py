"""Quiz Page — /resources/[semester]/[subject_slug]/quiz"""

import reflex as rx

from etude.components.ai_sidebar import ai_sidebar
from etude.components.topbar import topbar
from etude.components import ui
from etude.state import QuizState, ResourceState, UserState
from etude.styles import theme as t


def panel_header(back_label: str, on_back, right_label: str) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("chevron-left", size=16, color=t.TEXT_MUTED),
            rx.text(back_label, color=t.TEXT_BODY, font_size="13px", font_weight="500"),
            spacing="1",
            on_click=on_back,
            cursor="pointer",
            align_items="center",
            _hover={"color": t.ACCENT_STRONG},
        ),
        rx.spacer(),
        ui.badge(right_label, tone="accent"),
        width="100%",
        padding="14px 32px",
        border_bottom=f"1px solid {t.BORDER}",
        align_items="center",
        background=t.BG_CARD,
    )


def unit_card(unit: rx.Var) -> rx.Component:
    return ui.card(
        rx.hstack(
            ui.badge("Unit " + unit["unit_number"].to_string(), tone="accent"),
            rx.spacer(),
            rx.icon("chevron-right", size=16, color=t.TEXT_MUTED),
            width="100%",
            align_items="center",
        ),
        rx.text(
            unit["unit_title"],
            color=t.TEXT,
            font_family=t.FONT_DISPLAY,
            font_weight="700",
            font_size="18px",
            margin_top="12px",
            line_height="1.25",
        ),
        rx.text(
            unit["topic_count"].to_string() + " slides",
            color=t.TEXT_MUTED,
            font_size="13px",
            margin_top="12px",
        ),
        on_click=QuizState.generate_quiz(unit["unit_number"], unit["unit_title"], unit["document_id"]),
        hover=True,
        cursor="pointer",
        height="100%",
    )


def option_button(option: rx.Var) -> rx.Component:
    is_selected = QuizState.selected_answer == option
    return rx.box(
        rx.text(option, color=rx.cond(is_selected, t.ACCENT_STRONG, t.TEXT_BODY), font_size="15px", font_weight="500"),
        on_click=QuizState.select_answer(option),
        border=f"1px solid {rx.cond(is_selected, t.ACCENT, t.BORDER)}",
        background=rx.cond(is_selected, t.ACCENT_SOFT, t.BG_CARD),
        border_radius=t.RADIUS_MD,
        padding="15px 16px",
        cursor="pointer",
        transition="all .12s ease",
        _hover={"border_color": t.ACCENT},
        width="100%",
        margin_bottom="10px",
    )


def _review_option(item: rx.Var, i: int, letter: str) -> rx.Component:
    correct = item["options"][i] == item["answer"]
    return rx.box(
        rx.hstack(
            rx.text(
                letter + ".  ", item["options"][i],
                color=rx.cond(correct, t.SUCCESS, t.TEXT_BODY),
                font_size="14px",
                font_weight=rx.cond(correct, "600", "400"),
            ),
            rx.spacer(),
            rx.cond(correct, rx.icon("check", size=15, color=t.SUCCESS), rx.fragment()),
            width="100%",
            align_items="center",
        ),
        border=f"1px solid {rx.cond(correct, t.SUCCESS, t.BORDER)}",
        background=rx.cond(correct, t.SUCCESS_SOFT, t.BG_CARD),
        border_radius=t.RADIUS_SM,
        padding="11px 14px",
        width="100%",
    )


def result_question_card(item: rx.Var, idx: int) -> rx.Component:
    return ui.card(
        rx.text(
            "Q" + (idx + 1).to_string() + ".  ", item["question"],
            color=t.TEXT,
            font_size="15px",
            font_family=t.FONT_DISPLAY,
            font_weight="700",
            line_height="1.4",
        ),
        rx.vstack(
            _review_option(item, 0, "A"),
            _review_option(item, 1, "B"),
            _review_option(item, 2, "C"),
            _review_option(item, 3, "D"),
            width="100%",
            margin_top="14px",
            spacing="2",
        ),
        rx.box(
            rx.text(
                "Explanation  ",
                rx.text.span(item["explanation"], color=t.TEXT_BODY, font_weight="400"),
                color=t.ACCENT_STRONG,
                font_size="13px",
                font_weight="600",
            ),
            margin_top="16px",
            border_top=f"1px solid {t.BORDER}",
            padding_top="14px",
            width="100%",
        ),
        margin_bottom="16px",
        width="100%",
    )


def quiz_results_view() -> rx.Component:
    return rx.vstack(
        panel_header("Back to units", QuizState.back_to_units, "Quiz review"),
        rx.box(
            rx.vstack(
                ui.eyebrow("Score achieved"),
                rx.heading(
                    QuizState.score.to_string() + " / " + QuizState.questions.length().to_string(),
                    color=t.ACCENT_STRONG,
                    font_family=t.FONT_DISPLAY,
                    font_weight="700",
                    font_size="56px",
                    margin_y="8px",
                ),
                rx.text(
                    "Attempt saved · +" + (QuizState.score * 100).to_string() + " points",
                    color=t.TEXT_MUTED,
                    font_size="14px",
                ),
                align_items="center",
                spacing="0",
            ),
            width="100%",
            padding="40px",
            background=t.BG_CARD,
            border_bottom=f"1px solid {t.BORDER}",
        ),
        rx.box(
            rx.text(
                "Question by question",
                color=t.TEXT,
                font_weight="600",
                font_size="16px",
                margin_bottom="16px",
            ),
            rx.foreach(QuizState.questions, lambda q, idx: result_question_card(q, idx)),
            rx.hstack(
                ui.primary_button("Retake quiz", icon="rotate-ccw", on_click=QuizState.retake_quiz),
                ui.ghost_button("Choose another unit", on_click=QuizState.back_to_units),
                spacing="3",
                margin_top="8px",
            ),
            width="100%",
            padding="32px 40px 48px",
            max_width="760px",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
        overflow_y="auto",
    )


def quiz_view() -> rx.Component:
    return rx.vstack(
        panel_header("Quit quiz", QuizState.back_to_units, QuizState.progress_label),
        rx.box(
            rx.vstack(
                ui.eyebrow(
                    "Question " + (QuizState.current_index + 1).to_string()
                    + " of " + QuizState.questions.length().to_string()
                ),
                rx.heading(
                    QuizState.current_question["question"],
                    color=t.TEXT,
                    font_family=t.FONT_DISPLAY,
                    font_weight="700",
                    font_size="26px",
                    line_height="1.3",
                    margin_top="10px",
                ),
                align_items="start",
                spacing="0",
                margin_bottom="28px",
            ),
            rx.box(
                rx.foreach(QuizState.current_question_options, option_button),
                width="100%",
            ),
            rx.hstack(
                rx.hstack(
                    rx.icon("chevron-left", size=16),
                    rx.text("Previous", font_size="14px", font_weight="500"),
                    spacing="1",
                    on_click=QuizState.prev_question,
                    cursor="pointer",
                    align_items="center",
                    color=rx.cond(QuizState.current_index > 0, t.TEXT_BODY, t.BORDER_STRONG),
                ),
                rx.spacer(),
                rx.cond(
                    QuizState.is_last_question,
                    ui.primary_button("Submit quiz", icon="check", on_click=QuizState.submit_quiz),
                    rx.box(
                        rx.hstack(
                            rx.text("Next", font_size="14px", font_weight="600"),
                            rx.icon("chevron-right", size=16),
                            spacing="1",
                            align_items="center",
                        ),
                        on_click=QuizState.next_question,
                        cursor="pointer",
                        color=t.ACCENT_STRONG,
                    ),
                ),
                width="100%",
                margin_top="28px",
                padding_top="20px",
                border_top=f"1px solid {t.BORDER}",
                align_items="center",
            ),
            width="100%",
            max_width="720px",
            padding="40px",
        ),
        flex="1",
        width="100%",
        align_items="start",
        spacing="0",
        overflow_y="auto",
    )


def unit_picker() -> rx.Component:
    return rx.box(
        rx.vstack(
            ui.eyebrow(ResourceState.current_subject["subject_name"].to(str) + " · self assessment"),
            ui.heading("Take a quiz", size="34px", margin_top="6px"),
            ui.subtext(
                "Pick a syllabus unit to generate a 5-question test grounded in your syllabus.",
                margin_top="8px",
            ),
            align_items="start",
            spacing="0",
            margin_bottom="28px",
        ),
        rx.cond(
            QuizState.quiz_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(color=t.ACCENT, size="3"),
                    rx.text("Generating quiz questions…", color=t.TEXT, font_weight="600", font_size="15px"),
                    rx.text("Grounding in syllabus topics — up to 20 seconds.", color=t.TEXT_MUTED, font_size="13px"),
                    spacing="3",
                    align_items="center",
                ),
                width="100%",
                height="360px",
            ),
            rx.cond(
                QuizState.units_error != "",
                rx.center(
                    rx.vstack(
                        rx.icon("triangle-alert", size=26, color=t.ERROR),
                        rx.text(QuizState.units_error, color=t.ERROR, font_size="14px"),
                        spacing="2",
                        align_items="center",
                    ),
                    width="100%",
                    height="280px",
                ),
                rx.grid(
                    rx.foreach(QuizState.units, unit_card),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="4",
                    align_items="stretch",
                ),
            ),
        ),
        width="100%",
        padding="40px",
        overflow_y="auto",
        # max-width on a flex item leaves a dead gutter beside the sidebar.
        flex="1",
        min_width="0",
    )


def quiz_page() -> rx.Component:
    return rx.box(
        topbar(
            trail=[
                ("Resources", "/dashboard"),
                ("Semester " + ResourceState.semester, f"/resources/{ResourceState.semester}"),
                (ResourceState.current_subject["subject_name"], f"/resources/{ResourceState.semester}/{ResourceState.subject_slug}"),
                ("Quiz", None),
            ],
            active="resources",
            srn=UserState.srn,
        ),
        rx.hstack(
            rx.cond(
                QuizState.has_quiz,
                rx.cond(QuizState.submitted, quiz_results_view(), quiz_view()),
                unit_picker(),
            ),
            ai_sidebar(
                context_suffix="quiz",
                welcome_text=(
                    "I'm Etude AI — grounded in your syllabus. Ask me about any "
                    "quiz question or topic and I'll explain it step by step."
                ),
                suggestions=[
                    (
                        "Help me with this unit",
                        rx.cond(
                            QuizState.selected_unit_title != "",
                            f"Explain the key concepts tested in "
                            f"{QuizState.selected_unit_title} for "
                            f"{ResourceState.current_subject['subject_name']}",
                            f"Explain the key concepts covered in "
                            f"{ResourceState.current_subject['subject_name']}",
                        ),
                    ),
                    (
                        "Common pitfalls?",
                        f"What are common pitfalls or misconceptions "
                        f"students have when studying "
                        f"{ResourceState.current_subject['subject_name']}?",
                    ),
                ],
            ),
            width="100%",
            spacing="0",
            align_items="stretch",
            height="calc(100vh - 61px)",
        ),
        background=t.BG_PAGE,
        min_height="100vh",
        font_family=t.FONT_BODY,
        on_mount=QuizState.load_units,
    )
