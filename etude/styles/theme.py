"""Etude Theme"""

# Colors
BACKGROUND = "#000000"          # pure black (right panel bg)
SURFACE = "#0A1424"             # deep navy (left panel base)
CARD = "#000000"                # feature cards are black w/ border, not filled

PRIMARY = "#7C9CC0"             # muted slate-blue accent (buttons, "slides", labels)
PRIMARY_HOVER = "#6C89AC"
PRIMARY_TEXT_ON = "#0A1424"     # dark text used ON TOP of the primary button

TEXT = "#F8FAFC"                # headings / white text
TEXT_SECONDARY = "#94A3B8"      # body paragraph text
TEXT_MUTED = "#5C7691"          # dim mono labels, footer, timestamps

BORDER = "rgba(124,156,192,0.25)"   # hairline slate border used everywhere
BORDER_STRONG = "rgba(124,156,192,0.45)"  # input focus border

SUCCESS = "#22C55E"
ERROR = "#EF4444"

# This design uses sharp corners throughout — no rounding
CARD_RADIUS = "0px"
INPUT_RADIUS = "0px"

SHADOW = "none"

# Fonts
FONT_DISPLAY = "'Space Grotesk', sans-serif"   # bold headlines
FONT_MONO = "'JetBrains Mono', monospace"      # uppercase labels, buttons, meta text

# Google Fonts stylesheet URL — add this in your app = rx.App(stylesheets=[...])
FONT_STYLESHEET = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@500;700&"
    "family=JetBrains+Mono:wght@400;500;700&display=swap"
)
