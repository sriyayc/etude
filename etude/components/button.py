"""Reusable button components."""

import reflex as rx

from ..styles import theme


def primary_button(
    text: str,
    on_click=None,
):
    """Solid slate-blue, sharp-cornered, mono-uppercase button
    matching the etude sign-in button."""

    return rx.button(
        rx.hstack(
            rx.text(
                text.upper(),
                font_family=theme.FONT_MONO,
                font_weight="700",
                letter_spacing="0.08em",
                font_size="14px",
            ),
            rx.icon(
                "arrow-right",
                size=16,
            ),
            spacing="2",
            justify="center",
            align="center",
        ),
        on_click=on_click,
        type="button",
        width="100%",
        height="56px",
        border_radius=theme.INPUT_RADIUS,  # "0px" — sharp corners
        background=theme.PRIMARY,
        color=theme.PRIMARY_TEXT_ON,
        transition="opacity .2s ease",
        _hover={
            "opacity": "0.9",
        },
        # FIX 4: suppress the browser's default blue focus ring on click/tab
        outline="none",
        _focus={
            "outline": "none",
            "box_shadow": "none",
        },
        cursor="pointer",
    )


def secondary_link_button(text: str, href: str = "#"):
    """Text-style link e.g. '→ Create account'."""
    return rx.link(
        text,
        href=href,
        font_family=theme.FONT_MONO,
        font_size="14px",
        color=theme.PRIMARY,
        _hover={"text_decoration": "underline"},
    )
