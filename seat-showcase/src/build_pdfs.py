"""
build_pdfs.py - Generate the two themed deliverables:

  1. before_after_transformations.pdf  (cover/transition + BEFORE -> AFTER)
  2. completed_seats_gallery.pdf        (grid gallery of finished seats)

Both share one premium dark + gold theme (see seats.THEME).

Edit BRAND / TRANSFORMATIONS / GALLERY below to customize the copy.
Drop real photos in later by replacing the draw_seat() frames.
"""

from __future__ import annotations
from pdfkit import Document, Page
import seats
from seats import THEME, PALETTES, WORN

# --------------------------------------------------------------------------
# Editable content
# --------------------------------------------------------------------------
BRAND = {
    "name": "ATELIER SEATWORKS",
    "tagline": "Bespoke Seat Restoration & Reupholstery",
    "contact": "hello@atelierseatworks.com   |   +1 (555) 018-2273",
    "site": "atelierseatworks.com",
}

# Each transformation: label, worn "before" note, restored palette + "after" note
TRANSFORMATIONS = [
    {"title": "The Roadster Bucket", "palette": "cognac",
     "before": "Cracked hide, collapsed foam, split seams",
     "after":  "Full-grain cognac leather, rebuilt bolsters, gold contrast stitch"},
    {"title": "The Executive Sport", "palette": "carbon",
     "before": "Sun-faded panels, worn driver bolster",
     "after":  "Carbon-black nappa, reinforced side bolster, tonal stitch"},
    {"title": "The Grand Tourer", "palette": "royal_navy",
     "before": "Torn center panel, brittle vinyl, loose stitching",
     "after":  "Royal-navy leather, diamond channels, hand-finished piping"},
    {"title": "The Heritage Coupe", "palette": "racing_red",
     "before": "Discolored, flattened cushion, frayed edges",
     "after":  "Racing-red aniline, re-cored cushion, ivory double stitch"},
]

# Gallery: (title, palette key)
GALLERY = [
    ("Cognac Classic", "cognac"),
    ("Midnight Carbon", "carbon"),
    ("Monaco Red", "racing_red"),
    ("Regatta Navy", "royal_navy"),
    ("British Emerald", "emerald"),
    ("Alabaster Ivory", "ivory"),
    ("Amethyst Plum", "plum"),
    ("Cognac Diamond", "cognac"),
    ("Carbon Sport", "carbon"),
]


# --------------------------------------------------------------------------
# Shared page furniture
# --------------------------------------------------------------------------
def page_chrome(p: Page, kicker: str, page_no: str = ""):
    seats.draw_background(p)
    m = 34
    seats.frame(p, m, m, p.width - 2 * m, p.height - 2 * m, r=14,
                line_color=THEME["hairline"], lw=1.2)
    seats.frame(p, m + 6, m + 6, p.width - 2 * m - 12, p.height - 2 * m - 12,
                r=10, line_color="#202634", lw=0.6)
    s = 16
    seats.corner_flourish(p, m + 14, p.height - m - 14, s, 1, -1)
    seats.corner_flourish(p, p.width - m - 14, p.height - m - 14, s, -1, -1)
    seats.corner_flourish(p, m + 14, m + 14, s, 1, 1)
    seats.corner_flourish(p, p.width - m - 14, m + 14, s, -1, 1)
    # running header
    p.text_tracked(m + 22, p.height - m - 26, BRAND["name"],
                   font="Times-Bold", size=11, color=THEME["gold"],
                   tracking=2.2)
    p.text_tracked(p.width - m - 22, p.height - m - 26, kicker,
                   font="Helvetica", size=8.5, color=THEME["muted"],
                   tracking=1.8, align="right")
    # footer
    p.text(p.width / 2, m + 16, BRAND["site"], font="Helvetica",
           size=8, color=THEME["muted"], align="center")
    if page_no:
        p.text(p.width - m - 22, m + 16, page_no, font="Helvetica",
               size=8, color=THEME["muted"], align="right")


def badge(p: Page, cx, cy, text, fill, text_color="#0E1017"):
    w = p.text_width(text, "Helvetica-Bold", 9) + 22
    h = 18
    p.round_rect(cx - w / 2, cy - h / 2, w, h, h / 2, fill=fill)
    p.text_tracked(cx, cy - 3, text, font="Helvetica-Bold", size=9,
                   color=text_color, tracking=1.5, align="center")


def image_caption_frame(p, x, y, w, h, tag, tag_color, title):
    """A labelled framed area (the seat is drawn separately inside)."""
    p.linear_gradient_roundrect(x, y, w, h, 12,
                                [(0, THEME["panel_lo"]), (1, THEME["panel"])],
                                angle=90)
    seats.frame(p, x, y, w, h, r=12, line_color=THEME["hairline"], lw=1.1)
    badge(p, x + 46, y + h - 16, tag, tag_color)


# --------------------------------------------------------------------------
# PDF 1 - Before / After transformations
# --------------------------------------------------------------------------
def build_before_after(path):
    doc = Document(title="Seat Transformations - Before & After",
                   author=BRAND["name"], subject="Before and after gallery")

    # ---- Cover / transition page ----
    p = doc.add_page()
    seats.draw_background(p)
    m = 34
    seats.frame(p, m, m, p.width - 2 * m, p.height - 2 * m, r=14,
                line_color=THEME["gold"], lw=1.4)
    s = 20
    seats.corner_flourish(p, m + 16, p.height - m - 16, s, 1, -1)
    seats.corner_flourish(p, p.width - m - 16, p.height - m - 16, s, -1, -1)
    seats.corner_flourish(p, m + 16, m + 16, s, 1, 1)
    seats.corner_flourish(p, p.width - m - 16, m + 16, s, -1, 1)

    cxp = p.width / 2
    H = p.height

    # --- Top masthead ---
    p.text_tracked(cxp, H - 74, BRAND["name"], font="Times-Bold",
                   size=15, color=THEME["gold"], tracking=6, align="center")
    p.text_tracked(cxp, H - 92, BRAND["tagline"].upper(),
                   font="Helvetica", size=8.5, color=THEME["muted"],
                   tracking=3, align="center")

    # --- Title block ---
    p.text(cxp, H - 148, "Before  &  After", font="Times-Bold",
           size=46, color=THEME["ink"], align="center")
    seats.gold_rule(p, cxp - 150, H - 166, cxp + 150, center_dot=True)
    p.text_tracked(cxp, H - 186, "SEAT TRANSFORMATIONS",
                   font="Helvetica-Bold", size=12, color=THEME["gold"],
                   tracking=6, align="center")

    # --- Transition hero: worn seat -> restored seat, gilded arrow between ---
    seat_w, seat_h = 224, 250
    gap = 66
    total = seat_w * 2 + gap
    left_x = cxp - total / 2
    base_y = 104
    seats.draw_seat(p, left_x, base_y, seat_w, seat_h, WORN, worn=True)
    seats.draw_seat(p, left_x + seat_w + gap, base_y, seat_w, seat_h,
                    PALETTES["cognac"], worn=False)
    # arrow / transition mark
    ax = cxp
    ay = base_y + seat_h / 2
    p.save()
    p.set_alpha(0.92)
    p.circle(ax, ay, 26, fill=THEME["gold"])
    p.restore()
    p.set_fill("#0E1017")
    p.moveto(ax - 8, ay + 10)
    p.lineto(ax + 11, ay)
    p.lineto(ax - 8, ay - 10)
    p.close()
    p.fill()
    badge(p, left_x + seat_w / 2, base_y - 4, "BEFORE", THEME["before_tag"])
    badge(p, left_x + seat_w + gap + seat_w / 2, base_y - 4, "AFTER",
          THEME["after_tag"])

    # --- Contact footer ---
    p.text(cxp, 64, BRAND["contact"], font="Helvetica", size=9,
           color=THEME["muted"], align="center")

    # ---- One page per transformation ----
    for i, t in enumerate(TRANSFORMATIONS, start=1):
        p = doc.add_page()
        page_chrome(p, "BEFORE  /  AFTER", f"{i:02d}")
        cxp = p.width / 2

        p.text(cxp, p.height - 96, t["title"], font="Times-Bold",
               size=30, color=THEME["ink"], align="center")
        seats.gold_rule(p, cxp - 120, p.height - 112, cxp + 120)

        # two framed panels
        pad = 70
        pw = (p.width - 2 * pad - 60) / 2
        ph = p.height - 250
        py = 96
        lx = pad
        rx = pad + pw + 60

        image_caption_frame(p, lx, py, pw, ph, "BEFORE",
                             THEME["before_tag"], t["title"])
        image_caption_frame(p, rx, py, pw, ph, "AFTER",
                             THEME["after_tag"], t["title"])

        # seats inside frames
        inset = 26
        sw = pw - 2 * inset
        sh = ph - 70
        seats.draw_seat(p, lx + inset, py + 30, sw, sh, WORN, worn=True)
        seats.draw_seat(p, rx + inset, py + 30, sw, sh,
                        PALETTES[t["palette"]], worn=False)

        # transition arrow between the two frames
        ax = (lx + pw + rx) / 2
        ay = py + ph / 2
        p.circle(ax, ay, 20, fill=THEME["gold"])
        p.set_fill("#0E1017")
        p.moveto(ax - 6, ay + 8); p.lineto(ax + 9, ay)
        p.lineto(ax - 6, ay - 8); p.close(); p.fill()

        # notes under each frame
        p.text(lx + pw / 2, py - 22, t["before"], font="Times-Italic",
               size=10.5, color=THEME["muted"], align="center")
        p.text(rx + pw / 2, py - 22, t["after"], font="Times-Italic",
               size=10.5, color=THEME["gold_hi"], align="center")

    doc.save(path)
    return len(doc.pages)


# --------------------------------------------------------------------------
# PDF 2 - Completed seats gallery
# --------------------------------------------------------------------------
def build_gallery(path):
    doc = Document(title="Completed Seats - Gallery",
                   author=BRAND["name"], subject="Finished seat gallery")

    p = doc.add_page()
    page_chrome(p, "SELECTED WORK", "")
    cxp = p.width / 2
    p.text(cxp, p.height - 92, "Seats We've Done", font="Times-Bold",
           size=30, color=THEME["ink"], align="center")
    seats.gold_rule(p, cxp - 130, p.height - 108, cxp + 130)
    p.text_tracked(cxp, p.height - 128, "A SELECTION OF COMPLETED COMMISSIONS",
                   font="Helvetica", size=8.5, color=THEME["muted"],
                   tracking=3, align="center")

    # grid: 3 columns x 3 rows
    cols, rows = 3, 3
    gx0, gy0 = 60, 70
    gw = p.width - 2 * gx0
    gh = p.height - 230
    cell_gap = 22
    cell_w = (gw - (cols - 1) * cell_gap) / cols
    cell_h = (gh - (rows - 1) * cell_gap) / rows

    for idx, (title, pal_key) in enumerate(GALLERY):
        r = idx // cols
        c = idx % cols
        x = gx0 + c * (cell_w + cell_gap)
        # rows drawn top-to-bottom
        y = gy0 + (rows - 1 - r) * (cell_h + cell_gap)

        # card
        p.linear_gradient_roundrect(
            x, y, cell_w, cell_h, 12,
            [(0, THEME["panel_lo"]), (1, THEME["panel"])], angle=90)
        seats.frame(p, x, y, cell_w, cell_h, r=12,
                    line_color=THEME["hairline"], lw=1.0)

        # seat art
        inset_x = cell_w * 0.14
        seat_w = cell_w - 2 * inset_x
        seat_h = cell_h - 40
        seats.draw_seat(p, x + inset_x, y + 30, seat_w, seat_h,
                        PALETTES[pal_key], worn=False)

        # caption bar
        p.text(x + cell_w / 2, y + 12, title, font="Times-Bold",
               size=11, color=THEME["ink"], align="center")
        # tiny gold ticks
        p.line(x + cell_w / 2 - 26, y + 9, x + cell_w / 2 - 10, y + 9,
               color=THEME["gold"], width=0.6)
        p.line(x + cell_w / 2 + 10, y + 9, x + cell_w / 2 + 26, y + 9,
               color=THEME["gold"], width=0.6)

    p.text(cxp, 70 - 8 + 4, BRAND["tagline"], font="Times-Italic",
           size=10, color=THEME["muted"], align="center")

    doc.save(path)
    return len(doc.pages)


if __name__ == "__main__":
    n1 = build_before_after("before_after_transformations.pdf")
    n2 = build_gallery("completed_seats_gallery.pdf")
    print(f"before_after_transformations.pdf  -> {n1} pages")
    print(f"completed_seats_gallery.pdf       -> {n2} pages")
