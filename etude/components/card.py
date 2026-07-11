import reflex as rx

from ..styles import theme


def app_card(*children, width: str = "470px"):
    """Sharp-cornered black card with a hairline slate border —
    matches the sign-in card and the feature grid cells.
    No blur, no glow, no rounding."""
    return rx.box(
        *children,
        width=width,
        padding="36px",
        background=theme.CARD,
        border=f"1px solid {theme.BORDER}",
        border_radius=theme.CARD_RADIUS,  # "0px"
    )


def feature_cell(label: str, value: str):
    """Small bordered cell used in the 2x2 RAG / CITATIONS / QUIZZES / RANK grid."""
    return rx.box(
        rx.text(
            label.upper(),
            font_family=theme.FONT_MONO,
            font_size="11px",
            letter_spacing="0.08em",
            color=theme.PRIMARY,
            margin_bottom="4px",
        ),
        rx.text(
            value,
            color=theme.TEXT,
            font_weight="600",
            font_size="14px",
        ),
        padding="16px",
        border=f"1px solid {theme.BORDER}",
    )
