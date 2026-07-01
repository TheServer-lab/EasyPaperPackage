# Changelog

## 0.4.0

- Updated bundled parser/renderer to EPP 0.4 (backward compatible with
  0.1 through 0.3 documents).
- Syntax highlighting and live preview support for the new `@watermark
  "text" {color=,opacity=,rotate=,size=}` command, rendered centered
  behind page content on every page.
- Syntax highlighting and live preview support for the new `@sign
  "NAME" {ORG-ID}` command (page-scoped signature line).
- Syntax highlighting and live preview support for the new
  `@signandclose "NAME" {ORG-ID}` command. As in the reference renderer,
  this acts as a hard document terminator: it renders identically to
  `@sign`, but any content after the first occurrence is discarded.
- Syntax highlighting for the new `@ex:*` extension-namespace commands.
  These are parsed and ignored gracefully by the renderer (per spec),
  and are highlighted distinctly in the editor to signal that they have
  no defined rendering behavior.
- Added `white` as a recognized `@page` background color, matching the
  renderer's new `PAGE_COLORS.white`.
- **Not** carried over from the upstream v0.4 bundle: its screen-sizing
  and print stylesheet regress the 210mm/A4-exact print fix shipped in
  0.3.1 (back to an approximate `560px`-based layout and a `display:flex`
  print path that doesn't paginate reliably). Since this extension's
  preview doesn't expose printing, the practical impact here is limited
  to on-screen page proportions — but this version keeps the 0.3.1
  sizing/print CSS rather than adopting that regression, and only pulls
  in the genuinely new `@watermark`/`@sign` styles. Worth flagging
  upstream if you maintain the browser extension too.

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
