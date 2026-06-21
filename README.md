# Easy Paper Package (EPP)

> A plain UTF-8 document format for printable documents — no binaries, no internet, no complexity.

EPP is a lightweight, line-oriented document format designed for the simple case: a document that fits on A4 paper, with headings, paragraphs, lists, and the occasional table. It sits between a plain `.txt` file and a full PDF — structured enough to print cleanly, simple enough to last forever.

```
%epp=0.2%
; Header & footer on every page
@header "My Report"
@footer "Page [page]"

@page 1
@heading "Quarterly Summary" {bold,align=center}
@space
@quote "Simple formats survive longer."
@line
@bullet "Revenue up 12%" {type=check}
@bullet "Costs reduced" {type=check}
@bullet "New hires" {type=arrow}
```

## Why EPP?

- **Pure UTF-8** — every `.epp` file is plain text. Open it in Notepad and it reads fine.
- **No binaries** — zero embedded data. Images, fonts, and rendering are the viewer's job, not the file's.
- **Offline** — the viewer makes no network requests. Documents never leave your machine unless you choose.
- **A4 ready** — every page maps to A4 paper. Hit print and it comes out right.
- **Easy to parse** — a working parser fits in under 100 lines of JavaScript.
- **Human readable** — future-proof by design. In 30 years you can still open an `.epp` file and read it.

## This repository

This repo contains the EPP website: the landing page, documentation, and a browser-based editor for writing and exporting `.epp` files.

| File | Description |
|---|---|
| `index.html` | Landing page — overview, features, and a live example |
| `learning.html` | Full documentation — syntax, commands, attributes, escapes |
| `editor.html` | In-browser editor — write, preview, import, and export `.epp` files |
| `download.html` | Links out to this repository's [Releases](https://github.com/TheServer-lab/EasyPaperPackage/releases) |
| `license.html` | License terms |

Each page is a self-contained HTML file with no build step and no external dependencies — clone the repo and open `index.html` directly, or serve the folder with any static file server.

## Getting started

```bash
git clone https://github.com/TheServer-lab/EasyPaperPackage.git
cd EasyPaperPackage
open index.html   # or just double-click it
```

To try the format immediately, open `editor.html`, write a few `@heading` / `@text` / `@bullet` blocks, and use **Export** to download a `.epp` file, or **Source** to see the generated text.

## Format overview

An EPP file is a sequence of commands, one per line:

```
@command "text" {attributes}
```

- `@` prefixes a command (`@heading`, `@text`, `@bullet`, `@table`, …)
- Text arguments are wrapped in double quotes
- Attributes are an optional comma-separated list in `{ }` — flags like `bold`, or key-value pairs like `align=center`
- A semicolon (`;`) starts a comment, ignored to end of line
- Pages are separated with `@newpage`; `@header` / `@footer` repeat on every page

See [`learning.html`](./learning.html) for the complete command reference, attribute table, escape sequences, and a full worked example.

## Releases

Pre-built releases, source archives, and changelogs are published under [Releases](https://github.com/TheServer-lab/EasyPaperPackage/releases).

## License

Copyright © 2026 Sourasish Das. All rights reserved.

This software is proprietary, but free to use by anyone for any purpose. Redistribution, modification, and resale require permission. See [`license.html`](./license.html) or `LICENSE` for the full terms.
