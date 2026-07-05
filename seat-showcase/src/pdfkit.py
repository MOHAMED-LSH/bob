"""
pdfkit.py - A tiny, zero-dependency PDF engine.

Supports: multiple pages, RGB fills/strokes, arbitrary paths, rounded
rectangles, linear (axial) gradients with multiple color stops, constant
alpha (transparency) via ExtGState, coordinate transforms, and text using
the PDF core fonts with accurate width tables for proper alignment.

No third-party libraries are required. Pure standard-library Python 3.
"""

from __future__ import annotations

import math
import zlib
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# Core-font width tables (units per 1000 em) for character codes 32..126.
# Only the fonts we actually use are included.
# ---------------------------------------------------------------------------

_HELV = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667,
    "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 278, ';': 278,
    '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, 'A': 667, 'B': 667,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469,
    '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556,
    'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222,
    'm': 833, 'n': 556, 'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500,
    't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 500,
    '{': 334, '|': 260, '}': 334, '~': 584,
}

_HELVB = {
    ' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722,
    "'": 238, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 333, ';': 333,
    '<': 584, '=': 584, '>': 584, '?': 611, '@': 975, 'A': 722, 'B': 722,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 333, '\\': 278, ']': 333, '^': 584,
    '_': 556, '`': 333, 'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556,
    'f': 333, 'g': 611, 'h': 611, 'i': 278, 'j': 278, 'k': 556, 'l': 278,
    'm': 889, 'n': 611, 'o': 611, 'p': 611, 'q': 611, 'r': 389, 's': 556,
    't': 333, 'u': 611, 'v': 556, 'w': 778, 'x': 556, 'y': 556, 'z': 500,
    '{': 389, '|': 280, '}': 389, '~': 584,
}

_TIMES = {
    ' ': 250, '!': 333, '"': 408, '#': 500, '$': 500, '%': 833, '&': 778,
    "'": 180, '(': 333, ')': 333, '*': 500, '+': 564, ',': 250, '-': 333,
    '.': 250, '/': 278, '0': 500, '1': 500, '2': 500, '3': 500, '4': 500,
    '5': 500, '6': 500, '7': 500, '8': 500, '9': 500, ':': 278, ';': 278,
    '<': 564, '=': 564, '>': 564, '?': 444, '@': 921, 'A': 722, 'B': 667,
    'C': 667, 'D': 722, 'E': 611, 'F': 556, 'G': 722, 'H': 722, 'I': 333,
    'J': 389, 'K': 722, 'L': 611, 'M': 889, 'N': 722, 'O': 722, 'P': 556,
    'Q': 722, 'R': 667, 'S': 556, 'T': 611, 'U': 722, 'V': 722, 'W': 944,
    'X': 722, 'Y': 722, 'Z': 611, '[': 333, '\\': 278, ']': 333, '^': 469,
    '_': 500, '`': 333, 'a': 444, 'b': 500, 'c': 444, 'd': 500, 'e': 444,
    'f': 333, 'g': 500, 'h': 500, 'i': 278, 'j': 278, 'k': 500, 'l': 278,
    'm': 778, 'n': 500, 'o': 500, 'p': 500, 'q': 500, 'r': 333, 's': 389,
    't': 278, 'u': 500, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 444,
    '{': 480, '|': 200, '}': 480, '~': 541,
}

_TIMESB = {
    ' ': 250, '!': 333, '"': 555, '#': 500, '$': 500, '%': 1000, '&': 833,
    "'": 278, '(': 333, ')': 333, '*': 500, '+': 570, ',': 250, '-': 333,
    '.': 250, '/': 278, '0': 500, '1': 500, '2': 500, '3': 500, '4': 500,
    '5': 500, '6': 500, '7': 500, '8': 500, '9': 500, ':': 333, ';': 333,
    '<': 570, '=': 570, '>': 570, '?': 500, '@': 930, 'A': 722, 'B': 667,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 778, 'I': 389,
    'J': 500, 'K': 778, 'L': 667, 'M': 944, 'N': 722, 'O': 778, 'P': 611,
    'Q': 778, 'R': 722, 'S': 556, 'T': 667, 'U': 722, 'V': 722, 'W': 1000,
    'X': 722, 'Y': 722, 'Z': 667, '[': 333, '\\': 278, ']': 333, '^': 581,
    '_': 500, '`': 333, 'a': 500, 'b': 556, 'c': 444, 'd': 556, 'e': 444,
    'f': 333, 'g': 500, 'h': 556, 'i': 278, 'j': 333, 'k': 556, 'l': 278,
    'm': 833, 'n': 556, 'o': 500, 'p': 556, 'q': 556, 'r': 444, 's': 389,
    't': 333, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 444,
    '{': 394, '|': 220, '}': 394, '~': 520,
}

_TIMESI = {
    ' ': 250, '!': 333, '"': 420, '#': 500, '$': 500, '%': 833, '&': 778,
    "'": 214, '(': 333, ')': 333, '*': 500, '+': 675, ',': 250, '-': 333,
    '.': 250, '/': 278, '0': 500, '1': 500, '2': 500, '3': 500, '4': 500,
    '5': 500, '6': 500, '7': 500, '8': 500, '9': 500, ':': 333, ';': 333,
    '<': 675, '=': 675, '>': 675, '?': 500, '@': 920, 'A': 611, 'B': 611,
    'C': 667, 'D': 722, 'E': 611, 'F': 611, 'G': 722, 'H': 722, 'I': 333,
    'J': 444, 'K': 667, 'L': 556, 'M': 833, 'N': 667, 'O': 722, 'P': 611,
    'Q': 722, 'R': 611, 'S': 500, 'T': 556, 'U': 722, 'V': 611, 'W': 833,
    'X': 611, 'Y': 556, 'Z': 556, '[': 389, '\\': 278, ']': 389, '^': 422,
    '_': 500, '`': 333, 'a': 500, 'b': 500, 'c': 444, 'd': 500, 'e': 444,
    'f': 278, 'g': 500, 'h': 500, 'i': 278, 'j': 278, 'k': 444, 'l': 278,
    'm': 722, 'n': 500, 'o': 500, 'p': 500, 'q': 500, 'r': 389, 's': 389,
    't': 278, 'u': 500, 'v': 444, 'w': 667, 'x': 444, 'y': 444, 'z': 389,
    '{': 400, '|': 275, '}': 400, '~': 541,
}

# font key -> (PostScript base font name, width table)
FONTS = {
    'Helvetica': ('Helvetica', _HELV),
    'Helvetica-Bold': ('Helvetica-Bold', _HELVB),
    'Times': ('Times-Roman', _TIMES),
    'Times-Bold': ('Times-Bold', _TIMESB),
    'Times-Italic': ('Times-Italic', _TIMESI),
}


def hex_to_rgb(h: str) -> Tuple[float, float, float]:
    """Convert '#RRGGBB' (or 'RRGGBB') to a 0..1 RGB tuple."""
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255.0,
            int(h[2:4], 16) / 255.0,
            int(h[4:6], 16) / 255.0)


def _fmt(n: float) -> str:
    """Format a number for PDF output, trimming trailing zeros."""
    s = f"{n:.4f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


def _esc(text: str) -> str:
    return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


class Page:
    """A single page with a content stream and its own resource sets."""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        self.ops: List[str] = []
        self.shadings: List[str] = []   # inline shading dictionaries
        self.gstates: List[str] = []    # inline ExtGState dictionaries
        self.fonts_used: set = set()

    # -- raw ---------------------------------------------------------------
    def raw(self, s: str):
        self.ops.append(s)

    # -- state -------------------------------------------------------------
    def save(self):
        self.ops.append('q')

    def restore(self):
        self.ops.append('Q')

    def translate(self, x: float, y: float):
        self.ops.append(f"1 0 0 1 {_fmt(x)} {_fmt(y)} cm")

    def scale(self, sx: float, sy: float):
        self.ops.append(f"{_fmt(sx)} 0 0 {_fmt(sy)} 0 0 cm")

    def rotate(self, deg: float):
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        self.ops.append(f"{_fmt(c)} {_fmt(s)} {_fmt(-s)} {_fmt(c)} 0 0 cm")

    def set_line_width(self, w: float):
        self.ops.append(f"{_fmt(w)} w")

    def set_line_cap(self, cap: int):
        self.ops.append(f"{cap} J")

    def set_line_join(self, j: int):
        self.ops.append(f"{j} j")

    def set_dash(self, pattern: List[float], phase: float = 0):
        arr = ' '.join(_fmt(p) for p in pattern)
        self.ops.append(f"[{arr}] {_fmt(phase)} d")

    def clear_dash(self):
        self.ops.append("[] 0 d")

    def set_fill(self, color):
        r, g, b = _color(color)
        self.ops.append(f"{_fmt(r)} {_fmt(g)} {_fmt(b)} rg")

    def set_stroke(self, color):
        r, g, b = _color(color)
        self.ops.append(f"{_fmt(r)} {_fmt(g)} {_fmt(b)} RG")

    def set_alpha(self, ca: float, is_stroke: bool = False):
        key = 'CA' if is_stroke else 'ca'
        idx = len(self.gstates) + 1
        self.gstates.append(f"/GS{idx} << /{key} {_fmt(ca)} >>")
        self.ops.append(f"/GS{idx} gs")

    # -- paths -------------------------------------------------------------
    def moveto(self, x, y):
        self.ops.append(f"{_fmt(x)} {_fmt(y)} m")

    def lineto(self, x, y):
        self.ops.append(f"{_fmt(x)} {_fmt(y)} l")

    def curveto(self, x1, y1, x2, y2, x3, y3):
        self.ops.append(f"{_fmt(x1)} {_fmt(y1)} {_fmt(x2)} {_fmt(y2)} "
                        f"{_fmt(x3)} {_fmt(y3)} c")

    def close(self):
        self.ops.append('h')

    def fill(self):
        self.ops.append('f')

    def stroke(self):
        self.ops.append('S')

    def fill_stroke(self):
        self.ops.append('B')

    def clip(self):
        self.ops.append('W n')

    # -- shapes ------------------------------------------------------------
    def rect_path(self, x, y, w, h):
        self.ops.append(f"{_fmt(x)} {_fmt(y)} {_fmt(w)} {_fmt(h)} re")

    def rect(self, x, y, w, h, fill=None, stroke=None, line_width=None):
        if line_width is not None:
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill(fill)
        if stroke is not None:
            self.set_stroke(stroke)
        self.rect_path(x, y, w, h)
        if fill is not None and stroke is not None:
            self.fill_stroke()
        elif fill is not None:
            self.fill()
        elif stroke is not None:
            self.stroke()

    def round_rect_path(self, x, y, w, h, r):
        r = min(r, w / 2, h / 2)
        k = 0.5522847498 * r
        self.moveto(x + r, y)
        self.lineto(x + w - r, y)
        self.curveto(x + w - r + k, y, x + w, y + r - k, x + w, y + r)
        self.lineto(x + w, y + h - r)
        self.curveto(x + w, y + h - r + k, x + w - r + k, y + h, x + w - r, y + h)
        self.lineto(x + r, y + h)
        self.curveto(x + r - k, y + h, x, y + h - r + k, x, y + h - r)
        self.lineto(x, y + r)
        self.curveto(x, y + r - k, x + r - k, y, x + r, y)
        self.close()

    def round_rect(self, x, y, w, h, r, fill=None, stroke=None, line_width=None):
        if line_width is not None:
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill(fill)
        if stroke is not None:
            self.set_stroke(stroke)
        self.round_rect_path(x, y, w, h, r)
        if fill is not None and stroke is not None:
            self.fill_stroke()
        elif fill is not None:
            self.fill()
        elif stroke is not None:
            self.stroke()

    def circle(self, cx, cy, r, fill=None, stroke=None, line_width=None):
        k = 0.5522847498 * r
        if line_width is not None:
            self.set_line_width(line_width)
        if fill is not None:
            self.set_fill(fill)
        if stroke is not None:
            self.set_stroke(stroke)
        self.moveto(cx + r, cy)
        self.curveto(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
        self.curveto(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
        self.curveto(cx - r, cy - k, cx - k, cy - r, cx, cy - r)
        self.curveto(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
        self.close()
        if fill is not None and stroke is not None:
            self.fill_stroke()
        elif fill is not None:
            self.fill()
        elif stroke is not None:
            self.stroke()

    def line(self, x0, y0, x1, y1, color=None, width=None, cap=1):
        if width is not None:
            self.set_line_width(width)
        if color is not None:
            self.set_stroke(color)
        self.set_line_cap(cap)
        self.moveto(x0, y0)
        self.lineto(x1, y1)
        self.stroke()

    # -- gradients ---------------------------------------------------------
    def _build_function(self, stops):
        """stops: list of (t, color). Returns an inline PDF function dict."""
        colors = [_color(c) for _, c in stops]
        if len(stops) == 2:
            c0 = ' '.join(_fmt(v) for v in colors[0])
            c1 = ' '.join(_fmt(v) for v in colors[1])
            return (f"<< /FunctionType 2 /Domain [0 1] "
                    f"/C0 [{c0}] /C1 [{c1}] /N 1 >>")
        subs = []
        for i in range(len(stops) - 1):
            c0 = ' '.join(_fmt(v) for v in colors[i])
            c1 = ' '.join(_fmt(v) for v in colors[i + 1])
            subs.append(f"<< /FunctionType 2 /Domain [0 1] "
                        f"/C0 [{c0}] /C1 [{c1}] /N 1 >>")
        bounds = ' '.join(_fmt(stops[i][0]) for i in range(1, len(stops) - 1))
        encode = ' '.join('0 1' for _ in subs)
        return (f"<< /FunctionType 3 /Domain [0 1] "
                f"/Functions [{' '.join(subs)}] /Bounds [{bounds}] "
                f"/Encode [{encode}] >>")

    def _register_shading(self, x0, y0, x1, y1, stops):
        fn = self._build_function(stops)
        sh = (f"<< /ShadingType 2 /ColorSpace /DeviceRGB "
              f"/Coords [{_fmt(x0)} {_fmt(y0)} {_fmt(x1)} {_fmt(y1)}] "
              f"/Function {fn} /Extend [true true] >>")
        self.shadings.append(sh)
        return f"Sh{len(self.shadings)}"

    def linear_gradient_rect(self, x, y, w, h, stops, angle=90):
        """Fill a rectangle with a linear gradient.

        angle: 90 = vertical (bottom->top), 0 = horizontal (left->right).
        stops: list of (t in 0..1, color).
        """
        rad = math.radians(angle)
        cx, cy = x + w / 2, y + h / 2
        half = (abs(math.cos(rad)) * w + abs(math.sin(rad)) * h) / 2
        x0 = cx - math.cos(rad) * half
        y0 = cy - math.sin(rad) * half
        x1 = cx + math.cos(rad) * half
        y1 = cy + math.sin(rad) * half
        name = self._register_shading(x0, y0, x1, y1, stops)
        self.save()
        self.rect_path(x, y, w, h)
        self.clip()
        self.ops.append(f"/{name} sh")
        self.restore()

    def linear_gradient_roundrect(self, x, y, w, h, r, stops, angle=90):
        rad = math.radians(angle)
        cx, cy = x + w / 2, y + h / 2
        half = (abs(math.cos(rad)) * w + abs(math.sin(rad)) * h) / 2
        x0 = cx - math.cos(rad) * half
        y0 = cy - math.sin(rad) * half
        x1 = cx + math.cos(rad) * half
        y1 = cy + math.sin(rad) * half
        name = self._register_shading(x0, y0, x1, y1, stops)
        self.save()
        self.round_rect_path(x, y, w, h, r)
        self.clip()
        self.ops.append(f"/{name} sh")
        self.restore()

    # -- text --------------------------------------------------------------
    def text_width(self, text: str, font: str, size: float) -> float:
        table = FONTS[font][1]
        total = 0
        for ch in text:
            total += table.get(ch, 500)
        return total * size / 1000.0

    def text(self, x, y, text, font='Helvetica', size=12, color='#000000',
             align='left', char_spacing=None):
        self.fonts_used.add(font)
        if align in ('center', 'middle'):
            x -= self.text_width(text, font, size) / 2.0
        elif align == 'right':
            x -= self.text_width(text, font, size)
        r, g, b = _color(color)
        self.ops.append(f"{_fmt(r)} {_fmt(g)} {_fmt(b)} rg")
        self.ops.append("BT")
        if char_spacing is not None:
            self.ops.append(f"{_fmt(char_spacing)} Tc")
        self.ops.append(f"/{_font_alias(font)} {_fmt(size)} Tf")
        self.ops.append(f"{_fmt(x)} {_fmt(y)} Td")
        self.ops.append(f"({_esc(text)}) Tj")
        self.ops.append("ET")
        if char_spacing is not None:
            # reset for safety within stream via new BT next time; Tc persists
            self.ops.append("BT 0 Tc ET")

    def text_tracked(self, x, y, text, font='Helvetica', size=12,
                     color='#000000', tracking=0.0, align='left'):
        """Draw text with letter tracking (extra space between glyphs)."""
        self.fonts_used.add(font)
        table = FONTS[font][1]
        width = sum(table.get(ch, 500) for ch in text) * size / 1000.0
        width += tracking * (len(text) - 1 if len(text) else 0)
        if align in ('center', 'middle'):
            x -= width / 2.0
        elif align == 'right':
            x -= width
        r, g, b = _color(color)
        self.ops.append(f"{_fmt(r)} {_fmt(g)} {_fmt(b)} rg")
        self.ops.append("BT")
        self.ops.append(f"{_fmt(tracking)} Tc")
        self.ops.append(f"/{_font_alias(font)} {_fmt(size)} Tf")
        self.ops.append(f"{_fmt(x)} {_fmt(y)} Td")
        self.ops.append(f"({_esc(text)}) Tj")
        self.ops.append("0 Tc")
        self.ops.append("ET")


def _color(c):
    if isinstance(c, str):
        return hex_to_rgb(c)
    return c  # assume (r,g,b) 0..1 tuple


_FONT_ALIASES = {
    'Helvetica': 'F1',
    'Helvetica-Bold': 'F2',
    'Times': 'F3',
    'Times-Bold': 'F4',
    'Times-Italic': 'F5',
}


def _font_alias(font):
    return _FONT_ALIASES[font]


class Document:
    def __init__(self, title="Document", author="", subject=""):
        self.pages: List[Page] = []
        self.title = title
        self.author = author
        self.subject = subject

    def add_page(self, width=841.89, height=595.28) -> Page:
        p = Page(width, height)
        self.pages.append(p)
        return p

    def save(self, path: str):
        data = self._render()
        with open(path, 'wb') as fh:
            fh.write(data)

    def _render(self) -> bytes:
        objects: List[bytes] = []

        def add_obj(body: bytes) -> int:
            objects.append(body)
            return len(objects)  # 1-based object number

        # Reserve: 1=Catalog, 2=Pages. Fonts follow, then page objects.
        # We build fonts first as shared objects.
        font_objnums: Dict[str, int] = {}

        # placeholders for catalog & pages tree
        catalog_num = add_obj(b'')   # 1
        pages_num = add_obj(b'')     # 2

        # font objects (shared)
        for key, alias in _FONT_ALIASES.items():
            base = FONTS[key][0]
            body = (f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} "
                    f"/Encoding /WinAnsiEncoding >>").encode('latin-1')
            font_objnums[alias] = add_obj(body)

        page_obj_nums = []
        for page in self.pages:
            content = "\n".join(page.ops).encode('latin-1')
            stream = zlib.compress(content)
            content_body = (b"<< /Length " + str(len(stream)).encode() +
                            b" /Filter /FlateDecode >>\nstream\n" + stream +
                            b"\nendstream")
            content_num = add_obj(content_body)

            # resources
            font_res = " ".join(
                f"/{alias} {font_objnums[alias]} 0 R"
                for alias in _FONT_ALIASES.values()
            )
            res_parts = [f"/Font << {font_res} >>"]
            if page.shadings:
                sh = " ".join(f"/Sh{i+1} {s}"
                              for i, s in enumerate(page.shadings))
                res_parts.append(f"/Shading << {sh} >>")
            if page.gstates:
                gs = " ".join(page.gstates)
                res_parts.append(f"/ExtGState << {gs} >>")
            resources = "<< " + " ".join(res_parts) + " >>"

            page_body = (
                f"<< /Type /Page /Parent {pages_num} 0 R "
                f"/MediaBox [0 0 {_fmt(page.width)} {_fmt(page.height)}] "
                f"/Resources {resources} "
                f"/Contents {content_num} 0 R >>"
            ).encode('latin-1')
            page_obj_nums.append(add_obj(page_body))

        # fill in Pages tree
        kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
        objects[pages_num - 1] = (
            f"<< /Type /Pages /Count {len(page_obj_nums)} "
            f"/Kids [{kids}] >>"
        ).encode('latin-1')

        # fill in Catalog
        objects[catalog_num - 1] = (
            f"<< /Type /Catalog /Pages {pages_num} 0 R >>"
        ).encode('latin-1')

        # info object
        info_num = add_obj((
            f"<< /Title ({_esc(self.title)}) /Author ({_esc(self.author)}) "
            f"/Subject ({_esc(self.subject)}) /Producer (pdfkit.py) >>"
        ).encode('latin-1'))

        # assemble file
        out = bytearray()
        out += b"%PDF-1.7\n%\xE2\xE3\xCF\xD3\n"
        offsets = [0] * (len(objects) + 1)
        for i, body in enumerate(objects, start=1):
            offsets[i] = len(out)
            out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"

        xref_pos = len(out)
        n = len(objects) + 1
        out += b"xref\n"
        out += f"0 {n}\n".encode()
        out += b"0000000000 65535 f \n"
        for i in range(1, n):
            out += f"{offsets[i]:010d} 00000 n \n".encode()
        out += b"trailer\n"
        out += (f"<< /Size {n} /Root {catalog_num} 0 R "
                f"/Info {info_num} 0 R >>\n").encode()
        out += b"startxref\n"
        out += f"{xref_pos}\n".encode()
        out += b"%%EOF\n"
        return bytes(out)
