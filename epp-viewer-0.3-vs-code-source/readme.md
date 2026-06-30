# EPP Viewer for VS Code

Syntax highlighting and a live preview panel for `.epp` ("Easy Paper
Package") documents — a lightweight, plain-text alternative to PDF/Word
for simple printable documents.

## Features

- **Syntax highlighting** for the full EPP grammar (versions 0.1 through
  0.3): `@commands`, quoted strings (with escape sequences and the
  `[newline]`/`[page]` placeholders highlighted distinctly), attribute
  blocks (`{align=center,bold}`), the new v0.3 `@callout` command and
  its `color=` attribute, the new `highlight=` attribute on `@text`/
  `@heading`, the new page-level `{color=,lined,rotate=}` block on
  `@page`, comments, the version marker, and table cell separators.
- **Live preview**, just like Markdown's built-in preview: open a `.epp`
  file, run **EPP: Open Preview to the Side**, and see a paginated,
  styled rendering that updates as you type. Page navigation (buttons,
  arrow keys) lets you flip through multi-page documents without
  scrolling past them. v0.3 page styling — background tints, notebook-
  style lined pages, and rotated page content — renders in the preview
  exactly as it would in the EPP Viewer browser extension.

The preview uses the same parsing and rendering logic as the original EPP
Viewer browser extension, so what you see here matches what readers will
see.

## Usage

1. Open any `.epp` file — syntax highlighting applies automatically.
2. Click the preview icon in the editor title bar, or run **EPP: Open
   Preview to the Side** from the Command Palette (`Ctrl+Shift+P` /
   `Cmd+Shift+P`), or press `Ctrl+K V` (`Cmd+K V` on macOS).
3. Edit the file — the preview updates live.

## Commands

| Command | Description |
|---|---|
| `EPP: Open Preview` | Opens the preview in the current editor group |
| `EPP: Open Preview to the Side` | Opens the preview beside the current editor (like Markdown's side preview) |

## Format reference

The complete EPP grammar — every command and attribute through v0.3,
including `@callout`, `highlight=`, and the page-level `color=`/`lined`/
`rotate=` attributes — is specified in `EPP_Frozen_Spec_v0_3.md` (shipped
alongside this extension, not bundled inside the `.vsix`).

## Known limitations

- The preview does not currently support printing/exporting to PDF from
  within VS Code. For that, use the standalone EPP Viewer desktop app or
  its PDF export feature.
- Tables, code blocks, and quotes don't currently support custom
  attributes in the reference renderer (this mirrors the original
  format's behavior, not a limitation specific to this extension).
