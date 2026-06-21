# EPP Format Specification

**Version:** 0.2
**Status:** Stable (reverse-engineered from the reference implementation, `epp-core.js`)
**File extension:** `.epp`
**Encoding:** UTF-8

## 1. Overview

EPP ("Easy Paper Package") is a plain-text document format for describing
simple, printable, paginated documents — a lightweight alternative to PDF
or Word for content that's mostly headings, paragraphs, lists, tables, and
quotes.

An EPP file is a flat sequence of **commands**. Each command begins with
`@` and optionally takes a quoted text argument and/or a brace-delimited
attribute block. There is no nesting: every command either contributes a
block to the current page or sets document-level metadata.

```
@text "This is a paragraph." {color=blue}
```

There is no DOCTYPE, no closing tags, and no schema validation step in the
reference implementation — see §7 for the practical consequences of this.

## 2. Lexical structure

### 2.1 Whitespace and comments

Space, tab, `\n`, and `\r` are all whitespace and are insignificant
between tokens. A semicolon (`;`) starts a comment that runs to the end
of the line:

```
; this is a comment
@text "hello" ; NOTE: this is not treated as a trailing comment in all
              ; parser states — see §7.1. Put comments on their own line.
```

### 2.2 Tokens

A bare word (used for command names, page labels, and label names) is any
run of characters that contains no whitespace, `{`, or `;`.

### 2.3 Quoted strings

A quoted string is delimited by `"`. Inside a quoted string:

| Sequence | Meaning |
|---|---|
| `\"` | literal `"` |
| `\\` | literal `\` |
| `\[` | literal `[` |
| `\]` | literal `]` |
| a raw newline (pressing Enter inside the string) | collapsed to a single space |
| any other character | itself, literally |

There is no support for other escape sequences (e.g. `\n`, `\t`). To
produce a line break *within* rendered text, use the literal substring
`[newline]` (see §2.4) rather than an escape sequence or a real newline.

### 2.4 Inline text substitutions

Two literal substrings are recognized inside rendered text and replaced
at render time (not at parse time — they are stored verbatim in the
parsed text and substituted by the renderer):

- `[newline]` — forced line break. Valid inside `@heading`, `@text`,
  `@bullet`, `@code`, and `@quote` text.
- `[page]` — current page number. Valid **only** inside `@footer` text.

### 2.5 Attribute blocks

```
{key1=value1,key2,key3=value3}
```

- Delimited by `{` and `}`. The parser scans for the first `}` with no
  support for nested braces or escaped braces — an attribute block may
  not contain a literal `}` in a value.
- Entries are comma-separated.
- An entry of the form `key=value` sets a string-valued attribute. Both
  the key and value are lowercased.
- An entry with no `=` is a boolean flag, set to `true`.
- Whitespace around entries and around `=` is trimmed.
- An attribute block is optional and, when present, must immediately
  follow (whitespace permitted) the command's quoted text argument.

## 3. Document structure

An EPP document consists of an optional version marker, followed by an
unordered mixture of document-level commands and page content, organized
into pages by `@newpage`.

### 3.1 Version marker

```
%epp=0.2%
```

If present, this must be the first non-whitespace content in the file.
It is delimited by `%` ... `%`. Parsers are not required to reject files
with a missing or different version marker — the reference implementation
parses the rest of the file regardless of what (if anything) appears here.

### 3.2 Document-level commands

These set properties of the whole document. They may appear anywhere in
the file but are conventionally placed before the first page's content.

#### `@meta key="value"`

Stores an arbitrary metadata key/value pair (e.g. author, version,
keywords). Not rendered anywhere by the reference viewer. Unlike other
commands, this uses **inline** `key=value` syntax (no surrounding quotes
required around the whole pair) rather than a quoted-string argument:

```
@meta author="Jordan Pena"
@meta version="0.2"
```

See §7.2 for an important parsing caveat with this command.

#### `@title "text"`

Sets the document title, shown in viewer chrome (e.g. browser tab title,
toolbar brand label).

#### `@header "text"`

Sets a line of text rendered in a thin band at the **top of every page**.
May contain `[newline]` for a multi-line header.

#### `@footer "text"`

Sets a line of text rendered in a thin band at the **bottom of every
page**. May contain `[newline]` and the page-number token `[page]`
(see §2.4). If no `@footer` is set anywhere in the document, each page
instead gets a default centered footer showing just its page number.

### 3.3 Pages

A document is divided into pages by `@newpage`:

#### `@newpage`

Ends the current page (pushing it onto the document's page list) and
begins a new, empty page. A document always has at least one page, even
if `@newpage` is never used or the file is empty.

#### `@page <label>`

Sets the **label** of the *current* page (used in navigation UI as
`<label> / <total page count>`). This does **not** create a new page —
it only annotates whichever page is currently being built. If omitted,
a page's label defaults to its 1-based position in the document.

> **Important:** `@page` and `@newpage` are independent. A common mistake
> is assuming `@page 2` starts page 2 — it doesn't. The correct pattern
> for a multi-page document is:
> ```
> @page 1
> ... content ...
> @newpage
> @page 2
> ... content ...
> ```

### 3.4 Page content blocks

Each of the following commands appends one block to the page currently
being built.

#### `@heading "text" {attrs}`

A large, bold heading.

#### `@text "text" {attrs}`

A normal body paragraph.

Both `@heading` and `@text` accept these attributes:

| Attribute | Values | Effect |
|---|---|---|
| `color` | see §4 | Text color |
| `align` | `left` (default), `center`, `right` | Text alignment. Any other value is ignored and falls back to `left`. |
| `bold` | flag | Bold weight |
| `italic` | flag | Italic style |
| `underline` | flag | Underline |

#### `@bullet "text" {attrs}`

A list item. Consecutive `@bullet` commands (with no other block type in
between) are grouped into a single visual list; any other block type
closes the list.

Accepts the same `color`/`align`/`bold`/`italic`/`underline` attributes
as `@text`, plus:

| Attribute | Values | Effect |
|---|---|---|
| `type` | `disc` (default), `number`, `check`, `arrow`, `star` | Bullet glyph. `disc` → •, `check` → ✓, `arrow` → →, `star` → ★. `number` renders an auto-incrementing `1.`, `2.`, `3.` ... counter that resets whenever the list is broken by a non-bullet block. |

#### `@code "text" {attrs}`

A monospaced, pre-formatted code block, rendered with a shaded background
and an accent-colored left border. `attrs` are parsed but have no visual
effect in the reference renderer (reserved for future use).

#### `@quote "text"`

An italicized blockquote, rendered with an accent-colored left border.
Takes no meaningful attributes.

#### `@space`

Inserts vertical whitespace. Takes no arguments.

#### `@line`

Inserts a horizontal rule across the content width. Takes no arguments.

#### `@label <name>`

Inserts an invisible position marker, rendered by viewers as a small tab
on the page's edge (intended for bookmarking or cross-referencing a
location in a long document). `<name>` is a single bare word — not a
quoted string. Spaces are not permitted in the name.

#### `@table "h1|h2|h3..."`

Begins a new table on the current page. The quoted argument is a single
string of column headers separated by the pipe character `|`.

#### `@row "v1|v2|v3..."`

Appends one row to a table. The quoted argument is a single string of
cell values separated by `|`. An `@row` attaches itself to the **most
recently declared `@table` block on the current page** — see §7.3 for
the consequence of having multiple tables on one page.

A row's cell count does not need to match the header's column count:
missing trailing cells render blank; extra cells beyond the header count
are dropped by the reference renderer.

## 4. Color names

The `color` attribute accepts only the following named values (hex codes
and other CSS color syntax are **not** supported):

```
black   red   blue   green   gray (= grey)   white   amber (= orange)   purple
```

An unrecognized color name is silently ignored; the block renders in the
default ink color instead of raising an error.

## 5. Grammar summary (EBNF-style)

```
document     := [version-marker] {top-level-item}
version-marker := "%" "epp=" token "%"
top-level-item := meta-cmd | title-cmd | header-cmd | footer-cmd
                | page-cmd | newpage-cmd | content-block | COMMENT

meta-cmd     := "@meta" WS key "=" ["\""] value ["\""]
title-cmd    := "@title" WS quoted-string
header-cmd   := "@header" WS quoted-string
footer-cmd   := "@footer" WS quoted-string
page-cmd     := "@page" WS token
newpage-cmd  := "@newpage"

content-block := heading-cmd | text-cmd | bullet-cmd | code-cmd
              | quote-cmd | space-cmd | line-cmd | label-cmd
              | table-cmd | row-cmd

heading-cmd  := "@heading" WS quoted-string [attr-block]
text-cmd     := "@text"    WS quoted-string [attr-block]
bullet-cmd   := "@bullet"  WS quoted-string [attr-block]
code-cmd     := "@code"    WS quoted-string [attr-block]
quote-cmd    := "@quote"   WS quoted-string
space-cmd    := "@space"
line-cmd     := "@line"
label-cmd    := "@label"   WS token
table-cmd    := "@table"   WS quoted-string        ; pipe-delimited headers
row-cmd      := "@row"     WS quoted-string        ; pipe-delimited cells

attr-block   := "{" attr-entry {"," attr-entry} "}"
attr-entry   := key ["=" value]

quoted-string := "\"" {ESCAPED-CHAR | CHAR} "\""
token        := CHAR {CHAR}            ; no whitespace, "{", or ";"
```

## 6. Worked example

```
%epp=0.2%
@meta author="jordan"
@title "Quarterly Update"
@header "Internal — Q3 Review"
@footer "Page [page]"
@page 1
@heading "Highlights" {align=center,bold}
@text "Revenue grew 12% quarter over quarter."
@bullet "Shipped the new onboarding flow" {type=check}
@bullet "Closed three enterprise deals" {type=check}
@space
@quote "Best quarter in company history."
@newpage
@page 2
@heading "Team Breakdown"
@table "Team|Headcount|Open Roles"
@row "Engineering|24|3"
@row "Sales|11|2"
@row "Support|6|0"
```

This produces a two-page document: page 1 with a centered bold heading, a
paragraph, two check-marked bullets, a spacer, and a quote; page 2 with a
heading and a three-column, three-row table. Both pages show the header
band "Internal — Q3 Review" and a footer reading "Page 1" / "Page 2"
respectively.

## 7. Implementation notes and known quirks

These behaviors are preserved from the reference implementation. A
conforming parser that aims for compatibility with existing `.epp` files
in the wild should replicate them rather than "fixing" them, since
documents may have been authored around this exact behavior.

### 7.1 Comments are only recognized between top-level tokens

The `;` comment character is only special when the parser is scanning
for the next `@command` — it is not specially handled in the middle of
parsing a command's arguments. In practice this means comments should
always be placed on their own line; placing one after a command on the
same line works only incidentally and should not be relied upon.

### 7.2 `@meta key="value"` does not reliably handle multi-word values

`@meta` reads a single inline token up to the next whitespace, *then*
checks whether the result starts and ends with `"` to strip quotes. For
a value containing a space (e.g. `@meta title="My Document"`), only the
first word (`"My`) is read before whitespace ends the token, so the
quote-stripping never triggers and the stored value retains a leading
stray `"` and is truncated to the first word. **Use `@title "..."` to
set the document title** rather than `@meta title="..."`; reserve `@meta`
for genuinely single-word or no-space values.

### 7.3 `@row` always targets the nearest preceding `@table` on the page

If a page contains two `@table` blocks with other content in between,
every `@row` — regardless of where it appears relative to that other
content — attaches to whichever `@table` was declared most recently
before it. Authors should keep each table's `@row` commands contiguous
with their `@table` and avoid interleaving two tables' rows on the same
page.

### 7.4 Unknown commands and malformed input do not raise errors

The format has no validation step. An unrecognized `@command` has its
optional quoted-string argument and attribute block (if present)
consumed and silently discarded. A file containing no valid EPP syntax
at all (e.g. plain prose with no `@` commands) parses successfully into
a single page with zero blocks, rather than failing. A misspelled
attribute key (e.g. `{colour=red}` instead of `{color=red}`) is stored
as an unrecognized attribute and has no visual effect, again without any
error. Authors should validate documents by rendering them and visually
confirming the expected blocks appear, rather than relying on the parser
to catch mistakes.

### 7.5 The `aling` → `align` typo correction

For historical reasons, the attribute key `aling` (a transposition typo
of `align`) is silently corrected to `align` by the reference parser.
This is a preserved legacy compatibility shim, not a documented alias —
new documents should spell `align` correctly rather than relying on it.

## 8. Non-goals / explicit omissions

The following are intentionally outside the scope of EPP 0.2 and have no
syntax defined for them: images, links/hyperlinks, footnotes, nested
lists, cell spanning or styling within tables, custom fonts, page size or
margin control, and any unit of measurement. Documents requiring these
features should be authored in a different format.
