"""Reusable input components."""

import reflex as rx

from ..styles import theme


def text_input(
    placeholder: str,
    value: str = "",
    on_change=None,
    input_type: str = "text",
):
    """Sharp-cornered black input with hairline slate border,
    mono placeholder, and slate-blue focus ring — matches the
    SRN / password fields on the sign-in page."""
    return rx.input(
        placeholder=placeholder,
        value=value,
        on_change=on_change,
        type=input_type,
        width="100%",
        height="52px",
        padding="0 16px",
        border_radius=theme.INPUT_RADIUS,  # "0px"
        border=f"1px solid {theme.BORDER}",
        background=theme.BACKGROUND,  # pure black
        color=theme.TEXT,
        font_family=theme.FONT_MONO,
        font_size="14px",
        letter_spacing="0.03em",
        _placeholder={
            "color": theme.TEXT_MUTED,
        },
        _focus={
            "border": f"1px solid {theme.PRIMARY}",
            "box_shadow": "none",
            "outline": "none",
        },
    )


def label(text: str):
    """Small uppercase mono label placed above an input,
    e.g. 'SRN' or 'PESU ACADEMY PASSWORD'."""
    return rx.text(
        text.upper(),
        font_family=theme.FONT_MONO,
        font_size="12px",
        letter_spacing="0.08em",
        color=theme.TEXT_MUTED,
        margin_bottom="8px",
    )


def helper_text(text: str):
    """Small helper line under an input, e.g. 'format: PES1UG25CS235'."""
    return rx.text(
        text,
        font_family=theme.FONT_MONO,
        font_size="12px",
        color=theme.TEXT_MUTED,
        margin_top="6px",
        margin_bottom="20px",
    )
