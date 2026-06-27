# EPP — Easy Paper Package

> *"Simple formats survive longer than complicated ones."*

**EPP** is a lightweight, UTF-8 text document format for simple multi-page documents designed to be printed on A4 paper. It is human-readable, trivial to parse, and built to last.

```epp
%epp=0.3%
@header "Project Report"
@footer "Page [page]"

@page 1
@heading "Introduction" {bold, align=center}
@text "This document demonstrates EPP v0.3."
@callout "Sprint 12 is now complete." {color=green}
@bullet "Research phase" {type=check}
@bullet "Design review"  {type=check}
@bullet "Implementation" {type=arrow}
```

---

## What is EPP?

EPP (Easy Paper Package) is a plain-text document format with a `.epp` file extension. It uses a simple line-oriented command syntax — every command starts with `@`, takes a quoted string, and accepts an optional attribute block.

It is **not** a replacement for Markdown, HTML, DOCX, or PDF. It fills a narrower need: documents that a human can read as plain text, a simple parser can render, a printer can output on A4, and time cannot corrupt.

---

## Key properties

| Property | Detail |
|---|---|
| **Encoding** | Pure UTF-8 text, always |
| **Binary content** | None — no images, fonts, or embedded data |
| **Dependencies** | Zero — fully offline, no network calls |
| **Print target** | A4 paper |
| **Extension** | `.epp` |
| **Current version** | v0.3 (frozen) |

---

## Syntax

Every EPP command follows one of these patterns:

```epp
@command "text"
@command "text" {attribute, key=value}
@command bare_word
@command
```

A semicolon starts a comment. The version header is optional but recommended:

```epp
%epp=0.3%
; Everything after a semicolon is ignored

@meta title="My Document"
@meta author="SD"
```

---

## Command reference

### Document structure

| Command | Description |
|---|---|
| `@page N` | Start page number N |
| `@page N {lined}` | Lined (notebook-ruled) page |
| `@page N {color=cream}` | Coloured page background |
| `@page N {rotate=90}` | Rotate content 90° clockwise |
| `@newpage` | End current page, start next |
| `@title "..."` | Document title |
| `@meta key="value"` | Metadata key-value pair |
| `@header "..."` | Header band on every page |
| `@footer "Page [page]"` | Footer — `[page]` becomes the page number |
| `@label name` | Navigation bookmark (invisible in print) |

### Content blocks

| Command | Description |
|---|---|
| `@heading "..."` | Section heading |
| `@text "..."` | Body paragraph |
| `@bullet "..."` | List item |
| `@code "..."` | Monospace code block — use `[newline]` for line breaks |
| `@quote "..."` | Block quote |
| `@callout "..." {color=yellow}` | Coloured notice box |
| `@table "Col1\|Col2\|Col3"` | Table with pipe-separated headers |
| `@row "A\|B\|C"` | Table data row |
| `@line` | Horizontal rule |
| `@space` | Vertical gap |

### Text and heading attributes

| Attribute | Values |
|---|---|
| `bold` | flag |
| `italic` | flag |
| `underline` | flag |
| `align=` | `left` `center` `right` |
| `color=` | `black` `red` `blue` `green` `gray` `amber` `purple` `white` |
| `highlight=` | `yellow` `green` `blue` `pink` `red` `orange` |

### Bullet types

| `type=` value | Glyph |
|---|---|
| `disc` | • (default) |
| `number` | 1. 2. 3. … |
| `check` | ✓ |
| `arrow` | → |
| `star` | ★ |

### Callout colours

| `color=` | Auto label | Suggested use |
|---|---|---|
| `yellow` | Note | General reminders |
| `green` | Success | Completed steps |
| `blue` | Info | Reference, informational |
| `red` | Danger | Destructive or critical actions |
| `gray` | Note | Neutral side notes |
| `purple` | Note | Tips and hints |

---

## Complete example

```epp
%epp=0.3%
; Full v0.3 example

@meta title="Project Report"
@meta author="SD"

@header "Project Report"
@footer "Page [page]"

@page 1
@heading "Introduction" {bold, align=center}
@text "This document demonstrates all EPP v0.3 features."
@quote "Simple formats survive longer than complicated ones."
@callout "Sprint 12 is now complete."           {color=green}
@callout "Backup before running the migration." {color=yellow}
@bullet "Research phase"   {type=check}
@bullet "Design review"    {type=check}
@bullet "Implementation"   {type=arrow}

@newpage

@page 2 {color=blue}
@heading "Highlighted Notes" {bold}
@text "All targets were met ahead of schedule." {highlight=green}
@text "The API key section needs review."       {highlight=yellow}
@table "Name|Role|Status"
@row   "Alice|Lead|Active"
@row   "Bob|Design|Active"
@code  "$ make build[newline]$ make test[newline]All tests passed."

@newpage

@page 3 {lined}
@heading "Meeting Notes" {bold}
@text "Discussed roadmap for v0.4."
@text "Action items assigned to Alice and Bob."
@label notes_end

@newpage

@page 4 {rotate=90}
@heading "Wide Table (rotated)" {bold}
@table "Command|Added|Purpose"
@row "@callout|v0.3|Coloured notice box"
@row "@highlight|v0.3|Background tint on text"
@row "@page lined|v0.3|Notebook ruling"
@row "@page color|v0.3|Paper background tint"
```

---

## Version history

All versions are frozen. Each is a strict superset of the last — a v0.1 file is valid v0.3, and a v0.1 parser reading a v0.3 file will gracefully ignore what it doesn't know.

| Version | Status | What was added |
|---|---|---|
| **v0.3** | Frozen — current | `@callout`, `highlight=`, `@page {lined}`, `@page {color=}`, `@page {rotate=}` |
| **v0.2** | Frozen | `@meta`, `@header`, `@footer`, `@quote`, `@line`, `@table`, `@row`, `italic`, `underline`, bullet `type=`, `[page]` token |
| **v0.1** | Frozen — foundation | Core format: pages, text, headings, bullets, code, labels, basic attributes |

---

## Design goals

EPP is intended for:

- Simple documents and reports
- Multi-page text layout
- Long-term archival and preservation
- Human-readable source files
- Small, straightforward parsers

EPP is intentionally **not** designed for: images, embedded assets, scripting, rich inline formatting, or complex layouts. Use the right tool for those jobs.

---

## Writing a parser

A working EPP parser can be written in under 200 lines of most languages. The format is line-oriented: read line by line, strip comments (everything from `;` to end-of-line), match the `@command` prefix, extract the quoted string argument, and parse the optional `{attr, key=value}` block.

Unknown commands and unknown attributes should be silently ignored. This is what allows older parsers to read newer files without breaking.

---

## Why EPP is not open source

EPP is free to use and the specification is fully public. Anyone can write a parser, renderer, or tooling.

The project is not open source for one honest reason: **it costs money to run.** The website at [easypaperpackage.xyz](https://easypaperpackage.xyz) is actively maintained — domain, hosting, and upkeep come out of one person's pocket. Opening the repository would also mean managing issues, pull requests, and community expectations without the resources to do that sustainably. The current model — a published, frozen spec with a single maintainer — keeps EPP stable and the spec honest.

If EPP grows to attract contributors or funding, that changes. Until then, the format is yours to use freely.

---

## Escape sequences

Inside quoted strings:

| Sequence | Produces |
|---|---|
| `\"` | Literal double-quote |
| `\\` | Literal backslash |
| `\[` | Literal `[` |
| `\]` | Literal `]` |
| `[newline]` | Line break inside rendered text |

The `[page]` token is only recognised inside `@footer` text. Everywhere else it is treated as literal text.

---

## Rendering intent

A renderer may display EPP documents as a page preview, terminal viewer, printed A4 output, or exported PDF/HTML. The format makes no assumptions about the renderer. Renderers are encouraged to:

- Treat colour and style attributes as hints, not hard requirements
- Produce clean A4 output when printing
- Preserve block reading order exactly as written
- Handle unknown commands and attributes by ignoring them

---

## Links

- **Website:** [easypaperpackage.xyz](https://easypaperpackage.xyz)
- **Specification:** [easypaperpackage.xyz](https://easypaperpackage.xyz)
