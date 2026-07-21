"""Shared top navigation bar."""

import reflex as rx

from etude.state import UserState
from etude.styles import theme as t


def nav_tab(icon: str, label: str, href: str, active: bool = False):
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, font_size="14px", font_weight="600"),
            spacing="2",
            align_items="center",
        ),
        href=href,
        padding="8px 14px",
        border_radius=t.RADIUS_SM,
        bg=(t.ACCENT_SOFT if active else "transparent"),
        color=(t.ACCENT_STRONG if active else t.TEXT_BODY),
        font_family=t.FONT_BODY,
        text_decoration="none",
        transition="background .15s ease, color .15s ease",
        _hover={"background": t.BG_SUBTLE, "color": t.ACCENT_STRONG},
    )


def topbar(breadcrumb: str, srn: str = "", active: str = ""):

    return rx.hstack(

        # logo.png is the full "etude" wordmark -- don't pair it with a text
        # "etude" or the brand renders twice.
        rx.link(
            rx.image(src="/logo.png", height="30px", width="auto"),
            href="/dashboard",
            text_decoration="none",
            display="flex",
            align_items="center",
        ),

        rx.box(
            rx.icon("chevron-right", size=15, color=t.TEXT_MUTED),
            rx.text(
                breadcrumb,
                color=t.TEXT_BODY,
                font_size="14px",
                font_weight="500",
            ),
            display="flex",
            align_items="center",
            gap="6px",
            margin_left="6px",
        ),

        rx.spacer(),

        rx.hstack(
            nav_tab("layout-grid", "Resources", "/dashboard", active == "resources"),
            nav_tab("trophy", "Leaderboard", "/leaderboard", active == "leaderboard"),
            rx.cond(
                UserState.role == "admin",
                nav_tab("upload", "Upload", "/upload", active == "upload"),
                rx.fragment(),
            ),
            spacing="1",
            align_items="center",
        ),

        rx.menu.root(
            rx.menu.trigger(
                rx.hstack(
                    rx.box(
                        rx.icon("user", size=14, color=t.ACCENT_TEXT_ON),
                        bg=t.ACCENT,
                        border_radius=t.RADIUS_PILL,
                        padding="6px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text(srn, color=t.TEXT, font_size="14px", font_weight="600"),
                    rx.icon("chevron-down", size=15, color=t.TEXT_MUTED),
                    spacing="2",
                    align_items="center",
                    border=f"1px solid {t.BORDER}",
                    border_radius=t.RADIUS_PILL,
                    padding="5px 12px 5px 6px",
                    margin_left="14px",
                    cursor="pointer",
                    transition="border-color .15s ease, background .15s ease",
                    _hover={"border_color": t.BORDER_STRONG, "background": t.BG_SUBTLE},
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    "PESU STUDENT",
                    disabled=True,
                    color=t.TEXT_MUTED,
                    font_family=t.FONT_MONO,
                    font_size="11px",
                    letter_spacing="0.1em",
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(rx.icon("user", size=15), rx.text("Profile"), spacing="2"),
                    on_select=lambda: rx.redirect("/profile"),
                ),
                rx.menu.item(
                    rx.hstack(rx.icon("layout-grid", size=15), rx.text("Resources"), spacing="2"),
                    on_select=lambda: rx.redirect("/dashboard"),
                ),
                rx.menu.item(
                    rx.hstack(rx.icon("trophy", size=15), rx.text("Leaderboard"), spacing="2"),
                    on_select=lambda: rx.redirect("/leaderboard"),
                ),
                rx.cond(
                    UserState.role == "admin",
                    rx.menu.item(
                        rx.hstack(rx.icon("upload", size=15), rx.text("Upload"), spacing="2"),
                        on_select=lambda: rx.redirect("/upload"),
                    ),
                    rx.fragment(),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(rx.icon("log-out", size=15), rx.text("Sign out"), spacing="2"),
                    on_select=UserState.logout,
                    color=t.ERROR,
                ),
                bg=t.BG_CARD,
                border=f"1px solid {t.BORDER}",
                border_radius=t.RADIUS_MD,
                box_shadow=t.SHADOW_CARD,
                color=t.TEXT,
            ),
        ),

        width="100%",
        padding="14px 28px",
        border_bottom=f"1px solid {t.BORDER}",
        bg=t.BG_CARD,
        align_items="center",
        position="sticky",
        top="0",
        z_index="50",
    )
