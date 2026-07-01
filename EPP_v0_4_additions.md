# EPP — Easy Paper Package
## v0.4 Additions Draft

This document covers only what is new in v0.4. A v0.4 parser must also accept all v0.1, v0.2, and v0.3 syntax.

---

## Version Entry

| Version | Status | Summary |
|---------|--------|---------|
| v0.4 | Frozen | Watermarks, extension namespace, page signatures and document close |

---

## New Commands

### `@watermark`

Renders a large decorative text stamp across the page, behind all content. Declared once and applies to every page in the document unless overridden on a specific page.

```epp
@watermark "DRAFT"
@watermark "Classified" {center, rotate=40, size=150, color=blue, opacity=50}
```

`@watermark` is a document-level command and should be declared before the first `@page`. A renderer that cannot support transparency should fall back to rendering the watermark in a light tint of the specified `color` rather than omitting it entirely.

#### Watermark attributes

| Attribute | Values | Notes |
|-----------|--------|-------|
| `center` | flag | Centers the watermark on the page. Default behaviour. |
| `rotate` | integer (degrees) | Angle of rotation for the watermark text. Default: `0` |
| `size` | integer | Relative size hint for the watermark text. Default: `100` |
| `color` | see 8.2 | Colour of the watermark text. Default: `gray` |
| `opacity` | `0`–`100` | Transparency of the watermark as a percentage. `0` = invisible, `100` = fully opaque. Default: `30`. Renderers that cannot support transparency should fall back to a light tint of the specified `color`. |

---

### `@ex:` — Extension Namespace

Commands prefixed with `@ex:` belong to the extension namespace. They are not part of the core EPP spec. The `@ex:` prefix signals to both humans and parsers that a non-standard command is in use.

```epp
@ex:graph "sales_data.csv" {type=bar, color=blue}
@ex:qrcode "https://example.com"
@ex:signature {pad=true}
```

Extension commands follow the same general syntax as core commands:

```epp
@ex:name "optional text" {optional attributes}
```

The text argument and attribute block are both optional, as with some core commands. Attribute syntax inside `{ }` is identical to core EPP attribute syntax.

A v0.4 parser that does not recognise a specific extension command must ignore it gracefully and continue parsing. Extension commands are fully outside the frozen v0.4 scope and are not required to be implemented by any conforming renderer.

---

### `@sign`

Places a page-scoped signature at the point it appears in the document. Rendered as a dash followed by the signatory name (e.g. `-RICK`). Multiple `@sign` commands may appear on the same page to record co-signatories. They render in source order.

```epp
@sign "RICK" {ORG-001}
@sign "ALICE" {ORG-002}
```

The attribute block contains a single value: the third-party organisation's identifier for the signatory. This ID is **never rendered** — it is metadata intended for third-party document management or identity systems. The ID may be any value (integer, float, or string) as defined by the issuing organisation.

#### Behaviour

- Page-scoped: a `@sign` applies only to the page it appears on.
- Multiple `@sign` commands on the same page are permitted (co-signatories).
- `@sign` has no effect on subsequent pages.

---

### `@signandclose`

Places a single document-scoped signature and marks the document as closed. Only one `@signandclose` is permitted per document.

```epp
@signandclose "RICK" {ORG-001}
```

Rendered identically to `@sign` (e.g. `-RICK`). The third-party ID follows the same rules as `@sign` — any type, never rendered.

#### Behaviour

- Document-scoped: the signature applies to the document as a whole, not to a single page.
- Acts as a hard document terminator. Any content after `@signandclose` is ignored by the parser.
- Only one `@signandclose` is permitted. A second occurrence is invalid and should be ignored by renderers.
- A document containing `@signandclose` is considered closed and final.

---

## Frozen Scope

**Added in v0.4:**
`@watermark` with `rotate=`, `size=`, `opacity=`, `color=`, `center`; `@ex:` extension namespace; `@sign` with third-party ID attribute; `@signandclose` as document terminator.

Anything else is outside frozen v0.4 and belongs in a future version.

---

## Example Fragment

```epp
%epp=0.4%

@meta title="Classified Report"
@meta author="RICK"

@watermark "CLASSIFIED" {rotate=40, size=150, color=red, opacity=40}

@header "Classified Report"
@footer "Page [page]"

@page 1
@heading "Summary" {bold}
@text "This document contains sensitive information."
@callout "Handle with care." {color=red}
@sign "RICK" {ORG-001}
@sign "ALICE" {ORG-002}

@newpage

@page 2
@heading "Details" {bold}
@text "Further details are contained in the appendix."
@ex:graph "figures.csv" {type=bar, color=blue}

@signandclose "RICK" {ORG-001}
```
