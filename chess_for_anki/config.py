"""
Configuration for Chess for Anki.

Stores user preferences (move sound, board color, and - later - piece set and
board texture) via Anki's add-on config. Also derives the two board-square
colors from a single base color, so the user picks one color on a wheel and
the light/dark squares are generated as two shades of it.
"""

import base64
import os

NARRATION_SPEEDS = (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)


def narration_rate(value):
    return float(value) if type(value) in (int, float) and value in NARRATION_SPEEDS else 1.5

DEFAULTS = {
    "sound_enabled": True,
    "confetti_enabled": True,
    "explanation_pack": "starter-en",
    "notation_language": "auto",
    "narration_rate": 1.5,
    "voice_pack": "system",
    "voice_language": "en-US",
    "feedback_url": "https://github.com/fernandomec/chess-for-anki-community",
    "board_color": "#799459",   # base color = the DARK square
    "board_light": "#eeeccd",          # LIGHT square; "" = derive it from board_color
    "piece_set": "wooden",    # reserved for a later update
    "board_texture": "solid",   # reserved for a later update
    "mistakes_limit": 3,        # wrong moves allowed per card before it flips (1-5)
    # "Sticky fields": which Add-dialog fields keep their value for the next
    # card instead of clearing. Deck and Tags default ON (their old behavior);
    # the rest default OFF so nothing changes for existing users until they
    # pin a field.
    "sticky_deck": True,
    "sticky_title": False,
    "sticky_color": False,
    "sticky_startpos": False,
    "sticky_book": False,
    "sticky_personal": False,
    "sticky_tags": True,
    # Last-committed values of pinned fields (saved on Add, restored on open).
    # Only fields whose pin is on are meaningfully restored.
    "sticky_val_deck": "",
    "sticky_val_title": "",
    "sticky_val_color": "white",
    "sticky_val_startpos_fen": "",   # "" = opening; non-empty = that custom FEN
    "sticky_val_book": "",
    "sticky_val_personal": "",
    "sticky_val_tags": "",
    "toggle_one_key": "n",      # review hotkey: reveal notes one at a time
    "toggle_all_key": ",",      # review hotkey: open/close all notes at once
}

# A few one-click presets (base = dark-square color).
PRESETS = [
    ("Brown",  "#b58863"),
    ("Green",  "#769656"),
    ("Blue",   "#6f8faf"),
    ("Gray",   "#8a8a8a"),
    ("Purple", "#9c7bb5"),
]

# Piece styles (label, id). All render in both the web boards and the Qt editor.
PIECE_SETS = [
    ("Classic", "cburnett"),
    ("Letters", "letters"),
    ("Wooden", "wooden"),
    ("Blank", "blank"),
    ("Blindfolded", "blindfold"),
]

# Board textures (label, id). Applied to the study card and Manual Entry board.
TEXTURES = [
    ("Solid",   "solid"),
    ("Wood",    "wood"),
    ("Linen",   "linen"),
    ("Soft 3D", "soft"),
]


def texture_pattern(name):
    """Return a CSS background-image value for a texture (semi-transparent so it
    layers over any square color), or '' for a flat/solid board."""
    if name == "wood":
        return ("repeating-linear-gradient(90deg,"
                "rgba(0,0,0,0.07) 0px,rgba(0,0,0,0.07) 2px,"
                "rgba(255,255,255,0.05) 2px,rgba(255,255,255,0.05) 5px)")
    if name == "linen":
        return ("repeating-linear-gradient(0deg,rgba(0,0,0,0.05) 0 1px,"
                "transparent 1px 4px),"
                "repeating-linear-gradient(90deg,rgba(0,0,0,0.05) 0 1px,"
                "transparent 1px 4px)")
    if name == "soft":
        return ("radial-gradient(circle at 32% 28%,rgba(255,255,255,0.16),"
                "rgba(0,0,0,0.10) 78%)")
    return ""  # solid


def letters_svg(code):
    """Python mirror of the JS letters piece set (for the Qt position editor).
    `code` like 'wK'. Returns full <svg> markup."""
    color, ptype = code[0], code[1]
    is_white = color == "w"
    disc = "#f2f2f2" if is_white else "#2c2c2c"
    ink = "#2c2c2c" if is_white else "#f2f2f2"
    ring = "#8a8a8a" if is_white else "#111111"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" '
        'width="45" height="45">'
        f'<circle cx="22.5" cy="22.5" r="16.5" fill="{disc}" '
        f'stroke="{ring}" stroke-width="1.5"/>'
        f'<text x="22.5" y="29.5" text-anchor="middle" '
        f'font-family="Georgia, \'Times New Roman\', serif" font-size="21" '
        f'font-weight="bold" fill="{ink}">{ptype}</text></svg>'
    )


def blank_svg(code):
    """The Letters discs without the letters: plain coloured circles. The
    player tells the pieces apart by memory alone - a step below Letters,
    a step above Blindfolded."""
    is_white = code[0] == "w"
    disc = "#f2f2f2" if is_white else "#2c2c2c"
    ring = "#8a8a8a" if is_white else "#111111"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" '
        'width="45" height="45">'
        f'<circle cx="22.5" cy="22.5" r="16.5" fill="{disc}" '
        f'stroke="{ring}" stroke-width="1.5"/></svg>'
    )


# Wood palette for the "wooden" piece set (recolours the Classic silhouettes).
WOOD_WHITE_BODY = "#eaca94"
WOOD_WHITE_LINE = "#6e4a26"
WOOD_BLACK_BODY = "#5c3b22"
WOOD_BLACK_LINE = "#241509"
WOOD_BLACK_DETAIL = "#caa274"


def wooden_recolor(inner, is_white):
    """Recolour the Classic (cburnett) inner SVG markup into wood tones so the
    pieces keep their proper Staunton shapes but read as wooden. `inner` is the
    inner markup for one piece; `is_white` selects the light/dark wood."""
    if is_white:
        return (inner.replace('fill="#fff"', f'fill="{WOOD_WHITE_BODY}"')
                     .replace('stroke="#fff"', f'stroke="{WOOD_WHITE_BODY}"')
                     .replace('fill="#000"', f'fill="{WOOD_WHITE_LINE}"')
                     .replace('stroke="#000"', f'stroke="{WOOD_WHITE_LINE}"'))
    return (inner.replace('fill="#fff"', f'fill="{WOOD_BLACK_DETAIL}"')
                 .replace('stroke="#fff"', f'stroke="{WOOD_BLACK_DETAIL}"')
                 .replace('fill="#000"', f'fill="{WOOD_BLACK_BODY}"')
                 .replace('stroke="#000"', f'stroke="{WOOD_BLACK_LINE}"'))


def shade(hex_color, delta):
    """Lighten (delta>0) or darken (delta<0) a hex color by adjusting HSL
    lightness. Used to build subtle board textures in the Qt surfaces."""
    try:
        h, s, l = _rgb_to_hsl(*_hex_to_rgb(hex_color))
    except Exception:
        return hex_color
    l = max(0.0, min(1.0, l + delta))
    return _hsl_to_hex(h, s, l)


def qt_square_bg(base_hex, texture):
    """Return a Qt stylesheet `background` value for a square of `base_hex`
    under the given texture. Approximates the web CSS textures using Qt
    gradients (exact CSS repeats aren't available in Qt stylesheets)."""
    if texture == "soft":
        hi = shade(base_hex, 0.11)
        lo = shade(base_hex, -0.09)
        return (f"qradialgradient(cx:0.34, cy:0.30, radius:0.95, "
                f"fx:0.34, fy:0.30, stop:0 {hi}, stop:1 {lo})")
    if texture == "wood":
        d = shade(base_hex, -0.05)
        return (f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {base_hex}, stop:0.25 {d}, stop:0.5 {base_hex}, "
                f"stop:0.75 {d}, stop:1 {base_hex})")
    if texture == "linen":
        hi = shade(base_hex, 0.035)
        lo = shade(base_hex, -0.035)
        return (f"qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                f"stop:0 {hi}, stop:0.5 {base_hex}, stop:1 {lo})")
    return base_hex  # solid


# ── config storage ──
def get_config():
    from aqt import mw
    cfg = mw.addonManager.getConfig(__name__) or {}
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in cfg.items() if v is not None})
    return merged


def save_config(cfg):
    from aqt import mw
    mw.addonManager.writeConfig(__name__, cfg)


# ── color helpers ──
def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6.0, s, l


def _hue_to_rgb(p, q, t):
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p


def _hsl_to_hex(h, s, l):
    if s == 0:
        v = l * 255
        return _rgb_to_hex((v, v, v))
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = _hue_to_rgb(p, q, h + 1 / 3)
    g = _hue_to_rgb(p, q, h)
    b = _hue_to_rgb(p, q, h - 1 / 3)
    return _rgb_to_hex((r * 255, g * 255, b * 255))


def board_squares(base_hex):
    """Return (light_hex, dark_hex) from the user-chosen DARK square color.

    The chosen color is used as the dark square (as faithfully as possible). The
    light square is derived as a clearly lighter, gently desaturated shade of the
    same hue, so the two squares read as two shades of one color. Only the very
    top of the lightness range is guarded so a light pick still leaves enough
    contrast for the light square."""
    try:
        h, s, l = _rgb_to_hsl(*_hex_to_rgb(base_hex))
    except Exception:
        h, s, l = _rgb_to_hsl(*_hex_to_rgb(DEFAULTS["board_color"]))
    dark_l = min(l, 0.66)                       # use the chosen color as-is
    light_l = min(0.92, dark_l + 0.30)          # clearly lighter light square
    dark = _hsl_to_hex(h, s, dark_l)
    light = _hsl_to_hex(h, s * 0.82, light_l)
    return light, dark


def board_colors(c):
    """Return (light_hex, dark_hex) for a config dict.

    The dark square is ``board_color``. The light square is ``board_light`` if
    the user has chosen one; otherwise it is derived from the dark color
    exactly as before this setting existed - so configs from older versions
    (no ``board_light`` key) keep their board pixel-identical."""
    base = c.get("board_color", DEFAULTS["board_color"])
    light, dark = board_squares(base)
    custom = (c.get("board_light") or "").strip()
    if __import__("re").fullmatch(r"#[0-9A-Fa-f]{6}", custom):
        light = custom
    return light, dark


# ── move / capture / check sounds (base64-embedded so cards need no media files) ──
def _sound_b64(filename):
    path = os.path.join(os.path.dirname(__file__), "web", filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""


def move_sound_b64():
    return _sound_b64("move.mp3")


def capture_sound_b64():
    return _sound_b64("capture.mp3")


def check_sound_b64():
    return _sound_b64("check.mp3")


def castle_sound_b64():
    return _sound_b64("castle.mp3")


def mate_sound_b64():
    return _sound_b64("mate.mp3")


def mistake_sound_uri():
    """The attempt-mode wrong-move sound (Mistakes Limit rejections), as a
    data: URI or '' if the file is missing. Separate from sound_data_uris()
    because it is event-driven (not tied to a move's notation) and only the
    study card uses it."""
    b = _sound_b64("mistake.mp3")
    return ("data:audio/mpeg;base64," + b) if b else ""


def sound_data_uris():
    """Return (move_uri, capture_uri, check_uri, castle_uri, mate_uri) as
    data: URIs; any that are missing come back as '' (players then fall back
    toward the plain move sound, so an absent file can never silence
    anything)."""
    m = move_sound_b64()
    c = capture_sound_b64()
    k = check_sound_b64()
    o = castle_sound_b64()
    g = mate_sound_b64()
    mu = ("data:audio/mpeg;base64," + m) if m else ""
    cu = ("data:audio/mpeg;base64," + c) if c else ""
    ku = ("data:audio/mpeg;base64," + k) if k else ""
    ou = ("data:audio/mpeg;base64," + o) if o else ""
    gu = ("data:audio/mpeg;base64," + g) if g else ""
    return mu, cu, ku, ou, gu
