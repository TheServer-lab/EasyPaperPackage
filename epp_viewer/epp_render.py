"""
EPP document renderer for Tkinter.

Draws a single page of a parsed EPPDocument onto a Tkinter Canvas, closely
matching the visual styling of the original epp-style.css (paper colors,
serif/mono fonts, rule lines, bullet glyphs, tables, quote bars, label
tabs, header/footer bands).

The canvas is built at a fixed "design" width and a dynamically computed
height (pages grow to fit content, like the web viewer does), then the
caller can scale/scroll it as needed.
"""

import tkinter as tk
import tkinter.font as tkfont

from epp_parser import COLOR_MAP, BULLET_GLYPHS, ALIGN_VALUES

# ---- palette (from :root in epp-style.css) ----
PAPER_BG = "#faf6ec"
PAPER_INK = "#211c14"
ACCENT = "#c98a3e"
RULE = "#b9af98"
QUOTE_INK = "#5b564a"
CODE_BG = "#efe9da"
TABLE_HEAD_BG = "#ede7d6"
TABLE_ALT_BG = "#f4f0e6"
EMPTY_HINT = "#8a8270"
FOOTER_FALLBACK_INK = "#8a8270"

# ---- fonts (fallback chains; Tk silently substitutes if unavailable) ----
SERIF_CANDIDATES = ["Iowan Old Style", "Palatino Linotype", "Palatino", "Georgia", "Times New Roman", "serif"]
MONO_CANDIDATES = ["SF Mono", "Cascadia Code", "JetBrains Mono", "Menlo", "Consolas", "Courier New", "monospace"]

PAGE_WIDTH = 560        # matches `min(560px, 92vw)` design width
SIDE_PADDING = 40
BODY_TOP_PADDING = 36
BODY_BOTTOM_PADDING = 24
MIN_BODY_HEIGHT = int(PAGE_WIDTH * 1.3)  # matches CSS min-height rule


def _pick_available_font(root, candidates, fallback_family):
    available = set(tkfont.families(root))
    for name in candidates:
        if name in available:
            return name
    return fallback_family


class Fonts:
    """Resolved font objects, sized similarly to the CSS (15px body / 1.6 line-height)."""

    def __init__(self, root):
        serif = _pick_available_font(root, SERIF_CANDIDATES, "Georgia")
        mono = _pick_available_font(root, MONO_CANDIDATES, "Courier")
        self.serif_family = serif
        self.mono_family = mono

        self.body = tkfont.Font(root=root, family=serif, size=12)
        self.body_bold = tkfont.Font(root=root, family=serif, size=12, weight="bold")
        self.body_italic = tkfont.Font(root=root, family=serif, size=12, slant="italic")
        self.body_bold_italic = tkfont.Font(root=root, family=serif, size=12, weight="bold", slant="italic")

        self.heading = tkfont.Font(root=root, family=serif, size=17, weight="bold")
        self.heading_italic = tkfont.Font(root=root, family=serif, size=17, weight="bold", slant="italic")

        self.mono_band = tkfont.Font(root=root, family=mono, size=8)
        self.mono_code = tkfont.Font(root=root, family=mono, size=10)
        self.mono_glyph = tkfont.Font(root=root, family=mono, size=11)
        self.mono_label = tkfont.Font(root=root, family=mono, size=7, weight="bold")
        self.footer_fallback = tkfont.Font(root=root, family=mono, size=9)
        self.table = tkfont.Font(root=root, family=serif, size=11)
        self.table_bold = tkfont.Font(root=root, family=serif, size=11, weight="bold")

    def body_variant(self, bold, italic):
        if bold and italic:
            return self.body_bold_italic
        if bold:
            return self.body_bold
        if italic:
            return self.body_italic
        return self.body


def block_color(attrs):
    if not attrs:
        return None
    c = attrs.get("color")
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    return None


def block_align(attrs):
    if attrs and attrs.get("align") in ALIGN_VALUES:
        return attrs["align"]
    return "left"


def inline_text_lines(text):
    """EPP uses literal '[newline]' as a forced line break within a string."""
    return text.split("[newline]")


class PageCanvas(tk.Canvas):
    """A Canvas that draws one EPP page, matching the web viewer's look."""

    def __init__(self, master, fonts: Fonts, **kwargs):
        kwargs.setdefault("bg", PAPER_BG)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self.fonts = fonts

    def draw_page(self, page, page_number, header, footer):
        self.delete("all")
        y = 0
        width = PAGE_WIDTH

        # header band
        if header:
            y = self._draw_band(y, width, header, top_border=False, bottom_border=True)

        body_top = y + BODY_TOP_PADDING
        body_height = self._draw_body(page, body_top, width)
        body_bottom = max(body_top + body_height, y + MIN_BODY_HEIGHT) + BODY_BOTTOM_PADDING
        y = body_bottom

        # footer band
        if footer:
            footer_text = footer.replace("[page]", str(page_number))
            y = self._draw_band(y, width, footer_text, top_border=True, bottom_border=False)
        else:
            y = self._draw_fallback_footer(y, width, page_number)

        self.configure(width=width, height=int(y) + 1, scrollregion=(0, 0, width, int(y) + 1))
        return int(y) + 1

    # ---- bands ----

    def _draw_band(self, y, width, text, top_border, bottom_border):
        pad_v = 8
        lines = inline_text_lines(text)
        line_h = self.fonts.mono_band.metrics("linespace")
        height = pad_v * 2 + line_h * len(lines)
        if top_border:
            self.create_line(0, y, width, y, fill=RULE)
        cy = y + pad_v
        for line in lines:
            self.create_text(width / 2, cy, text=line, font=self.fonts.mono_band,
                              fill=RULE, anchor="n", justify="center")
            cy += line_h
        y2 = y + height
        if bottom_border:
            self.create_line(0, y2, width, y2, fill=RULE)
        return y2

    def _draw_fallback_footer(self, y, width, page_number):
        pad_top, pad_bottom = 6, 10
        line_h = self.fonts.footer_fallback.metrics("linespace")
        cy = y + pad_top
        self.create_text(width / 2, cy, text=str(page_number), font=self.fonts.footer_fallback,
                          fill=FOOTER_FALLBACK_INK, anchor="n", justify="center")
        return y + pad_top + line_h + pad_bottom

    # ---- body ----

    def _draw_body(self, page, top, page_width):
        content_left = SIDE_PADDING
        content_right = page_width - SIDE_PADDING
        content_width = content_right - content_left
        y = top
        list_counter = 0
        in_list = False
        total = len(page.blocks)
        label_positions = []  # (idx, name) to place after we know body height

        for idx, block in enumerate(page.blocks):
            if block.type != "bullet":
                in_list = False
                list_counter = 0

            if block.type == "heading":
                y = self._draw_paragraph(block, content_left, content_width, y,
                                          font_plain=self.fonts.heading,
                                          font_italic=self.fonts.heading_italic,
                                          bottom_margin=14)
            elif block.type == "text":
                y = self._draw_paragraph(block, content_left, content_width, y,
                                          font_plain=self.fonts.body,
                                          font_italic=self.fonts.body_italic,
                                          bottom_margin=12)
            elif block.type == "bullet":
                in_list = True
                list_counter += 1
                y = self._draw_bullet(block, content_left, content_width, y, list_counter)
            elif block.type == "code":
                y = self._draw_code(block, content_left, content_width, y)
            elif block.type == "space":
                y += 18
            elif block.type == "line":
                y += 5
                self.create_line(content_left, y, content_right, y, fill=RULE)
                y += 11
            elif block.type == "quote":
                y = self._draw_quote(block, content_left, content_width, y)
            elif block.type == "table":
                y = self._draw_table(block, content_left, content_width, y)
            elif block.type == "label":
                label_positions.append((idx, block.name))

        if total == 0:
            font = self.fonts.body_italic
            self.create_text(content_left, y, text="This page is empty.", font=font,
                              fill=EMPTY_HINT, anchor="nw")
            y += font.metrics("linespace")

        body_height = y - top

        # place label tabs along the right edge, proportional to position in flow
        for idx, name in label_positions:
            frac = 0.5 if total <= 1 else (idx / (total - 1))
            tab_y = top + frac * max(body_height, 1)
            self._draw_label_tab(page_width - SIDE_PADDING, tab_y, name)

        return body_height

    def _wrap_text(self, text, font, max_width):
        """Greedy word-wrap using actual font metrics."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if font.measure(trial) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_paragraph(self, block, left, width, y, font_plain, font_italic, bottom_margin):
        attrs = block.attrs or {}
        color = block_color(attrs) or PAPER_INK
        align = block_align(attrs)
        bold = bool(attrs.get("bold"))
        italic = bool(attrs.get("italic"))
        underline = bool(attrs.get("underline"))

        if font_plain is self.fonts.heading:
            font = self.fonts.heading_italic if italic else self.fonts.heading
        else:
            font = self.fonts.body_variant(bold, italic)
        # Tk fonts created above already encode bold for heading; ensure weight for body headings too
        if font_plain is self.fonts.heading and bold is False:
            font = self.fonts.heading_italic if italic else self.fonts.heading

        underline_font = font.copy()
        underline_font.configure(underline=1)
        draw_font = underline_font if underline else font

        for raw_line in inline_text_lines(block.text):
            wrapped = self._wrap_text(raw_line, draw_font, width) if raw_line else [""]
            for line in wrapped:
                x = self._x_for_align(left, width, align, draw_font.measure(line))
                self.create_text(x, y, text=line, font=draw_font, fill=color, anchor="nw")
                y += draw_font.metrics("linespace") * 1.3
        return y + bottom_margin

    def _x_for_align(self, left, width, align, text_w):
        if align == "center":
            return left + max(0, (width - text_w) / 2)
        if align == "right":
            return left + max(0, width - text_w)
        return left

    def _draw_bullet(self, block, left, width, y, counter):
        attrs = block.attrs or {}
        color = block_color(attrs) or ACCENT
        text_color = block_color(attrs) or PAPER_INK
        btype = attrs.get("type", "disc")
        glyph_w = 24
        gap = 8

        if btype == "number":
            glyph = f"{counter}."
        else:
            glyph = BULLET_GLYPHS.get(btype) or "\u2022"

        self.create_text(left + glyph_w, y, text=glyph, font=self.fonts.mono_glyph,
                          fill=color, anchor="ne")

        text_left = left + glyph_w + gap
        text_width = width - glyph_w - gap
        font = self.fonts.body
        max_line_h = 0
        cy = y
        first = True
        for raw_line in inline_text_lines(block.text):
            wrapped = self._wrap_text(raw_line, font, text_width) if raw_line else [""]
            for line in wrapped:
                self.create_text(text_left, cy, text=line, font=font, fill=text_color, anchor="nw")
                cy += font.metrics("linespace") * 1.3
                max_line_h = font.metrics("linespace") * 1.3
        return cy + 4  # margin-bottom: 4px between bullets, like CSS

    def _draw_code(self, block, left, width, y):
        pad_x, pad_y = 12, 10
        border_w = 3
        font = self.fonts.mono_code
        raw_lines = []
        for chunk in block.text.split("[newline]"):
            raw_lines.extend(chunk.split("\n"))
        line_h = font.metrics("linespace")
        block_height = pad_y * 2 + line_h * max(1, len(raw_lines))

        self.create_rectangle(left, y, left + width, y + block_height, fill=CODE_BG, outline="")
        self.create_rectangle(left, y, left + border_w, y + block_height, fill=ACCENT, outline="")

        ty = y + pad_y
        for line in raw_lines:
            self.create_text(left + border_w + pad_x, ty, text=line, font=font,
                              fill=PAPER_INK, anchor="nw")
            ty += line_h
        return y + block_height + 12

    def _draw_quote(self, block, left, width, y):
        pad_x, pad_y = 16, 8
        border_w = 3
        font = self.fonts.body_italic
        text_width = width - pad_x - border_w
        lines = []
        for raw_line in inline_text_lines(block.text):
            lines.extend(self._wrap_text(raw_line, font, text_width) if raw_line else [""])
        line_h = font.metrics("linespace") * 1.3
        block_height = pad_y * 2 + line_h * len(lines)

        self.create_rectangle(left, y, left + border_w, y + block_height, fill=ACCENT, outline="")
        ty = y + pad_y
        for line in lines:
            self.create_text(left + border_w + pad_x, ty, text=line, font=font,
                              fill=QUOTE_INK, anchor="nw")
            ty += line_h
        return y + block_height + 14

    def _draw_table(self, block, left, width, y):
        headers = [h.strip() for h in block.headers]
        rows = [[c.strip() for c in row] for row in block.rows]
        ncols = max(len(headers), max((len(r) for r in rows), default=0), 1)
        col_w = width / ncols
        pad_x, pad_y = 10, 5
        font = self.fonts.table
        font_bold = self.fonts.table_bold
        row_h = font.metrics("linespace") + pad_y * 2

        def draw_row(cells, y0, bg, bold):
            self.create_rectangle(left, y0, left + width, y0 + row_h, fill=bg, outline=RULE)
            for c in range(ncols):
                cx = left + c * col_w
                self.create_rectangle(cx, y0, cx + col_w, y0 + row_h, fill=bg, outline=RULE)
                text = cells[c] if c < len(cells) else ""
                self.create_text(cx + pad_x, y0 + row_h / 2, text=text,
                                  font=font_bold if bold else font, fill=PAPER_INK, anchor="w")

        cy = y
        if headers:
            draw_row(headers, cy, TABLE_HEAD_BG, True)
            cy += row_h
        for i, row in enumerate(rows):
            bg = TABLE_ALT_BG if i % 2 == 1 else PAPER_BG
            draw_row(row, cy, bg, False)
            cy += row_h

        return cy + 14

    def _draw_label_tab(self, x, y, name):
        font = self.fonts.mono_label
        text = name.upper()
        # Approximate the CSS's rotated tab as a small flag at the right edge.
        pad_x, pad_y = 6, 2
        text_w = font.measure(text)
        text_h = font.metrics("linespace")
        box_w = text_h + pad_y * 2
        box_h = text_w + pad_x * 2
        bx0, by0 = x + 4, y - box_h / 2
        bx1, by1 = bx0 + box_w, by0 + box_h
        self.create_rectangle(bx0, by0, bx1, by1, fill=ACCENT, outline="")
        self.create_text((bx0 + bx1) / 2, (by0 + by1) / 2, text=text, font=font,
                          fill="#1b1b1a", angle=90, anchor="center")
