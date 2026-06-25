"""
PDF export for EPP documents.

This mirrors the visual rules in epp-style.css / epp-core.js as closely as
practical with ReportLab's canvas API: cream paper background, serif body
text, mono header/footer bands, accent-colored rule lines and bullets,
shaded tables, quote bars, and code blocks.

This module is optional: the GUI app calls it lazily so the rest of the
viewer works even on a machine without `reportlab` installed. If it's
missing, the caller shows the user a one-line message about installing it.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from epp_parser import (
    COLOR_MAP, BULLET_GLYPHS, ALIGN_VALUES, EPPDocument, Page,
    CALLOUT_COLORS, HIGHLIGHT_COLORS, PAGE_COLORS, PAGE_ROTATE_VALUES,
)

PAPER_BG = HexColor("#faf6ec")
PAPER_INK = HexColor("#211c14")
ACCENT = HexColor("#c98a3e")
RULE = HexColor("#b9af98")
QUOTE_INK = HexColor("#5b564a")
CODE_BG = HexColor("#efe9da")
TABLE_HEAD_BG = HexColor("#ede7d6")
TABLE_ALT_BG = HexColor("#f4f0e6")
EMPTY_HINT = HexColor("#8a8270")
FOOTER_FALLBACK_INK = HexColor("#8a8270")
LINE_RULE_SPACING = 26
LINE_RULE_COLOR = HexColor("#b9af98")
LINE_MARGIN_COLOR = HexColor("#dc7864")

SERIF = "Times-Roman"
SERIF_BOLD = "Times-Bold"
SERIF_ITALIC = "Times-Italic"
SERIF_BOLD_ITALIC = "Times-BoldItalic"
MONO = "Courier"

SIDE_MARGIN = 56
TOP_MARGIN = 56
BOTTOM_MARGIN = 56


def _hex_color(name, fallback=PAPER_INK):
    h = COLOR_MAP.get(name)
    return HexColor(h) if h else fallback


def _page_palette(page_attrs):
    """v0.3: resolve a page's {color=} attribute to (bg, ink) HexColors,
    defaulting to the plain cream/paper-ink pair used pre-v0.3."""
    key = (page_attrs or {}).get("color")
    palette = PAGE_COLORS.get(key)
    if not palette:
        return PAPER_BG, PAPER_INK
    return HexColor(palette["bg"]), HexColor(palette["ink"])


class _NoOpCanvas:
    """Absorbs every ReportLab canvas call used by the body-drawing
    helpers below, without writing anything -- used for a dry-run sizing
    pass (e.g. to know a lined page's rule extent, or a rotated body's
    real footprint, before committing to the real drawing pass)."""

    def setFont(self, *a, **k): pass
    def setFillColor(self, *a, **k): pass
    def setStrokeColor(self, *a, **k): pass
    def drawString(self, *a, **k): pass
    def drawCentredString(self, *a, **k): pass
    def rect(self, *a, **k): pass
    def line(self, *a, **k): pass
    def roundRect(self, *a, **k): pass
    def saveState(self, *a, **k): pass
    def restoreState(self, *a, **k): pass
    def translate(self, *a, **k): pass
    def rotate(self, *a, **k): pass


def _body_font(bold, italic):
    if bold and italic:
        return SERIF_BOLD_ITALIC
    if bold:
        return SERIF_BOLD
    if italic:
        return SERIF_ITALIC
    return SERIF


def _wrap_text(text, font, size, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if stringWidth(trial, font, size) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _align_x(left, width, align, text_w):
    if align == "center":
        return left + max(0, (width - text_w) / 2)
    if align == "right":
        return left + max(0, width - text_w)
    return left


class PDFPageWriter:
    def __init__(self, c: pdfcanvas.Canvas, page_w, page_h):
        self.c = c
        self.page_w = page_w
        self.page_h = page_h

    def new_page(self, bg=PAPER_BG):
        c = self.c
        c.setFillColor(bg)
        c.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)
        c.setFillColor(PAPER_INK)

    def draw_lined_background(self, body_top, body_bottom, content_left, content_w):
        """v0.3 @page {lined}: horizontal notebook-style rules at fixed
        intervals across the body area, plus a left margin rule. Bounded
        to the page's actual final body extent (mirrors the Tk renderer's
        _draw_lined_background)."""
        c = self.c
        c.setStrokeColor(LINE_RULE_COLOR)
        ry = body_top
        while ry <= body_bottom:
            y_pdf = self.page_h - ry
            c.line(0, y_pdf, self.page_w, y_pdf)
            ry += LINE_RULE_SPACING
        margin_x = content_left + 12
        c.setStrokeColor(LINE_MARGIN_COLOR)
        c.line(margin_x, self.page_h - body_top, margin_x, self.page_h - body_bottom)

    def draw_band(self, y_from_top, text, top_border, bottom_border, content_w):
        c = self.c
        size = 8
        lines = text.split("[newline]")
        line_h = size * 1.5
        pad_v = 8
        cy_top = self.page_h - y_from_top
        if top_border:
            c.setStrokeColor(RULE)
            c.line(SIDE_MARGIN, cy_top, SIDE_MARGIN + content_w, cy_top)
        c.setFont(MONO, size)
        c.setFillColor(RULE)
        ty = cy_top - pad_v - size * 0.8
        for line in lines:
            w = stringWidth(line, MONO, size)
            c.drawString(SIDE_MARGIN + (content_w - w) / 2, ty, line)
            ty -= line_h
        height = pad_v * 2 + line_h * len(lines)
        bottom_y = y_from_top + height
        if bottom_border:
            c.setStrokeColor(RULE)
            cy_bottom = self.page_h - bottom_y
            c.line(SIDE_MARGIN, cy_bottom, SIDE_MARGIN + content_w, cy_bottom)
        c.setFillColor(PAPER_INK)
        return bottom_y

    def draw_fallback_footer(self, y_from_top, page_number, content_w):
        c = self.c
        size = 9
        text = str(page_number)
        w = stringWidth(text, MONO, size)
        cy = self.page_h - y_from_top - 6 - size * 0.8
        c.setFont(MONO, size)
        c.setFillColor(FOOTER_FALLBACK_INK)
        c.drawString(SIDE_MARGIN + (content_w - w) / 2, cy, text)
        c.setFillColor(PAPER_INK)
        return y_from_top + 6 + size * 1.5 + 10


def export_pdf(doc: EPPDocument, out_path: str, fonts=None):
    """Render an EPPDocument to a PDF file at out_path. `fonts` is unused
    (kept for interface symmetry with the Tk renderer) since PDF uses its
    own built-in font set."""
    page_w, page_h = A4
    content_w = page_w - 2 * SIDE_MARGIN

    c = pdfcanvas.Canvas(out_path, pagesize=A4)
    total = len(doc.pages)

    for idx, page in enumerate(doc.pages):
        page_attrs = getattr(page, "page_attrs", {}) or {}
        page_bg, page_ink = _page_palette(page_attrs)

        writer = PDFPageWriter(c, page_w, page_h)
        writer.new_page(bg=page_bg)
        page_number = page.number or str(idx + 1)

        y = TOP_MARGIN
        if doc.header:
            y = writer.draw_band(y, doc.header, top_border=False, bottom_border=True, content_w=content_w)

        body_top = y + 28

        rotate_raw = str(page_attrs.get("rotate")) if page_attrs.get("rotate") else None
        rotate_deg = int(rotate_raw) if rotate_raw in PAGE_ROTATE_VALUES else 0

        # v0.3 {lined}: the rule background must sit *behind* the body
        # content but its extent depends on the body's final height, so
        # measure first with a no-op canvas, draw the lines, then draw
        # the real body on top -- same two-pass approach as the Tk port.
        if page_attrs.get("lined"):
            measured_end = _measure_body_height_pdf(page, body_top, content_w, page_h,
                                                      rotate_deg, page_w)
            measured_bottom = max(measured_end, body_top + 1) + 20
            writer.draw_lined_background(body_top, measured_bottom, SIDE_MARGIN, content_w)

        if rotate_deg:
            y_body_end = _draw_rotated_body_pdf(c, page, body_top, content_w, page_h,
                                                 page_w, rotate_deg, page_ink)
        else:
            y_body_end = _draw_body_pdf(c, page, body_top, content_w, page_h, page_ink=page_ink)
        body_bottom = max(y_body_end, body_top + 1) + 20

        y = body_bottom
        if doc.footer:
            footer_text = doc.footer.replace("[page]", str(page_number))
            writer.draw_band(y, footer_text, top_border=True, bottom_border=False, content_w=content_w)
        else:
            writer.draw_fallback_footer(y, page_number, content_w)

        if idx < total - 1:
            c.showPage()

    c.save()


def _draw_body_pdf(c, page: Page, top, content_w, page_h, page_ink=None, left=None):
    left = SIDE_MARGIN if left is None else left
    page_ink = page_ink or PAPER_INK
    y = top
    list_counter = 0
    total = len(page.blocks)
    label_positions = []

    for idx, block in enumerate(page.blocks):
        if block.type != "bullet":
            list_counter = 0

        if block.type == "heading":
            y = _draw_paragraph_pdf(c, block, left, content_w, y, page_h,
                                     base_size=17, bottom_margin=14, bold_default=True,
                                     page_ink=page_ink)
        elif block.type == "text":
            y = _draw_paragraph_pdf(c, block, left, content_w, y, page_h,
                                     base_size=11, bottom_margin=10, bold_default=False,
                                     page_ink=page_ink)
        elif block.type == "bullet":
            list_counter += 1
            y = _draw_bullet_pdf(c, block, left, content_w, y, page_h, list_counter, page_ink)
        elif block.type == "code":
            y = _draw_code_pdf(c, block, left, content_w, y, page_h)
        elif block.type == "callout":
            y = _draw_callout_pdf(c, block, left, content_w, y, page_h)
        elif block.type == "space":
            y += 16
        elif block.type == "line":
            y += 5
            c.setStrokeColor(RULE)
            c.line(left, page_h - y, left + content_w, page_h - y)
            y += 11
        elif block.type == "quote":
            y = _draw_quote_pdf(c, block, left, content_w, y, page_h)
        elif block.type == "table":
            y = _draw_table_pdf(c, block, left, content_w, y, page_h)
        elif block.type == "label":
            label_positions.append((idx, block.name))

    if total == 0:
        c.setFont(SERIF_ITALIC, 11)
        c.setFillColor(EMPTY_HINT)
        c.drawString(left, page_h - top - 11, "This page is empty.")
        c.setFillColor(PAPER_INK)
        y = top + 20

    body_height = y - top

    # Label tabs are page-edge chrome, never rotated, and skipped
    # entirely during a measuring pass (a _NoOpCanvas dry run has zero
    # side effects by design -- otherwise it would draw a real, stray
    # tab that a later real pass then draws again on top of).
    if not isinstance(c, _NoOpCanvas):
        for idx, name in label_positions:
            frac = 0.5 if total <= 1 else (idx / (total - 1))
            tab_y = top + frac * max(body_height, 1)
            _draw_label_tab_pdf(c, left + content_w, tab_y, name, page_h)

    return y


def _draw_paragraph_pdf(c, block, left, width, y, page_h, base_size, bottom_margin,
                         bold_default, page_ink=None):
    attrs = block.attrs or {}
    color = _hex_color(attrs.get("color"), page_ink or PAPER_INK)
    align = attrs.get("align") if attrs.get("align") in ALIGN_VALUES else "left"
    bold = bool(attrs.get("bold")) or bold_default
    italic = bool(attrs.get("italic"))
    underline = bool(attrs.get("underline"))
    highlight_key = attrs.get("highlight")
    highlight_color = HIGHLIGHT_COLORS.get(highlight_key)
    font = _body_font(bold, italic)
    line_h = base_size * 1.45

    c.setFont(font, base_size)
    c.setFillColor(color)
    for raw_line in block.text.split("[newline]"):
        wrapped = _wrap_text(raw_line, font, base_size, width) if raw_line else [""]
        for line in wrapped:
            w = stringWidth(line, font, base_size)
            x = _align_x(left, width, align, w)
            baseline = page_h - y - base_size * 0.85
            if highlight_color:
                # v0.3 highlight=: a background tint behind the text,
                # approximating the <mark> the web renderer uses. Drawn
                # immediately before the text so it sits behind it.
                c.setFillColor(HexColor(highlight_color))
                pad = 2
                c.rect(x - pad, baseline - 2, w + pad * 2, base_size * 1.15, fill=1, stroke=0)
                c.setFillColor(color)
            c.drawString(x, baseline, line)
            if underline:
                c.setStrokeColor(color)
                c.line(x, baseline - 1.5, x + w, baseline - 1.5)
            y += line_h
    c.setFillColor(PAPER_INK)
    return y + bottom_margin


def _draw_bullet_pdf(c, block, left, width, y, page_h, counter, page_ink=None):
    attrs = block.attrs or {}
    accent_color = _hex_color(attrs.get("color"), ACCENT)
    text_color = _hex_color(attrs.get("color"), page_ink or PAPER_INK)
    btype = attrs.get("type", "disc")
    glyph_w = 22
    gap = 8
    size = 11
    line_h = size * 1.45

    glyph = f"{counter}." if btype == "number" else (BULLET_GLYPHS.get(btype) or "\u2022")

    baseline = page_h - y - size * 0.85
    c.setFont(MONO, size * 0.95)
    c.setFillColor(accent_color)
    gw = stringWidth(glyph, MONO, size * 0.95)
    c.drawString(left + glyph_w - gw, baseline, glyph)

    text_left = left + glyph_w + gap
    text_width = width - glyph_w - gap
    c.setFont(SERIF, size)
    c.setFillColor(text_color)
    cy = y
    for raw_line in block.text.split("[newline]"):
        wrapped = _wrap_text(raw_line, SERIF, size, text_width) if raw_line else [""]
        for line in wrapped:
            c.drawString(text_left, page_h - cy - size * 0.85, line)
            cy += line_h
    c.setFillColor(PAPER_INK)
    return cy + 4


def _draw_code_pdf(c, block, left, width, y, page_h):
    pad_x, pad_y = 10, 9
    border_w = 3
    size = 9.5
    raw_lines = []
    for chunk in block.text.split("[newline]"):
        raw_lines.extend(chunk.split("\n"))
    line_h = size * 1.5
    block_height = pad_y * 2 + line_h * max(1, len(raw_lines))

    c.setFillColor(CODE_BG)
    c.rect(left, page_h - y - block_height, width, block_height, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(left, page_h - y - block_height, border_w, block_height, fill=1, stroke=0)

    c.setFont(MONO, size)
    c.setFillColor(PAPER_INK)
    ty = y + pad_y
    for line in raw_lines:
        c.drawString(left + border_w + pad_x, page_h - ty - size * 0.85, line)
        ty += line_h
    return y + block_height + 12


def _draw_quote_pdf(c, block, left, width, y, page_h):
    pad_x, pad_y = 14, 8
    border_w = 3
    size = 11
    text_width = width - pad_x - border_w
    lines = []
    for raw_line in block.text.split("[newline]"):
        lines.extend(_wrap_text(raw_line, SERIF_ITALIC, size, text_width) if raw_line else [""])
    line_h = size * 1.45
    block_height = pad_y * 2 + line_h * len(lines)

    c.setFillColor(ACCENT)
    c.rect(left, page_h - y - block_height, border_w, block_height, fill=1, stroke=0)
    c.setFont(SERIF_ITALIC, size)
    c.setFillColor(QUOTE_INK)
    ty = y + pad_y
    for line in lines:
        c.drawString(left + border_w + pad_x, page_h - ty - size * 0.85, line)
        ty += line_h
    c.setFillColor(PAPER_INK)
    return y + block_height + 14


def _draw_callout_pdf(c, block, left, width, y, page_h):
    """v0.3 @callout: a coloured notice box with an auto-generated label
    (e.g. "Note", "Danger") looked up from CALLOUT_COLORS, matching the
    web renderer's behavior exactly -- the label is never author-supplied."""
    attrs = block.attrs or {}
    color_key = attrs.get("color") or "yellow"
    palette = CALLOUT_COLORS.get(color_key, CALLOUT_COLORS["yellow"])
    bg = HexColor(palette["bg"])
    border = HexColor(palette["border"])
    text_color = HexColor(palette["text"])
    label = palette["label"]

    pad_x, pad_y = 13, 9
    border_w = 3
    label_size = 8
    body_size = 11
    text_width = width - pad_x * 2 - border_w

    label_h = label_size * 1.3
    lines = []
    for raw_line in block.text.split("[newline]"):
        lines.extend(_wrap_text(raw_line, SERIF, body_size, text_width) if raw_line else [""])
    body_line_h = body_size * 1.35
    block_height = pad_y * 2 + label_h + 3 + body_line_h * len(lines)

    c.setFillColor(bg)
    c.rect(left, page_h - y - block_height, width, block_height, fill=1, stroke=0)
    c.setFillColor(border)
    c.rect(left, page_h - y - block_height, border_w, block_height, fill=1, stroke=0)

    tx = left + border_w + pad_x
    c.setFont(MONO, label_size)
    c.setFillColor(border)
    label_baseline = page_h - (y + pad_y) - label_size * 0.85
    c.drawString(tx, label_baseline, label.upper())

    c.setFont(SERIF, body_size)
    c.setFillColor(text_color)
    ty = y + pad_y + label_h + 3
    for line in lines:
        c.drawString(tx, page_h - ty - body_size * 0.85, line)
        ty += body_line_h

    c.setFillColor(PAPER_INK)
    return y + block_height + 12


def _draw_table_pdf(c, block, left, width, y, page_h):
    headers = [h.strip() for h in block.headers]
    rows = [[cell.strip() for cell in row] for row in block.rows]
    ncols = max(len(headers), max((len(r) for r in rows), default=0), 1)
    col_w = width / ncols
    pad_x = 8
    size = 10
    row_h = size * 1.7

    def draw_row(cells, y0, bg, bold):
        c.setFillColor(bg)
        c.rect(left, page_h - y0 - row_h, width, row_h, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.rect(left, page_h - y0 - row_h, width, row_h, fill=0, stroke=1)
        font = SERIF_BOLD if bold else SERIF
        c.setFont(font, size)
        c.setFillColor(PAPER_INK)
        for col in range(ncols):
            cx = left + col * col_w
            c.line(cx, page_h - y0, cx, page_h - y0 - row_h) if col > 0 else None
            text = cells[col] if col < len(cells) else ""
            c.drawString(cx + pad_x, page_h - y0 - row_h / 2 - size * 0.32, text)

    cy = y
    if headers:
        draw_row(headers, cy, TABLE_HEAD_BG, True)
        cy += row_h
    for i, row in enumerate(rows):
        bg = TABLE_ALT_BG if i % 2 == 1 else PAPER_BG
        draw_row(row, cy, bg, False)
        cy += row_h
    c.setFillColor(PAPER_INK)
    return cy + 14


def _draw_label_tab_pdf(c, x, y, name, page_h):
    size = 7
    text = name.upper()
    text_w = stringWidth(text, MONO, size)
    pad = 4
    box_w = size + pad * 2
    box_h = text_w + pad * 2

    c.saveState()
    cy = page_h - y
    c.translate(x + box_w / 2, cy)
    c.rotate(90)
    c.setFillColor(ACCENT)
    c.roundRect(-box_h / 2, -box_w / 2, box_h, box_w, 2, fill=1, stroke=0)
    c.setFont(MONO, size)
    c.setFillColor(HexColor("#1b1b1a"))
    c.drawCentredString(0, -size * 0.32, text)
    c.restoreState()


def _measure_body_height_pdf(page, body_top, content_w, page_h, rotate_deg, page_w):
    """Dry-run _draw_body_pdf (or its rotated counterpart) against a
    _NoOpCanvas to find out how much vertical space a page's body will
    actually need, without drawing anything -- used so a {lined}
    background's extent can be computed before the real body (which
    must be drawn on top of, not under, the lines) is drawn for real."""
    noop = _NoOpCanvas()
    if rotate_deg:
        return _draw_rotated_body_pdf(noop, page, body_top, content_w, page_h,
                                       page_w, rotate_deg, PAPER_INK)
    return _draw_body_pdf(noop, page, body_top, content_w, page_h, page_ink=PAPER_INK)


def _draw_rotated_body_pdf(c, page, body_top, content_w, page_h, page_w, rotate_deg, page_ink):
    """v0.3 @page {rotate=90|180|270}.

    Mirrors the reference CSS's two different techniques (see the Tk
    renderer's _draw_rotated_body for the full rationale):

    - 180: the body is simply flipped upside down in place -- text still
      wraps against the page's normal content width. ReportLab's native
      rotate() around the body's own center reproduces this exactly with
      no re-flow needed.

    - 90 / 270: content re-flows against the *page's height* as the
      wrapping width (matching `writing-mode:vertical-rl/lr`), so we
      measure the real local content height with a _NoOpCanvas dry run
      first, then draw for real rotated 90/270 around that measured
      block's own center, translated back onto the page's body center
      -- otherwise short content ends up off-center and long content
      can overflow the page edge, exactly the bug the Tk port hit before
      this same fix was applied there.
    """
    provisional_height = content_w  # same fixed allowance the Tk port uses via MIN_BODY_HEIGHT-equivalent
    center_x = page_w / 2
    center_y = page_h - (body_top + provisional_height / 2)  # ReportLab y grows upward

    if rotate_deg == 180:
        c.saveState()
        c.translate(center_x, center_y)
        c.rotate(180)
        c.translate(-center_x, -center_y)
        _draw_body_pdf(c, page, body_top, content_w, page_h, page_ink=page_ink)
        c.restoreState()
        # Matches _draw_body_pdf's contract: callers compute
        # `body_bottom = max(y_body_end, body_top+1) + 20`, so this
        # must be an *absolute* y-position, not a bare height allowance.
        return body_top + provisional_height

    # 90 or 270: measure first against the swapped wrap width.
    wrap_width = provisional_height
    noop = _NoOpCanvas()
    measured_height = _draw_body_pdf(noop, page, body_top, wrap_width, page_h, page_ink=page_ink,
                                      left=SIDE_MARGIN) - body_top

    local_pivot_x = SIDE_MARGIN + wrap_width / 2
    local_pivot_y_pdf = page_h - (body_top + measured_height / 2)

    c.saveState()
    # Move the local pivot to the origin, rotate, then move the origin
    # back out to where the real page's body center is -- equivalent to
    # "rotate in place, then recenter," same as the Tk RotatedDrawing.
    c.translate(center_x, center_y)
    # ReportLab's rotate() is mathematically CCW-positive (the canvas's
    # y axis points up), but the spec defines 90 as *visually* clockwise
    # and 270 as *visually* counter-clockwise. So visual-clockwise-90
    # needs rotate(-90), and visual-counter-clockwise-270 needs
    # rotate(+90) -- the inverse of what passing rotate_deg through
    # directly would give.
    c.rotate(-90 if rotate_deg == 90 else 90)
    c.translate(-local_pivot_x, -local_pivot_y_pdf)
    _draw_body_pdf(c, page, body_top, wrap_width, page_h, page_ink=page_ink)
    c.restoreState()

    # Same absolute-y contract as the 180 branch above.
    return body_top + provisional_height
