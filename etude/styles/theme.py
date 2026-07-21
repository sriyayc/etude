"""Etude design system — clean, light, modern edtech.

Single source of truth for colours, type, spacing and reusable primitives.
The brand accent stays in the original steel-blue family; only the surrounding
surfaces moved from a black terminal look to a light, rounded, airy one.
"""

# ----------------------------------------------------------------------
# Colour tokens
# ----------------------------------------------------------------------

# Surfaces
BG_PAGE = "#F5F8FA"        # app background (very light blue-grey)
BG_CARD = "#FFFFFF"        # cards, bars, panels
BG_SUBTLE = "#EEF3F7"      # hover fills, inset areas
BG_SIDEBAR = "#FBFCFD"     # AI sidebar / secondary panels

# Brand accent — unchanged steel-blue hue
ACCENT = "#5D8AA8"         # brand fill / highlights
ACCENT_STRONG = "#3D6885"  # darker accent for text on white (accessible)
ACCENT_HOVER = "#4E7691"
ACCENT_SOFT = "#E9F1F6"    # tinted chip / badge background
ACCENT_TEXT_ON = "#FFFFFF"  # text on a filled accent button

# Text
TEXT = "#1B2A38"           # headings / primary text
TEXT_BODY = "#41535F"      # paragraph text
TEXT_MUTED = "#7B8A98"     # meta, timestamps, dim labels

# Lines
BORDER = "#E3E9EF"         # hairline borders
BORDER_STRONG = "#CBD6DF"  # input / focus borders

# Status
SUCCESS = "#2E9E6B"
SUCCESS_SOFT = "#E7F5EE"
ERROR = "#D9534F"
ERROR_SOFT = "#FBECEC"

# ----------------------------------------------------------------------
# Shape & elevation
# ----------------------------------------------------------------------

RADIUS = "16px"
RADIUS_MD = "12px"
RADIUS_SM = "8px"
RADIUS_PILL = "999px"

SHADOW_SM = "0 1px 2px rgba(16,32,48,0.05)"
SHADOW_CARD = "0 1px 2px rgba(16,32,48,0.04), 0 6px 20px rgba(16,32,48,0.06)"
SHADOW_HOVER = "0 2px 4px rgba(16,32,48,0.06), 0 12px 28px rgba(16,32,48,0.10)"

# ----------------------------------------------------------------------
# Type
# ----------------------------------------------------------------------

FONT_DISPLAY = "'Space Grotesk', sans-serif"   # headings
FONT_BODY = "'Inter', system-ui, sans-serif"   # everything else
FONT_MONO = "'JetBrains Mono', monospace"      # small code / codes only

FONT_STYLESHEET = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@500;600;700&"
    "family=Inter:wght@400;500;600;700&"
    "family=JetBrains+Mono:wght@400;500;600&display=swap"
)

# ----------------------------------------------------------------------
# Backwards-compatible aliases (old names some modules still import)
# ----------------------------------------------------------------------

BACKGROUND = BG_PAGE
SURFACE = BG_CARD
CARD = BG_CARD
PRIMARY = ACCENT
PRIMARY_HOVER = ACCENT_HOVER
PRIMARY_TEXT_ON = ACCENT_TEXT_ON
TEXT_SECONDARY = TEXT_BODY
CARD_RADIUS = RADIUS_MD
INPUT_RADIUS = RADIUS_SM
SHADOW = SHADOW_CARD
