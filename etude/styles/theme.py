"""Etude design system — dark, modern edtech.

Single source of truth for colours, type, spacing and reusable primitives.
The brand accent stays in the steel-blue family; surfaces are a blue-tinted
charcoal rather than pure black, which keeps long reading sessions comfortable
and lets elevation read through surface lightness instead of heavy shadow.

Contrast notes (WCAG AA against BG_PAGE):
  TEXT        ~15.9:1
  TEXT_BODY   ~10.2:1
  TEXT_MUTED   ~6.0:1
Text on a filled ACCENT button uses ACCENT_TEXT_ON (near-black, ~6.4:1);
white-on-accent would only reach ~3.7:1 and fail AA at body sizes.
"""

# ----------------------------------------------------------------------
# Colour tokens
# ----------------------------------------------------------------------

# Surfaces — elevation increases with lightness
BG_PAGE = "#0E1418"        # app background (deepest)
BG_CARD = "#161E24"        # cards, bars, panels
BG_SUBTLE = "#1C262E"      # hover fills, inset areas
BG_SIDEBAR = "#121A20"     # AI sidebar / secondary panels

# Brand accent — steel-blue, brightened so it carries on a dark ground
ACCENT = "#6FA3C0"          # brand fill / highlights
ACCENT_STRONG = "#9CC4DC"   # accent *text* on dark surfaces (lighter, not darker)
ACCENT_HOVER = "#83B4CE"    # brightens on hover
ACCENT_SOFT = "#1A2A35"     # tinted chip / badge background
ACCENT_TEXT_ON = "#0B1116"  # text/icons on a filled accent button

# Text
TEXT = "#E8EEF3"           # headings / primary text
TEXT_BODY = "#B4C2CD"      # paragraph text
TEXT_MUTED = "#8494A1"     # meta, timestamps, dim labels

# Lines
BORDER = "#222E37"         # hairline borders
BORDER_STRONG = "#31414D"  # input / focus borders

# Status — brightened for legibility on dark
SUCCESS = "#4ECB8D"
SUCCESS_SOFT = "#13291F"
ERROR = "#F0796F"
ERROR_SOFT = "#2A1618"

# Hero gradient (login split-panel). Kept deliberately deep so the white
# text layered on it stays well above AA.
HERO_GRADIENT = "linear-gradient(150deg, #1E3A4C 0%, #2E5A73 55%, #3D7290 100%)"

# ----------------------------------------------------------------------
# Shape & elevation
# ----------------------------------------------------------------------

RADIUS = "16px"
RADIUS_MD = "12px"
RADIUS_SM = "8px"
RADIUS_PILL = "999px"

# On dark, shadow alone reads poorly — these are deeper, and surfaces also
# lighten with elevation (see BG_* above) to carry the hierarchy.
SHADOW_SM = "0 1px 2px rgba(0,0,0,0.40)"
SHADOW_CARD = "0 1px 2px rgba(0,0,0,0.35), 0 6px 20px rgba(0,0,0,0.45)"
SHADOW_HOVER = "0 2px 4px rgba(0,0,0,0.40), 0 12px 28px rgba(0,0,0,0.55)"

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
