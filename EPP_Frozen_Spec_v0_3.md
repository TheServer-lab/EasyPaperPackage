# EPP — Easy Paper Package
## Frozen Specification v0.3

EPP is a lightweight, UTF-8 text document format for simple multi-page documents. It is designed to be easy to read, easy to parse, and easy to preserve.

---

## 1. Goals

EPP is intended for:

- simple documents
- multi-page text layout
- long-term preservation
- human-readable source files
- small and straightforward parsers

EPP is **not** intended to replace Markdown, DOCX, HTML, or PDF.

---

## 2. Version History

| Version | Status | Summary |
|---------|--------|---------|
| v0.1 | Frozen | Core format: pages, text, headings, bullets, code, labels, basic attributes |
| v0.2 | Frozen | Metadata, page chrome, tables, quotes, lines, italic/underline, bullet styles |
| v0.3 | Frozen | Callout boxes, text highlighting, lined pages, coloured pages, page rotation |

This document specifies v0.3. A v0.3 parser must also accept all v0.1 and v0.2 syntax.

---

## 3. File Rules

- EPP files are plain UTF-8 text.
- Binary data is not embedded in the file.
- Rendering is the job of an EPP renderer, not the file format itself.
- The format is line-oriented and command-based.
- The conventional file extension is `.epp`.

---

## 4. Version Header

Every EPP file should begin with a version header:

```epp
%epp=0.3%
```

This identifies the document as EPP v0.3. The header is optional but strongly recommended. A renderer encountering an unknown version number should attempt to parse the file anyway.

---

## 5. Comments

A semicolon starts a comment. Everything from `;` to the end of the line is ignored by the renderer.

```epp
; This entire line is a comment
@text "Hello world" ; This part is also ignored
```

---

## 6. General Syntax

Most EPP commands follow this pattern:

```epp
@command "text" {attributes}
```

The `@` prefix identifies a command. The text argument is always in double quotes. The attribute block in `{ }` is optional.

Some commands take no text argument (`@space`, `@line`, `@newpage`). Some take a bare word instead of a quoted string (`@page 1`, `@label mymark`).

### 6.1 Strings

Text values are written in double quotes:

```epp
@text "Hello World"
```

### 6.2 Escape sequences

Inside quoted text:

| Sequence | Produces |
|----------|----------|
| `\"` | A literal double-quote character |
| `\\` | A literal backslash |
| `\[` | A literal `[` |
| `\]` | A literal `]` |
| `[newline]` | A line break inside the rendered text |

### 6.3 Attribute blocks

Attributes are a comma-separated list inside `{ }`. Key-value pairs use `=`. Boolean flags are bare words:

```epp
{bold, italic, align=center, color=blue, type=check}
```

Attribute names and values are case-insensitive.

---

## 7. Complete Command Reference

### 7.1 `@page`

Declares the current page number and optional page-level presentation attributes.

```epp
@page 1
@page 2 {color=blue}
@page 3 {lined}
@page 4 {rotate=90}
@page 5 {lined, color=yellow}
```

The page number is a bare word (not quoted). Page-level attributes are described in section 9.

### 7.2 `@newpage`

Ends the current page and starts a new one.

```epp
@newpage
```

### 7.3 `@title`

Sets the document title. Used by renderers for window titles, PDF metadata, and similar.

```epp
@title "My Document"
```

### 7.4 `@meta`

Declares a document-level metadata key-value pair. *(Added in v0.2)*

```epp
@meta title="Project Report"
@meta author="SD"
@meta version="0.3"
```

The value is an unquoted or quoted string directly following `key=`. Renderers may use metadata for PDF export, file indexing, or display purposes.

### 7.5 `@header`

Text printed in a ruled band at the top of every page. *(Added in v0.2)*

```epp
@header "My Document"
```

### 7.6 `@footer`

Text printed in a ruled band at the bottom of every page. *(Added in v0.2)*

The token `[page]` inside the footer text is replaced by the current page number at render time.

```epp
@footer "Page [page]"
```

### 7.7 `@heading`

A section heading.

```epp
@heading "Introduction"
@heading "Summary" {bold, align=center}
```

Supports: `bold`, `italic`, `underline`, `align=`, `color=`, `highlight=`.

### 7.8 `@text`

A paragraph of body text.

```epp
@text "This is a paragraph."
@text "This one is highlighted." {highlight=yellow}
```

Supports: `bold`, `italic`, `underline`, `align=`, `color=`, `highlight=`.

### 7.9 `@bullet`

A list item. Consecutive `@bullet` commands form a list. The list closes when any non-bullet block appears.

```epp
@bullet "First item"
@bullet "Numbered item" {type=number}
@bullet "Check item"    {type=check}
```

Supports: `type=`, `color=`. See section 8.3 for bullet types.

### 7.10 `@code`

A monospace code block. Use `[newline]` for line breaks within the block.

```epp
@code "print('Hello World')"
@code "line one[newline]line two[newline]line three"
```

### 7.11 `@quote`

A blockquote — rendered with emphasis to distinguish it from body text. *(Added in v0.2)*

```epp
@quote "Simple formats survive longer than complicated ones."
```

### 7.12 `@callout`

A coloured callout box for notices, warnings, and annotations. *(Added in v0.3)*

```epp
@callout "Remember to save your work." {color=yellow}
@callout "All data will be permanently deleted." {color=red}
@callout "Build passed — ready to deploy." {color=green}
@callout "This step requires an API key." {color=blue}
```

Requires the `color=` attribute. See section 8.4 for callout colours. If no colour is specified, renderers should default to `yellow`.

The callout label (e.g. "Note", "Warning", "Danger") is generated automatically by the renderer from the colour value — it is not written by the author.

### 7.13 `@line`

A horizontal rule divider. *(Added in v0.2)*

```epp
@line
```

### 7.14 `@space`

Inserts a vertical gap between blocks.

```epp
@space
```

### 7.15 `@label`

Defines a named bookmark in the document. Labels are invisible in print output but used for viewer navigation and document references.

```epp
@label intro_end
```

### 7.16 `@table` and `@row`

Declares a simple table. *(Added in v0.2)*

`@table` takes a pipe-separated list of column headers. Each subsequent `@row` adds a data row. A `@row` attaches to the most recent `@table` on the same page.

```epp
@table "Name|Role|Age"
@row "Alice|Developer|25"
@row "Bob|Designer|30"
```

---

## 8. Attributes

### 8.1 Text and heading attributes

| Attribute | Values | Commands | Notes |
|-----------|--------|----------|-------|
| `bold` | flag | `@heading`, `@text` | Bold weight |
| `italic` | flag | `@heading`, `@text` | Italic style |
| `underline` | flag | `@heading`, `@text` | Underline decoration |
| `align` | `left` `center` `right` | `@heading`, `@text` | Horizontal alignment. Default: `left` |
| `color` | see 8.2 | `@heading`, `@text`, `@bullet` | Text colour hint |
| `highlight` | see 8.5 | `@heading`, `@text` | Background highlight tint *(v0.3)* |

### 8.2 Colour values (`color=`)

| Value | Approximate colour |
|-------|--------------------|
| `black` | Near-black ink |
| `red` | Muted red |
| `blue` | Mid blue |
| `green` | Mid green |
| `gray` / `grey` | Medium gray |
| `amber` / `orange` | Warm amber |
| `purple` | Muted purple |
| `white` | Paper white |

Colour values are renderer hints. Renderers should choose paper-appropriate tones rather than saturated screen colours.

### 8.3 Bullet types (`type=`)

| Value | Glyph | Notes |
|-------|-------|-------|
| `disc` | • | Default |
| `number` | 1. 2. 3. … | Auto-increments within consecutive numbered bullets; resets on any non-bullet block |
| `check` | ✓ | |
| `arrow` | → | |
| `star` | ★ | |

### 8.4 Callout colours (`color=` on `@callout`)

| Value | Suggested use | Auto label |
|-------|---------------|------------|
| `yellow` | General notes, reminders | Note |
| `green` | Success, completed steps | Success |
| `blue` | Informational, references | Info |
| `red` | Danger, destructive actions | Danger |
| `gray` | Neutral side notes | Note |
| `purple` | Tips, hints, extra detail | Note |

### 8.5 Highlight colours (`highlight=` on `@text`, `@heading`)

The entire text block is rendered with a background tint. *(Added in v0.3)*

| Value | Colour |
|-------|--------|
| `yellow` | Warm yellow |
| `green` | Soft green |
| `blue` | Light blue |
| `pink` | Soft pink |
| `red` | Light red |
| `orange` | Light orange |

### 8.6 Page-level attributes (on `@page`)

Page-level attributes apply to the entire page. They are specified in an attribute block after the page number. *(Added in v0.3)*

| Attribute | Values | Effect |
|-----------|--------|--------|
| `color` | `cream` `blue` `pink` `green` `yellow` `gray` | Sets the page background to a paper-toned tint. Default: `cream` |
| `lined` | flag | Renders horizontal rules across the page at line-height intervals, with a left margin rule, resembling notebook paper |
| `rotate` | `90` `180` `270` | Rotates the text content inside the page. The page itself remains portrait. `90` = clockwise, `180` = upside down, `270` = counter-clockwise |

`color` and `lined` may be combined:

```epp
@page 5 {lined, color=yellow}
```

---

## 9. The `[page]` Token

The token `[page]` is recognised exclusively inside `@footer` text. It is replaced by the current page's number at render time.

```epp
@footer "Page [page] of my document"
```

`[page]` inside any other command is treated as literal text.

---

## 10. Rendering Intent

A renderer may display EPP documents in any suitable way, including:

- a page preview window
- a terminal viewer
- printed output on A4 paper
- exported PDF or HTML

The file format itself stays plain text. Renderers are encouraged to:

- treat colour and style attributes as hints, not hard requirements
- produce clean A4-sized output when printing
- preserve the reading order of blocks exactly as written
- handle unknown commands gracefully by ignoring them

---

## 11. Compatibility

v0.3 is a strict superset of v0.2 and v0.1.

- Every valid v0.1 document is a valid v0.3 document.
- Every valid v0.2 document is a valid v0.3 document.
- A v0.3 parser encountering a v0.1 or v0.2 version header should parse it normally.
- A v0.1 or v0.2 parser encountering a v0.3 file should ignore unknown commands and attributes gracefully.

---

## 12. Complete Example Document

```epp
%epp=0.3%
; Full v0.3 example document

@meta title="Project Report"
@meta author="SD"
@meta version="0.3"

@header "Project Report"
@footer "Page [page]"

@page 1
@title "Project Report"
@heading "Introduction" {bold, align=center}
@text "This document demonstrates all EPP v0.3 features."
@space
@quote "Simple formats survive longer than complicated ones."
@line
@callout "Sprint 12 is now complete." {color=green}
@callout "Backup before running the migration script." {color=yellow}
@space
@heading "Steps Completed"
@bullet "Research phase"   {type=check}
@bullet "Design review"    {type=check}
@bullet "Implementation"   {type=arrow}

@newpage

@page 2 {color=blue}
@heading "Highlighted Notes" {bold}
@text "All targets were met ahead of schedule." {highlight=green}
@text "The API key section needs review."        {highlight=yellow}
@space
@heading "Team"
@table "Name|Role|Status"
@row "Alice|Lead|Active"
@row "Bob|Design|Active"
@space
@code "$ make build[newline]$ make test[newline]All tests passed."

@newpage

@page 3 {lined}
@heading "Meeting Notes" {bold}
@text "Discussed roadmap for v0.4."
@text "Agreed on release schedule."
@text "Action items assigned to Alice and Bob."
@label notes_end

@newpage

@page 4 {rotate=90}
@heading "Wide Table (rotated)" {bold}
@table "Command|Added|Text|Attrs|Notes"
@row "@callout|v0.3|yes|color=|Coloured notice box"
@row "@text highlight|v0.3|yes|highlight=|Background tint on text"
@row "@page lined|v0.3|no|lined|Notebook ruling on page"
@row "@page color|v0.3|no|color=|Paper background tint"
@row "@page rotate|v0.3|no|rotate=|Rotate text content"
```

---

## 13. Frozen Scope

This v0.3 specification is now frozen.

**Carried forward from v0.1:**
version header, comments, `@page`, `@newpage`, `@title`, `@heading`, `@text`, `@space`, `@label`, `@bullet`, `@code`, `color=`, `bold`, `align=`

**Added in v0.2:**
`@meta`, `@header`, `@footer`, `@quote`, `@line`, `@table`, `@row`, `italic`, `underline`, `type=` on bullets, `[page]` footer token

**Added in v0.3:**
`@callout` with `color=`, `highlight=` attribute on `@text` and `@heading`, `@page {lined}`, `@page {color=}`, `@page {rotate=}`

Anything else is outside frozen v0.3 and belongs in a future version.
