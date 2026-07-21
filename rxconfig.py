import reflex as rx

config = rx.Config(
    app_name="etude",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        # Radix-backed components (rx.input, rx.spinner, rx.markdown) follow
        # this theme rather than our own tokens, so it has to be dark too or
        # they render as light islands on a dark page. Configured here rather
        # than via rx.App(theme=...), which is deprecated since 0.9.0.
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="dark", accent_color="blue", gray_color="slate")
        ),
    ]
)