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

from epp_parser import COLOR_MAP, BULLET_GLYPHS, ALIGN_VALUES, EPPDocument, Page

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

    def new_page(self):
        c = self.c
        c.setFillColor(PAPER_BG)
        c.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)
        c.setFillColor(PAPER_INK)

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
        writer = PDFPageWriter(c, page_w, page_h)
        writer.new_page()
        page_number = page.number or str(idx + 1)

        y = TOP_MARGIN
        if doc.header:
            y = writer.draw_band(y, doc.header, top_border=False, bottom_border=True, content_w=content_w)

        body_top = y + 28
        y_body_end = _draw_body_pdf(c, page, body_top, content_w, page_h)
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


def _draw_body_pdf(c, page: Page, top, content_w, page_h):
    left = SIDE_MARGIN
    y = top
    list_counter = 0
    total = len(page.blocks)
    label_positions = []

    for idx, block in enumerate(page.blocks):
        if block.type != "bullet":
            list_counter = 0

        if block.type == "heading":
            y = _draw_paragraph_pdf(c, block, left, content_w, y, page_h,
                                     base_size=17, bottom_margin=14, bold_default=True)
        elif block.type == "text":
            y = _draw_paragraph_pdf(c, block, left, content_w, y, page_h,
                                     base_size=11, bottom_margin=10, bold_default=False)
        elif block.type == "bullet":
            list_counter += 1
            y = _draw_bullet_pdf(c, block, left, content_w, y, page_h, list_counter)
        elif block.type == "code":
            y = _draw_code_pdf(c, block, left, content_w, y, page_h)
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
    for idx, name in label_positions:
        frac = 0.5 if total <= 1 else (idx / (total - 1))
        tab_y = top + frac * max(body_height, 1)
        _draw_label_tab_pdf(c, left + content_w, tab_y, name, page_h)

    return y


def _draw_paragraph_pdf(c, block, left, width, y, page_h, base_size, bottom_margin, bold_default):
    attrs = block.attrs or {}
    color = _hex_color(attrs.get("color"), PAPER_INK)
    align = attrs.get("align") if attrs.get("align") in ALIGN_VALUES else "left"
    bold = bool(attrs.get("bold")) or bold_default
    italic = bool(attrs.get("italic"))
    underline = bool(attrs.get("underline"))
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
            c.drawString(x, baseline, line)
            if underline:
                c.setStrokeColor(color)
                c.line(x, baseline - 1.5, x + w, baseline - 1.5)
            y += line_h
    c.setFillColor(PAPER_INK)
    return y + bottom_margin


def _draw_bullet_pdf(c, block, left, width, y, page_h, counter):
    attrs = block.attrs or {}
    accent_color = _hex_color(attrs.get("color"), ACCENT)
    text_color = _hex_color(attrs.get("color"), PAPER_INK)
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
