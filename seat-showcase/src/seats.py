"""
seats.py - Shared visual theme + stylized vector car-seat illustrations.

Everything here draws onto a pdfkit.Page. No image assets are needed:
the seats are rendered as vector art so the PDFs are fully self-contained.
"""

from __future__ import annotations
import math
from pdfkit import Page

# ---------------------------------------------------------------------------
# Shared premium theme
# ---------------------------------------------------------------------------
THEME = {
    "bg_top":    "#0E1017",
    "bg_bottom": "#1C2130",
    "panel":     "#161A26",
    "panel_lo":  "#10131C",
    "gold":      "#C8A24B",
    "gold_hi":   "#EAD08A",
    "ink":       "#F3F1EA",
    "muted":     "#8A90A0",
    "hairline":  "#2C3242",
    "before_tag": "#B4523E",
    "after_tag":  "#5FA37A",
}

# Upholstery palettes used for the "after" / restored seats and the gallery.
# Each: bolster gradient (top/bottom), panel gradient (top/bottom), stitch.
PALETTES = {
    "cognac": {
        "bol_t": "#A6673A", "bol_b": "#6E3F20",
        "pan_t": "#8F5228", "pan_b": "#5E3315",
        "stitch": "#EAD08A", "seam": "#3A2210",
    },
    "carbon": {
        "bol_t": "#3A3F4C", "bol_b": "#191C24",
        "pan_t": "#2A2E39", "pan_b": "#12141B",
        "stitch": "#C8A24B", "seam": "#000000",
    },
    "racing_red": {
        "bol_t": "#C0392B", "bol_b": "#7E1F16",
        "pan_t": "#A5281D", "pan_b": "#651510",
        "stitch": "#F4E4C1", "seam": "#3F0C08",
    },
    "royal_navy": {
        "bol_t": "#2E4A73", "bol_b": "#16273F",
        "pan_t": "#25405F", "pan_b": "#101F30",
        "stitch": "#D9B15A", "seam": "#0A1420",
    },
    "emerald": {
        "bol_t": "#2E7D5B", "bol_b": "#154532",
        "pan_t": "#256A4B", "pan_b": "#103525",
        "stitch": "#EAD08A", "seam": "#0A2118",
    },
    "ivory": {
        "bol_t": "#E9E3D3", "bol_b": "#C9C1AC",
        "pan_t": "#DED7C4", "pan_b": "#B9B199",
        "stitch": "#8A6D34", "seam": "#8F8866",
    },
    "plum": {
        "bol_t": "#6E3A63", "bol_b": "#3E1F39",
        "pan_t": "#5C3053", "pan_b": "#301829",
        "stitch": "#E7C77A", "seam": "#1F0F1B",
    },
}

# A washed-out, tired palette for the "before" seats.
WORN = {
    "bol_t": "#6A665C", "bol_b": "#464339",
    "pan_t": "#5C584E", "pan_b": "#3C392F",
    "stitch": "#7C7666", "seam": "#26241C",
}


# ---------------------------------------------------------------------------
# Backgrounds & decorative helpers
# ---------------------------------------------------------------------------

def draw_background(p: Page):
    """Fill the whole page with the deep vertical theme gradient + vignette."""
    p.linear_gradient_rect(
        0, 0, p.width, p.height,
        [(0, THEME["bg_bottom"]), (0.55, THEME["bg_top"]), (1, "#080A10")],
        angle=90,
    )
    # subtle diagonal sheen
    p.save()
    p.set_alpha(0.05)
    p.linear_gradient_rect(
        0, 0, p.width, p.height,
        [(0, "#000000"), (0.5, "#6E7A8C"), (1, "#000000")],
        angle=35,
    )
    p.restore()


def gold_rule(p: Page, x0, y, x1, center_dot=True):
    """A thin gold horizontal rule with an optional diamond in the middle."""
    p.line(x0, y, x1, y, color=THEME["gold"], width=0.8)
    if center_dot:
        cx = (x0 + x1) / 2
        s = 3.2
        p.set_fill(THEME["gold"])
        p.moveto(cx, y + s); p.lineto(cx + s, y)
        p.lineto(cx, y - s); p.lineto(cx - s, y); p.close(); p.fill()


def corner_flourish(p: Page, x, y, size, flip_x=1, flip_y=1):
    """A small L-shaped gilded corner ornament."""
    p.set_stroke(THEME["gold"])
    p.set_line_width(1.1)
    p.set_line_cap(1)
    p.moveto(x, y + flip_y * size)
    p.lineto(x, y)
    p.lineto(x + flip_x * size, y)
    p.stroke()
    p.moveto(x + flip_x * (size * 0.32), y + flip_y * (size * 0.32))
    p.lineto(x + flip_x * (size * 0.32 + size * 0.5),
             y + flip_y * (size * 0.32))
    p.stroke()
    p.moveto(x + flip_x * (size * 0.32), y + flip_y * (size * 0.32))
    p.lineto(x + flip_x * (size * 0.32),
             y + flip_y * (size * 0.32 + size * 0.5))
    p.stroke()


def frame(p: Page, x, y, w, h, r=10, line_color=None, lw=1.2):
    line_color = line_color or THEME["hairline"]
    p.round_rect(x, y, w, h, r, stroke=line_color, line_width=lw)


# ---------------------------------------------------------------------------
# The seat illustration
# ---------------------------------------------------------------------------

def _panel(p: Page, x, y, w, h, r, top, bottom, stitch, seam,
           channels=3, worn=False):
    """A padded, channel-stitched leather panel."""
    p.linear_gradient_roundrect(x, y, w, h, r,
                                [(0, bottom), (1, top)], angle=90)
    # clip so decorations stay inside the panel
    p.save()
    p.round_rect_path(x, y, w, h, r)
    p.clip()
    # top sheen
    p.set_fill("#FFFFFF")
    p.set_alpha(0.06)
    p.rect_path(x, y + h * 0.62, w, h * 0.38)
    p.fill()
    p.restore()

    # vertical channels + stitching
    if channels >= 2:
        inset = r * 0.7
        usable = w - 2 * inset
        step = usable / channels
        p.save()
        p.round_rect_path(x, y, w, h, r)
        p.clip()
        for i in range(1, channels):
            lx = x + inset + step * i
            # valley shadow
            p.line(lx, y + h * 0.08, lx, y + h * 0.92,
                   color=seam, width=1.6)
            # stitch dashes
            p.set_stroke(stitch)
            p.set_line_width(1.0)
            p.set_dash([2.4, 2.6])
            p.moveto(lx - 1.4, y + h * 0.08)
            p.lineto(lx - 1.4, y + h * 0.92)
            p.stroke()
            p.clear_dash()
        p.restore()

    if worn:
        _wear(p, x, y, w, h, r)


def _wear(p: Page, x, y, w, h, r):
    """Overlay cracks, fading and a small tear to age a panel."""
    p.save()
    p.round_rect_path(x, y, w, h, r)
    p.clip()
    # dull fade
    p.set_fill("#9A9384")
    p.set_alpha(0.12)
    p.rect_path(x, y, w, h)
    p.fill()
    # dark grime pooling at the bottom
    p.set_fill("#000000")
    p.set_alpha(0.18)
    p.rect_path(x, y, w, h * 0.22)
    p.fill()
    p.set_alpha(1)
    # hairline cracks
    p.set_stroke("#26241C")
    p.set_line_width(0.8)
    rnd = _lcg(int(x * 13 + y * 7 + w))
    for _ in range(6):
        cxp = x + rnd() * w
        cyp = y + h * (0.25 + rnd() * 0.6)
        px, py = cxp, cyp
        p.moveto(px, py)
        for _ in range(3):
            px += (rnd() - 0.5) * w * 0.18
            py += (rnd() - 0.5) * h * 0.16
            p.lineto(px, py)
        p.stroke()
    # a small tear (exposed foam)
    tx = x + w * (0.3 + rnd() * 0.4)
    ty = y + h * (0.35 + rnd() * 0.3)
    p.set_fill("#D8CDB4")
    p.moveto(tx, ty)
    p.lineto(tx + w * 0.05, ty + h * 0.07)
    p.lineto(tx + w * 0.11, ty + h * 0.01)
    p.lineto(tx + w * 0.06, ty - h * 0.05)
    p.close()
    p.fill()
    p.restore()


def _lcg(seed):
    """Deterministic pseudo-random generator so output is reproducible."""
    state = {"s": (seed * 2654435761) & 0xFFFFFFFF}

    def rnd():
        state["s"] = (1103515245 * state["s"] + 12345) & 0x7FFFFFFF
        return state["s"] / 0x7FFFFFFF
    return rnd


def draw_seat(p: Page, x, y, w, h, pal, worn=False):
    """Draw a stylized front-view bucket/sport seat inside box (x,y,w,h)."""
    cx = x + w / 2
    bol_t, bol_b = pal["bol_t"], pal["bol_b"]
    pan_t, pan_b = pal["pan_t"], pal["pan_b"]
    stitch, seam = pal["stitch"], pal["seam"]

    # soft drop shadow under the whole seat
    p.save()
    p.set_alpha(0.35)
    p.set_fill("#000000")
    p.round_rect_path(x + w * 0.12, y + h * 0.01, w * 0.76, h * 0.18,
                      h * 0.06)
    p.fill()
    p.restore()

    # ---- Headrest ----
    hr_w, hr_h = w * 0.28, h * 0.15
    hr_x, hr_y = cx - hr_w / 2, y + h - hr_h
    # posts
    p.set_stroke(seam)
    p.set_line_width(max(2.0, w * 0.012))
    p.set_line_cap(1)
    p.line(cx - hr_w * 0.22, hr_y - h * 0.03, cx - hr_w * 0.22, hr_y + hr_h * 0.35)
    p.line(cx + hr_w * 0.22, hr_y - h * 0.03, cx + hr_w * 0.22, hr_y + hr_h * 0.35)
    _panel(p, hr_x, hr_y, hr_w, hr_h, hr_w * 0.32,
           bol_t, bol_b, stitch, seam, channels=2, worn=worn)

    # ---- Backrest ----
    br_w, br_h = w * 0.70, h * 0.44
    br_x = cx - br_w / 2
    br_y = hr_y - h * 0.03 - br_h
    bol_w = br_w * 0.20
    # side bolsters (raised)
    _panel(p, br_x, br_y, bol_w, br_h, bol_w * 0.45,
           bol_t, bol_b, stitch, seam, channels=0, worn=worn)
    _panel(p, br_x + br_w - bol_w, br_y, bol_w, br_h, bol_w * 0.45,
           bol_t, bol_b, stitch, seam, channels=0, worn=worn)
    # center panel (inset, channel-stitched)
    cp_x = br_x + bol_w * 0.92
    cp_w = br_w - 2 * bol_w * 0.92
    _panel(p, cp_x, br_y + br_h * 0.04, cp_w, br_h * 0.92, cp_w * 0.10,
           pan_t, pan_b, stitch, seam, channels=4, worn=worn)

    # ---- Seat base ----
    sb_w, sb_h = w * 0.80, h * 0.24
    sb_x = cx - sb_w / 2
    sb_y = y + h * 0.03
    sbol_w = sb_w * 0.18
    _panel(p, sb_x, sb_y, sbol_w, sb_h, sbol_w * 0.5,
           bol_t, bol_b, stitch, seam, channels=0, worn=worn)
    _panel(p, sb_x + sb_w - sbol_w, sb_y, sbol_w, sb_h, sbol_w * 0.5,
           bol_t, bol_b, stitch, seam, channels=0, worn=worn)
    cb_x = sb_x + sbol_w * 0.92
    cb_w = sb_w - 2 * sbol_w * 0.92
    _panel(p, cb_x, sb_y + sb_h * 0.05, cb_w, sb_h * 0.9, cb_w * 0.06,
           pan_t, pan_b, stitch, seam, channels=4, worn=worn)
