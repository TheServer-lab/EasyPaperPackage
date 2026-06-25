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

import math
import tkinter as tk
import tkinter.font as tkfont

from epp_parser import (
    COLOR_MAP, BULLET_GLYPHS, ALIGN_VALUES,
    CALLOUT_COLORS, HIGHLIGHT_COLORS, PAGE_COLORS, PAGE_ROTATE_VALUES,
)

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
LINE_RULE_SPACING = 26  # matches the 26px repeating-linear-gradient in epp-style.css
LINE_RULE_COLOR = "#b9af98"  # rgba(185,175,152,.4) over cream, approximated as a flat tint


class MeasuringContext:
    """A drawing-context shim that accepts the same create_text/
    create_rectangle/create_polygon/create_line calls as tk.Canvas but
    draws nothing -- used as a dry-run pass to measure how tall a body
    actually lays out to, before committing to real (rotated) drawing
    with the correct pivot. Keeping this a real no-op object (rather
    than e.g. monkeypatching) means _draw_body needs no awareness that
    it's being measured instead of drawn.
    """

    def create_text(self, *a, **k):
        return None

    def create_line(self, *a, **k):
        return None

    def create_rectangle(self, *a, **k):
        return None

    def create_polygon(self, *a, **k):
        return None

    def configure(self, *a, **k):
        pass

    def delete(self, *a, **k):
        pass


class RotatedDrawing:
    """A drawing-context shim with the same create_text/create_rectangle/
    create_polygon/create_line surface as tk.Canvas, but rotates every
    coordinate it's given around a pivot point before forwarding to the
    real canvas, and adds `angle` to any text's own rotation.

    This lets the existing _draw_body()/_draw_paragraph()/etc methods
    stay completely unaware of rotation: PageCanvas.draw_page() decides
    whether to hand them the real canvas (no rotation) or one of these
    (v0.3 @page {rotate=...}) without changing a single drawing call.

    For 90/270, the caller re-flows the body against a *swapped* wrap
    width (see _draw_rotated_body), which means the incoming coordinates
    already live in a "local" frame whose origin isn't the real page's
    origin. `recenter_from`/`recenter_to` let the caller say "treat this
    local point as the rotation pivot, and place that pivot at this real
    point after rotation" -- i.e. rotate-in-place around a point that
    isn't the real page center, then shift the whole result onto the
    real page center. For the plain 180 case both points are just the
    same real center and this degenerates to the original simple rotation.
    """

    def __init__(self, canvas, angle_deg, pivot_x, pivot_y,
                 recenter_to_x=None, recenter_to_y=None):
        self._canvas = canvas
        self._angle = angle_deg % 360
        self._rad = math.radians(self._angle)
        self._cos = math.cos(self._rad)
        self._sin = math.sin(self._rad)
        self._px = pivot_x
        self._py = pivot_y
        # Where the pivot should land after rotation. Defaults to the
        # pivot itself (rotate in place -- the original 180 behaviour).
        self._tx = pivot_x if recenter_to_x is None else recenter_to_x
        self._ty = pivot_y if recenter_to_y is None else recenter_to_y

    def _rot(self, x, y):
        dx, dy = x - self._px, y - self._py
        # Canvas y grows downward, so a "clockwise" rotation visually
        # corresponds to this standard 2D rotation matrix as-is.
        rx = dx * self._cos - dy * self._sin
        ry = dx * self._sin + dy * self._cos
        return self._tx + rx, self._ty + ry

    def create_text(self, x, y, **kwargs):
        rx, ry = self._rot(x, y)
        base_angle = kwargs.pop("angle", 0)
        # tk's text angle is counter-clockwise in degrees; our _angle is
        # the clockwise visual rotation we want, so subtract.
        kwargs["angle"] = (base_angle - self._angle) % 360
        return self._canvas.create_text(rx, ry, **kwargs)

    def create_line(self, *coords, **kwargs):
        pts = self._rot_coords(coords)
        return self._canvas.create_line(*pts, **kwargs)

    def create_rectangle(self, x0, y0, x1, y1, **kwargs):
        # A rotated rectangle is a polygon, not a rectangle, in the
        # general case -- always emit a polygon so corners land right.
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = []
        for cx, cy in corners:
            rx, ry = self._rot(cx, cy)
            pts.extend([rx, ry])
        return self._canvas.create_polygon(*pts, **kwargs)

    def create_polygon(self, *coords, **kwargs):
        pts = self._rot_coords(coords)
        return self._canvas.create_polygon(*pts, **kwargs)

    def _rot_coords(self, coords):
        if len(coords) == 1 and isinstance(coords[0], (list, tuple)):
            coords = coords[0]
        out = []
        for i in range(0, len(coords) - 1, 2):
            rx, ry = self._rot(coords[i], coords[i + 1])
            out.extend([rx, ry])
        return out

    def configure(self, *a, **k):
        pass  # no-op: only the outer PageCanvas should resize itself

    def delete(self, *a, **k):
        pass


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
        self.callout_label = tkfont.Font(root=root, family=mono, size=8, weight="bold")

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
        page_attrs = getattr(page, "page_attrs", {}) or {}

        # v0.3: resolve page background/ink color (defaults to cream/paper-ink)
        color_key = page_attrs.get("color")
        palette = PAGE_COLORS.get(color_key, {"bg": PAPER_BG, "ink": PAPER_INK})
        page_bg, page_ink = palette["bg"], palette["ink"]
        self.configure(bg=page_bg)

        # header band (chrome, not "page content" -- never rotated, always paper-ink toned)
        if header:
            y = self._draw_band(self, y, width, header, top_border=False, bottom_border=True)

        body_top = y + BODY_TOP_PADDING

        rotate_raw = str(page_attrs.get("rotate")) if page_attrs.get("rotate") else None
        rotate_deg = int(rotate_raw) if rotate_raw in PAGE_ROTATE_VALUES else 0

        if rotate_deg:
            body_height = self._draw_rotated_body(page, body_top, width, page_ink, rotate_deg)
        else:
            body_height = self._draw_body(self, page, body_top, width, page_ink)

        body_bottom = max(body_top + body_height, y + MIN_BODY_HEIGHT) + BODY_BOTTOM_PADDING
        y = body_bottom

        # footer band
        if footer:
            footer_text = footer.replace("[page]", str(page_number))
            y = self._draw_band(self, y, width, footer_text, top_border=True, bottom_border=False)
        else:
            y = self._draw_fallback_footer(y, width, page_number)

        # v0.3: lined-paper ruling, drawn last then sent behind everything,
        # bounded to the body's actual final extent (header-band bottom to
        # footer-band top) now that both are known.
        if page_attrs.get("lined"):
            self._draw_lined_background(body_top, body_bottom, width, page_ink)

        self.configure(width=width, height=int(y) + 1, scrollregion=(0, 0, width, int(y) + 1))
        return int(y) + 1

    def _draw_lined_background(self, body_top, body_bottom, width, ink):
        """v0.3 @page {lined}: horizontal notebook-style rules at fixed
        intervals across the body area, plus a left margin rule,
        approximating the CSS repeating-linear-gradient + ::before
        margin line. Bounded to the page's actual final body extent and
        sent behind all other content."""
        ry = body_top
        while ry <= body_bottom:
            self.create_line(0, ry, PAGE_WIDTH, ry, fill=LINE_RULE_COLOR, tags="lined-rule")
            ry += LINE_RULE_SPACING
        margin_x = SIDE_PADDING + 12
        self.create_line(margin_x, body_top, margin_x, body_bottom,
                          fill="#dc7864", tags="lined-rule")
        self.tag_lower("lined-rule")

    def _draw_rotated_body(self, page, body_top, page_width, page_ink, rotate_deg):
        """v0.3 @page {rotate=90|180|270}.

        The reference CSS implements this two different ways depending
        on the angle, and the distinction matters for correctness, not
        just visuals:

        - 180: a plain `transform:rotate(180deg)` on the already-laid-out
          body -- text still wraps against the page's normal width, the
          whole block is just flipped upside down. Simple coordinate
          rotation of the existing layout reproduces this exactly.

        - 90 / 270: `writing-mode:vertical-rl`/`vertical-lr` -- the
          browser's text layout engine re-flows content from scratch
          with the *page's height* as the wrapping width (since the
          reading direction is now vertical). Rotating the coordinates
          of a layout that was wrapped against the page's *width* would
          clip text against the wrong boundary, which is exactly the bug
          a naive "rotate the same layout" approach produces. So for
          these two angles we re-flow against a wrap width equal to the
          provisional body height, then rotate the result 90/270 around
          its own center -- but that center must be based on how tall
          the content *actually* turned out (a long page vs a short one
          produce very different local heights), not a fixed guess, or
          short content ends up off-center and long content overflows
          the page edge. So this runs a no-op measuring pass first to
          find the real local height, then draws for real using that.
        """
        provisional_height = MIN_BODY_HEIGHT
        center_x = PAGE_WIDTH / 2
        center_y = body_top + provisional_height / 2

        if rotate_deg == 180:
            ctx = RotatedDrawing(self, 180, center_x, center_y)
            return self._draw_body(ctx, page, body_top, page_width, page_ink)

        # 90 or 270: measure first (no drawing), against a wrap width
        # equal to the provisional body height -- the same allowance the
        # unrotated path uses as its minimum.
        wrap_width = provisional_height
        measured_height = self._draw_body(MeasuringContext(), page, body_top, wrap_width, page_ink)

        # Now draw for real. The local rectangle that _draw_body will
        # actually fill is x in [SIDE_PADDING, SIDE_PADDING+wrap_width],
        # y in [body_top, body_top+measured_height] -- rotate around
        # *that* rectangle's true center, then recenter onto the real
        # page's body center, so short content lands centered and long
        # content is measured (not guessed) before it's placed.
        local_pivot_x = SIDE_PADDING + wrap_width / 2
        local_pivot_y = body_top + measured_height / 2
        ctx = RotatedDrawing(self, rotate_deg, local_pivot_x, local_pivot_y,
                              recenter_to_x=center_x, recenter_to_y=center_y)
        self._draw_body(ctx, page, body_top, wrap_width, page_ink)

        # The real vertical space this rotated body consumes on the
        # actual page corresponds to its local *width* usage (wrap_width
        # itself, since text fills across the full wrap width in the
        # common case) -- but to stay safely within the same allowance
        # the unrotated path guarantees, report the fixed provisional
        # height rather than trying to derive a tighter bound from
        # measured_height (which is a local-frame *height*, i.e. the
        # rotated result's real-page *width* usage, not its real-page
        # height usage).
        return provisional_height

    # ---- bands ----

    def _draw_band(self, ctx, y, width, text, top_border, bottom_border):
        pad_v = 8
        lines = inline_text_lines(text)
        line_h = self.fonts.mono_band.metrics("linespace")
        height = pad_v * 2 + line_h * len(lines)
        if top_border:
            ctx.create_line(0, y, width, y, fill=RULE)
        cy = y + pad_v
        for line in lines:
            ctx.create_text(width / 2, cy, text=line, font=self.fonts.mono_band,
                             fill=RULE, anchor="n", justify="center")
            cy += line_h
        y2 = y + height
        if bottom_border:
            ctx.create_line(0, y2, width, y2, fill=RULE)
        return y2

    def _draw_fallback_footer(self, y, width, page_number):
        pad_top, pad_bottom = 6, 10
        line_h = self.fonts.footer_fallback.metrics("linespace")
        cy = y + pad_top
        self.create_text(width / 2, cy, text=str(page_number), font=self.fonts.footer_fallback,
                          fill=FOOTER_FALLBACK_INK, anchor="n", justify="center")
        return y + pad_top + line_h + pad_bottom

    # ---- body ----

    def _draw_body(self, ctx, page, top, page_width, page_ink=None):
        page_ink = page_ink or PAPER_INK
        content_left = SIDE_PADDING
        content_right = page_width - SIDE_PADDING
        content_width = content_right - content_left
        y = top
        list_counter = 0
        total = len(page.blocks)
        label_positions = []  # (idx, name) to place after we know body height

        for idx, block in enumerate(page.blocks):
            if block.type != "bullet":
                list_counter = 0

            if block.type == "heading":
                y = self._draw_paragraph(ctx, block, content_left, content_width, y,
                                          font_plain=self.fonts.heading,
                                          font_italic=self.fonts.heading_italic,
                                          bottom_margin=14, page_ink=page_ink)
            elif block.type == "text":
                y = self._draw_paragraph(ctx, block, content_left, content_width, y,
                                          font_plain=self.fonts.body,
                                          font_italic=self.fonts.body_italic,
                                          bottom_margin=12, page_ink=page_ink)
            elif block.type == "bullet":
                list_counter += 1
                y = self._draw_bullet(ctx, block, content_left, content_width, y, list_counter, page_ink)
            elif block.type == "code":
                y = self._draw_code(ctx, block, content_left, content_width, y)
            elif block.type == "callout":
                y = self._draw_callout(ctx, block, content_left, content_width, y)
            elif block.type == "space":
                y += 18
            elif block.type == "line":
                y += 5
                ctx.create_line(content_left, y, content_right, y, fill=RULE)
                y += 11
            elif block.type == "quote":
                y = self._draw_quote(ctx, block, content_left, content_width, y)
            elif block.type == "table":
                y = self._draw_table(ctx, block, content_left, content_width, y)
            elif block.type == "label":
                label_positions.append((idx, block.name))

        if total == 0:
            font = self.fonts.body_italic
            ctx.create_text(content_left, y, text="This page is empty.", font=font,
                             fill=EMPTY_HINT, anchor="nw")
            y += font.metrics("linespace")

        body_height = y - top

        # Label tabs are page-edge navigation chrome (like header/footer),
        # not rotated content -- always placed via the real canvas, and
        # always anchored to the real page width (not `page_width`,
        # which is the swapped wrap-width for 90/270 rotated bodies).
        # Skipped entirely during a measuring pass (MeasuringContext),
        # since that pass exists only to compute body_height and should
        # have zero side effects on the real canvas -- otherwise a
        # rotated page's dry-run would draw a real, stray tab that the
        # second (real) pass then draws again on top of.
        if not isinstance(ctx, MeasuringContext):
            for idx, name in label_positions:
                frac = 0.5 if total <= 1 else (idx / (total - 1))
                tab_y = top + frac * max(body_height, 1)
                self._draw_label_tab(PAGE_WIDTH - SIDE_PADDING, tab_y, name)

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

    def _draw_paragraph(self, ctx, block, left, width, y, font_plain, font_italic,
                         bottom_margin, page_ink=None):
        attrs = block.attrs or {}
        color = block_color(attrs) or (page_ink or PAPER_INK)
        align = block_align(attrs)
        bold = bool(attrs.get("bold"))
        italic = bool(attrs.get("italic"))
        underline = bool(attrs.get("underline"))
        highlight_key = attrs.get("highlight")
        highlight_bg = HIGHLIGHT_COLORS.get(highlight_key)

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
                line_h = draw_font.metrics("linespace") * 1.3
                if highlight_bg:
                    # v0.3 highlight=: a background tint behind the text,
                    # approximating the <mark> the web renderer uses.
                    text_w = draw_font.measure(line)
                    pad = 2
                    ctx.create_rectangle(x - pad, y, x + text_w + pad, y + line_h * 0.92,
                                          fill=highlight_bg, outline="")
                ctx.create_text(x, y, text=line, font=draw_font, fill=color, anchor="nw")
                y += line_h
        return y + bottom_margin

    def _x_for_align(self, left, width, align, text_w):
        if align == "center":
            return left + max(0, (width - text_w) / 2)
        if align == "right":
            return left + max(0, width - text_w)
        return left

    def _draw_bullet(self, ctx, block, left, width, y, counter, page_ink=None):
        attrs = block.attrs or {}
        color = block_color(attrs) or ACCENT
        text_color = block_color(attrs) or (page_ink or PAPER_INK)
        btype = attrs.get("type", "disc")
        glyph_w = 24
        gap = 8

        if btype == "number":
            glyph = f"{counter}."
        else:
            glyph = BULLET_GLYPHS.get(btype) or "\u2022"

        ctx.create_text(left + glyph_w, y, text=glyph, font=self.fonts.mono_glyph,
                         fill=color, anchor="ne")

        text_left = left + glyph_w + gap
        text_width = width - glyph_w - gap
        font = self.fonts.body
        cy = y
        for raw_line in inline_text_lines(block.text):
            wrapped = self._wrap_text(raw_line, font, text_width) if raw_line else [""]
            for line in wrapped:
                ctx.create_text(text_left, cy, text=line, font=font, fill=text_color, anchor="nw")
                cy += font.metrics("linespace") * 1.3
        return cy + 4  # margin-bottom: 4px between bullets, like CSS

    def _draw_code(self, ctx, block, left, width, y):
        pad_x, pad_y = 12, 10
        border_w = 3
        font = self.fonts.mono_code
        raw_lines = []
        for chunk in block.text.split("[newline]"):
            raw_lines.extend(chunk.split("\n"))
        line_h = font.metrics("linespace")
        block_height = pad_y * 2 + line_h * max(1, len(raw_lines))

        ctx.create_rectangle(left, y, left + width, y + block_height, fill=CODE_BG, outline="")
        ctx.create_rectangle(left, y, left + border_w, y + block_height, fill=ACCENT, outline="")

        ty = y + pad_y
        for line in raw_lines:
            ctx.create_text(left + border_w + pad_x, ty, text=line, font=font,
                             fill=PAPER_INK, anchor="nw")
            ty += line_h
        return y + block_height + 12

    def _draw_quote(self, ctx, block, left, width, y):
        pad_x, pad_y = 16, 8
        border_w = 3
        font = self.fonts.body_italic
        text_width = width - pad_x - border_w
        lines = []
        for raw_line in inline_text_lines(block.text):
            lines.extend(self._wrap_text(raw_line, font, text_width) if raw_line else [""])
        line_h = font.metrics("linespace") * 1.3
        block_height = pad_y * 2 + line_h * len(lines)

        ctx.create_rectangle(left, y, left + border_w, y + block_height, fill=ACCENT, outline="")
        ty = y + pad_y
        for line in lines:
            ctx.create_text(left + border_w + pad_x, ty, text=line, font=font,
                             fill=QUOTE_INK, anchor="nw")
            ty += line_h
        return y + block_height + 14

    def _draw_callout(self, ctx, block, left, width, y):
        """v0.3 @callout: a coloured notice box with an auto-generated
        label (e.g. "Note", "Danger") looked up from CALLOUT_COLORS,
        matching the web renderer's behavior exactly -- the label is
        never author-supplied."""
        attrs = block.attrs or {}
        color_key = attrs.get("color") or "yellow"
        palette = CALLOUT_COLORS.get(color_key, CALLOUT_COLORS["yellow"])
        bg, border, text_color, label = (
            palette["bg"], palette["border"], palette["text"], palette["label"],
        )

        pad_x, pad_y = 13, 9
        border_w = 3
        label_font = self.fonts.callout_label
        body_font = self.fonts.body
        text_width = width - pad_x * 2 - border_w

        label_h = label_font.metrics("linespace")
        lines = []
        for raw_line in inline_text_lines(block.text):
            lines.extend(self._wrap_text(raw_line, body_font, text_width) if raw_line else [""])
        body_line_h = body_font.metrics("linespace") * 1.25
        block_height = pad_y * 2 + label_h + 3 + body_line_h * len(lines)

        ctx.create_rectangle(left, y, left + width, y + block_height, fill=bg, outline="")
        ctx.create_rectangle(left, y, left + border_w, y + block_height, fill=border, outline="")

        tx = left + border_w + pad_x
        ty = y + pad_y
        ctx.create_text(tx, ty, text=label.upper(), font=label_font, fill=border, anchor="nw")
        ty += label_h + 3
        for line in lines:
            ctx.create_text(tx, ty, text=line, font=body_font, fill=text_color, anchor="nw")
            ty += body_line_h

        return y + block_height + 12

    def _draw_table(self, ctx, block, left, width, y):
        headers = [h.strip() for h in block.headers]
        rows = [[c.strip() for c in row] for row in block.rows]
        ncols = max(len(headers), max((len(r) for r in rows), default=0), 1)
        col_w = width / ncols
        pad_x, pad_y = 10, 5
        font = self.fonts.table
        font_bold = self.fonts.table_bold
        row_h = font.metrics("linespace") + pad_y * 2

        def draw_row(cells, y0, bg, bold):
            ctx.create_rectangle(left, y0, left + width, y0 + row_h, fill=bg, outline=RULE)
            for c in range(ncols):
                cx = left + c * col_w
                ctx.create_rectangle(cx, y0, cx + col_w, y0 + row_h, fill=bg, outline=RULE)
                text = cells[c] if c < len(cells) else ""
                ctx.create_text(cx + pad_x, y0 + row_h / 2, text=text,
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
