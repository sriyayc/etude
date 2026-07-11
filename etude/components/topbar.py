"""Shared top navigation bar."""

import reflex as rx

from etude.state import UserState

ACCENT = "#5D8AA8"
ACCENT_LIGHT = "#7393B3"
BORDER = "#1F3A3D"
BACKGROUND = "#000000"


def nav_tab(icon: str, label: str, href: str, active: bool = False):
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=15),
            rx.text(
                label,
                font_family="monospace",
                font_size="12px",
                letter_spacing="0.15em",
                text_transform="uppercase",
            ),
            spacing="2",
            align_items="center",
        ),
        href=href,
        padding="10px 16px",
        bg="rgba(93,138,168,0.15)" if active else "transparent",
        border=f"1px solid {ACCENT if active else 'transparent'}",
        color="white" if active else ACCENT_LIGHT,
        _hover={"color": "white"},
    )


def topbar(breadcrumb: str, srn: str = "", active: str = ""):

    return rx.hstack(

        rx.hstack(
            rx.image(src="/logo.png", height="28px", width="auto"),
            rx.text("/PESU", color=ACCENT, font_family="monospace",
                    font_size="12px", letter_spacing="0.1em"),
            rx.icon("chevron-right", size=14, color=ACCENT_LIGHT),
            rx.text(breadcrumb, color="white", font_family="monospace", font_size="13px"),
            spacing="3",
            align_items="center",
        ),

        rx.spacer(),

        rx.hstack(
            nav_tab("bar-chart-2", "Resources", "/dashboard", active == "resources"),
            nav_tab("trophy", "Leaderboard", "/leaderboard", active == "leaderboard"),
            spacing="2",
            align_items="center",
        ),

        rx.menu.root(
            rx.menu.trigger(
                rx.hstack(
                    rx.box(
                        rx.icon("user", size=12),
                        bg=ACCENT,
                        color="black",
                        padding="4px 6px",
                        display="flex",
                        align_items="center",
                    ),
                    rx.text(srn, color="white", font_family="monospace", font_size="13px"),
                    spacing="2",
                    align_items="center",
                    border=f"1px solid {BORDER}",
                    padding="8px 14px",
                    margin_left="20px",
                    cursor="pointer",
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    "PESU STUDENT",
                    disabled=True,
                    color=ACCENT_LIGHT,
                    font_family="monospace",
                    font_size="11px",
                    letter_spacing="0.1em",
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(rx.icon("user", size=14), rx.text("Profile"), spacing="2"),
                    on_select=lambda: rx.redirect("/profile"),
                ),
                rx.menu.item(
                    rx.hstack(rx.icon("bar-chart-2", size=14), rx.text("Resources"), spacing="2"),
                    on_select=lambda: rx.redirect("/dashboard"),
                ),
                rx.menu.item(
                    rx.hstack(rx.icon("trophy", size=14), rx.text("Leaderboard"), spacing="2"),
                    on_select=lambda: rx.redirect("/leaderboard"),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(rx.icon("log-out", size=14), rx.text("Sign out"), spacing="2"),
                    on_select=UserState.logout,
                ),
                bg="#0A2647",
                border=f"1px solid {BORDER}",
                color="white",
            ),
        ),

        width="100%",
        padding="18px 32px",
        border_bottom=f"1px solid {BORDER}",
        bg=BACKGROUND,
        align_items="center",
    )
