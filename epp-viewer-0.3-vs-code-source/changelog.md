# Changelog

## 0.3.1

- Updated bundled renderer to match an upstream fix to page sizing: the
  preview's page now sizes itself to true A4 proportions (210mm width,
  1:√2 aspect ratio) instead of an approximated fixed width/ratio.
- Bundled CSS also picked up an overhauled print stylesheet (exact
  210×297mm sheets, zero margins, forced color printing for callouts/
  highlights/page tints/lined rules/table striping) from the same
  upstream update. This applies to the browser extension's print/export
  path; the VS Code preview itself does not expose printing, so this
  part has no visible effect here, but is included for parity with the
  bundled file.

## 0.3.0

- Updated bundled parser/renderer to EPP 0.3 (backward compatible with
  0.1 and 0.2 documents).
- Syntax highlighting for the new `@callout` command and its `color=`
  attribute.
- Syntax highlighting for the new `highlight=` attribute on `@text` and
  `@heading`.
- Syntax highlighting for the new page-level attribute block on `@page`
  (`color=`, `lined`, `rotate=`).
- Live preview now renders callout boxes, highlighted text, page
  background tints, notebook-style lined pages, and rotated page content.

## 0.2.0

- Initial release.
- Syntax highlighting for the EPP 0.2 grammar.
- Live preview panel with page navigation, matching the EPP Viewer
  browser extension's rendering.
