"""Reusable UI primitives for the light design system.

Import these instead of re-styling raw boxes on every page so the look
stays consistent everywhere.
"""

import reflex as rx

from etude.styles import theme as t


def page(*children, **props) -> rx.Component:
    """Full-height app page wrapper: light background + body font."""
    return rx.box(
        *children,
        background=t.BG_PAGE,
        min_height="100vh",
        font_family=t.FONT_BODY,
        color=t.TEXT,
        **props,
    )


def container(*children, **props) -> rx.Component:
    """Centred, max-width content column with page padding."""
    props.setdefault("width", "100%")
    props.setdefault("max_width", "1200px")
    props.setdefault("margin", "0 auto")
    props.setdefault("padding", "40px 32px 64px")
    return rx.box(*children, **props)


def card(*children, hover: bool = False, **props) -> rx.Component:
    """White rounded card with a soft shadow."""
    props.setdefault("background", t.BG_CARD)
    props.setdefault("border", f"1px solid {t.BORDER}")
    props.setdefault("border_radius", t.RADIUS_MD)
    props.setdefault("box_shadow", t.SHADOW_CARD)
    props.setdefault("padding", "24px")
    if hover:
        props.setdefault(
            "transition",
            "box-shadow .18s ease, transform .18s ease, border-color .18s ease",
        )
        props.setdefault(
            "_hover",
            {
                "box_shadow": t.SHADOW_HOVER,
                "transform": "translateY(-2px)",
                "border_color": t.BORDER_STRONG,
            },
        )
    return rx.box(*children, **props)


def badge(text, tone: str = "accent", **props) -> rx.Component:
    """Small pill label."""
    palette = {
        "accent": (t.ACCENT_SOFT, t.ACCENT_STRONG),
        "success": (t.SUCCESS_SOFT, t.SUCCESS),
        "error": (t.ERROR_SOFT, t.ERROR),
        "muted": (t.BG_SUBTLE, t.TEXT_MUTED),
    }
    bg, fg = palette.get(tone, palette["accent"])
    props.setdefault("background", bg)
    props.setdefault("color", fg)
    props.setdefault("padding", "3px 10px")
    props.setdefault("border_radius", t.RADIUS_PILL)
    props.setdefault("font_size", "11px")
    props.setdefault("font_weight", "600")
    props.setdefault("font_family", t.FONT_BODY)
    props.setdefault("letter_spacing", "0.02em")
    props.setdefault("display", "inline-flex")
    props.setdefault("align_items", "center")
    props.setdefault("white_space", "nowrap")
    return rx.box(text, **props)


def eyebrow(text, **props) -> rx.Component:
    """Small uppercase label above a heading."""
    props.setdefault("color", t.ACCENT_STRONG)
    props.setdefault("font_family", t.FONT_MONO)
    props.setdefault("font_size", "12px")
    props.setdefault("font_weight", "600")
    props.setdefault("letter_spacing", "0.14em")
    props.setdefault("text_transform", "uppercase")
    return rx.text(text, **props)


def heading(text, size: str = "36px", **props) -> rx.Component:
    props.setdefault("color", t.TEXT)
    props.setdefault("font_family", t.FONT_DISPLAY)
    props.setdefault("font_weight", "700")
    props.setdefault("font_size", size)
    props.setdefault("line_height", "1.15")
    props.setdefault("letter_spacing", "-0.01em")
    return rx.heading(text, **props)


def subtext(text, **props) -> rx.Component:
    props.setdefault("color", t.TEXT_BODY)
    props.setdefault("font_size", "15px")
    props.setdefault("line_height", "1.55")
    return rx.text(text, **props)


def primary_button(label, icon: str | None = None, **props) -> rx.Component:
    inner = rx.hstack(
        rx.icon(icon, size=16) if icon else rx.fragment(),
        rx.text(label, font_weight="600", font_size="14px"),
        spacing="2",
        align_items="center",
        justify="center",
    )
    props.setdefault("type", "button")
    props.setdefault("background", t.ACCENT)
    props.setdefault("color", t.ACCENT_TEXT_ON)
    props.setdefault("padding", "11px 20px")
    props.setdefault("border_radius", t.RADIUS_SM)
    props.setdefault("cursor", "pointer")
    props.setdefault("border", "none")
    props.setdefault("font_family", t.FONT_BODY)
    props.setdefault("display", "flex")
    props.setdefault("align_items", "center")
    props.setdefault("justify_content", "center")
    props.setdefault("transition", "background .15s ease")
    props.setdefault("_hover", {"background": t.ACCENT_HOVER})
    return rx.el.button(inner, **props)


def ghost_button(label, icon: str | None = None, **props) -> rx.Component:
    inner = rx.hstack(
        rx.icon(icon, size=16) if icon else rx.fragment(),
        rx.text(label, font_weight="600", font_size="14px"),
        spacing="2",
        align_items="center",
        justify="center",
    )
    props.setdefault("type", "button")
    props.setdefault("background", t.BG_CARD)
    props.setdefault("color", t.TEXT_BODY)
    props.setdefault("padding", "10px 18px")
    props.setdefault("border_radius", t.RADIUS_SM)
    props.setdefault("cursor", "pointer")
    props.setdefault("border", f"1px solid {t.BORDER}")
    props.setdefault("font_family", t.FONT_BODY)
    props.setdefault("display", "flex")
    props.setdefault("align_items", "center")
    props.setdefault("justify_content", "center")
    props.setdefault("transition", "background .15s ease, border-color .15s ease")
    props.setdefault(
        "_hover", {"background": t.BG_SUBTLE, "border_color": t.BORDER_STRONG}
    )
    return rx.el.button(inner, **props)


def text_input(**props) -> rx.Component:
    props.setdefault("background", t.BG_CARD)
    props.setdefault("border", f"1px solid {t.BORDER_STRONG}")
    props.setdefault("border_radius", t.RADIUS_SM)
    props.setdefault("color", t.TEXT)
    props.setdefault("font_family", t.FONT_BODY)
    props.setdefault("font_size", "14px")
    props.setdefault("padding", "11px 14px")
    props.setdefault("width", "100%")
    props.setdefault("_placeholder", {"color": t.TEXT_MUTED})
    props.setdefault("_focus", {"border_color": t.ACCENT, "outline": "none"})
    return rx.input(**props)
