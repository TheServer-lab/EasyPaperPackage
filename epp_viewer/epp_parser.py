"""
EPP (Easy Paper Package) document parser.

This is a faithful Python port of the parsing grammar implemented in
epp-core.js (the EPP Viewer browser extension), updated for EPP 0.3. It
turns raw .epp source text into a structured document: a list of pages
(each with optional page-level attributes — color/lined/rotate, added in
v0.3) containing an ordered list of "blocks" (heading, text, bullet,
code, quote, callout, table, label, space, line), plus document-level
title/header/footer/meta. v0.1 and v0.2 documents parse unchanged, since
v0.3 is a strict superset.

The renderer (epp_render.py) and PDF exporter (epp_pdf.py) consume this
structure to draw pages.
"""

from dataclasses import dataclass, field
from typing import Optional


COLOR_MAP = {
    "black": "#211c14",
    "red": "#a23b2e",
    "blue": "#2e5c8a",
    "green": "#3c6b3f",
    "gray": "#5b564a",
    "grey": "#5b564a",
    "white": "#faf6ec",
    "amber": "#c98a3e",
    "orange": "#c98a3e",
    "purple": "#5b3a6b",
}

# v0.3: callout background/border/text colours keyed by color=, ported
# verbatim (same hex values) from CALLOUT_COLORS in epp-core.js.
CALLOUT_COLORS = {
    "yellow": {"bg": "#fdf3dc", "border": "#c98a3e", "text": "#6b3e10", "label": "Note"},
    "red":    {"bg": "#fce8e6", "border": "#a23b2e", "text": "#6b1e16", "label": "Danger"},
    "green":  {"bg": "#dff0df", "border": "#3c6b3f", "text": "#1e3d20", "label": "Success"},
    "blue":   {"bg": "#ddeef7", "border": "#2e5c8a", "text": "#1a3d5c", "label": "Info"},
    "gray":   {"bg": "#f0eeea", "border": "#5b564a", "text": "#2e2a24", "label": "Note"},
    "purple": {"bg": "#ede8f7", "border": "#5b3a6b", "text": "#2e1a3d", "label": "Note"},
}

# v0.3: highlight= colour map (paper-friendly tints), ported verbatim from
# HIGHLIGHT_COLORS in epp-core.js.
HIGHLIGHT_COLORS = {
    "yellow": "#fff176",
    "green": "#c8f5c8",
    "blue": "#c2e3fc",
    "pink": "#fcd5e8",
    "red": "#fdd5d3",
    "orange": "#ffe0b2",
}

# v0.3: page background/ink colours keyed by @page's color=, ported
# verbatim from PAGE_COLORS in epp-core.js.
PAGE_COLORS = {
    "cream":  {"bg": "#faf6ec", "ink": "#211c14"},
    "blue":   {"bg": "#edf3fc", "ink": "#1c3358"},
    "pink":   {"bg": "#fce8f0", "ink": "#5a1c33"},
    "green":  {"bg": "#ecf6ec", "ink": "#1c3d1c"},
    "yellow": {"bg": "#fefadf", "ink": "#4a3a00"},
    "gray":   {"bg": "#f0eeea", "ink": "#2e2a24"},
}

PAGE_ROTATE_VALUES = ("90", "180", "270")

ALIGN_VALUES = ("left", "center", "right")
TEXT_TYPES = ("heading", "text", "bullet", "code", "callout")

BULLET_GLYPHS = {
    "disc": "\u2022",
    "number": None,  # handled separately
    "check": "\u2713",
    "arrow": "\u2192",
    "star": "\u2605",
}


@dataclass
class Block:
    type: str
    text: str = ""
    attrs: dict = field(default_factory=dict)
    name: Optional[str] = None          # for 'label'
    headers: list = field(default_factory=list)   # for 'table'
    rows: list = field(default_factory=list)       # for 'table'


@dataclass
class Page:
    number: Optional[str] = None
    blocks: list = field(default_factory=list)
    page_attrs: dict = field(default_factory=dict)  # v0.3: color, lined, rotate


@dataclass
class EPPDocument:
    version: Optional[str] = None
    title: Optional[str] = None
    header: Optional[str] = None
    footer: Optional[str] = None
    meta: dict = field(default_factory=dict)
    pages: list = field(default_factory=list)


class EPPParseError(Exception):
    pass


def parse_epp(source: str) -> EPPDocument:
    """Parse raw .epp source text into an EPPDocument."""
    i = 0
    n = len(source)
    title = None
    version = None
    header = None
    footer = None
    meta = {}
    pages = []
    current = Page(number=None, blocks=[])

    def is_ws(c):
        return c in (" ", "\t", "\n", "\r")

    def skip_ws_and_comments():
        nonlocal i
        while i < n:
            c = source[i]
            if is_ws(c):
                i += 1
                continue
            if c == ";":
                while i < n and source[i] != "\n":
                    i += 1
                continue
            break

    def read_word():
        nonlocal i
        start = i
        while i < n and not is_ws(source[i]) and source[i] not in ("{", ";"):
            i += 1
        return source[start:i]

    def read_quoted_string():
        nonlocal i
        i += 1  # consume opening "
        out = []
        while i < n:
            c = source[i]
            if c == "\\":
                nxt = source[i + 1] if i + 1 < n else ""
                if nxt in ('"', "[", "]", "\\"):
                    out.append(nxt)
                    i += 2
                    continue
                out.append(c)
                i += 1
                continue
            if c == '"':
                i += 1
                break
            if c == "\n":
                out.append(" ")
                i += 1
                continue
            out.append(c)
            i += 1
        return "".join(out)

    def read_attr_block():
        nonlocal i
        i += 1  # consume {
        start = i
        while i < n and source[i] != "}":
            i += 1
        inner = source[start:i]
        if i < n:
            i += 1
        attrs = {}
        for part in inner.split(","):
            p = part.strip()
            if not p:
                continue
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip().lower()
                v = v.strip().lower()
                if k == "aling":
                    k = "align"
                attrs[k] = v
            else:
                attrs[p.lower()] = True
        return attrs

    def read_inline_kv():
        nonlocal i
        skip_ws_and_comments()
        start = i
        while i < n and not is_ws(source[i]) and source[i] != ";":
            i += 1
        token = source[start:i]
        if "=" in token:
            k, _, v = token.partition("=")
            if v.startswith('"') and v.endswith('"') and len(v) >= 2:
                v = v[1:-1]
            return k.strip().lower(), v.strip()
        return token.strip().lower(), ""

    skip_ws_and_comments()
    if i < n and source[i] == "%":
        start = i
        i += 1
        while i < n and source[i] != "%":
            i += 1
        raw = source[start + 1:i]
        if i < n:
            i += 1
        if raw.startswith("epp="):
            version = raw[len("epp="):]
        else:
            version = raw

    while True:
        skip_ws_and_comments()
        if i >= n:
            break
        if source[i] != "@":
            i += 1
            continue
        i += 1
        cmd = read_word().lower()

        if cmd == "newpage":
            pages.append(current)
            current = Page(number=None, blocks=[], page_attrs={})
            continue
        if cmd == "page":
            skip_ws_and_comments()
            current.number = read_word()
            skip_ws_and_comments()
            # v0.3: @page N {lined} {color=blue} {rotate=90}
            if i < n and source[i] == "{":
                current.page_attrs = read_attr_block()
            continue
        if cmd == "title":
            skip_ws_and_comments()
            if i < n and source[i] == '"':
                title = read_quoted_string()
            continue
        if cmd == "label":
            skip_ws_and_comments()
            name = read_word()
            current.blocks.append(Block(type="label", name=name))
            continue
        if cmd == "space":
            current.blocks.append(Block(type="space"))
            continue
        if cmd == "line":
            current.blocks.append(Block(type="line"))
            continue

        if cmd == "meta":
            k, v = read_inline_kv()
            meta[k] = v
            if k == "title" and not title:
                title = v
            continue
        if cmd == "header":
            skip_ws_and_comments()
            if i < n and source[i] == '"':
                header = read_quoted_string()
            continue
        if cmd == "footer":
            skip_ws_and_comments()
            if i < n and source[i] == '"':
                footer = read_quoted_string()
            continue
        if cmd == "quote":
            skip_ws_and_comments()
            text = ""
            if i < n and source[i] == '"':
                text = read_quoted_string()
            current.blocks.append(Block(type="quote", text=text))
            continue
        if cmd == "table":
            skip_ws_and_comments()
            headers = []
            if i < n and source[i] == '"':
                headers = read_quoted_string().split("|")
            current.blocks.append(Block(type="table", headers=headers, rows=[]))
            continue
        if cmd == "row":
            skip_ws_and_comments()
            cells = []
            if i < n and source[i] == '"':
                cells = read_quoted_string().split("|")
            last_table = None
            for b in reversed(current.blocks):
                if b.type == "table":
                    last_table = b
                    break
            if last_table is not None:
                last_table.rows.append(cells)
            continue

        if cmd in TEXT_TYPES:
            skip_ws_and_comments()
            text = ""
            if i < n and source[i] == '"':
                text = read_quoted_string()
            skip_ws_and_comments()
            attrs = {}
            if i < n and source[i] == "{":
                attrs = read_attr_block()
            current.blocks.append(Block(type=cmd, text=text, attrs=attrs))
            continue

        # unknown command - skip rest of line tokens
        skip_ws_and_comments()
        if i < n and source[i] == '"':
            read_quoted_string()
        skip_ws_and_comments()
        if i < n and source[i] == "{":
            read_attr_block()

    pages.append(current)
    return EPPDocument(
        version=version, title=title, header=header, footer=footer,
        meta=meta, pages=pages,
    )


def parse_epp_file(path: str) -> EPPDocument:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    return parse_epp(source)
