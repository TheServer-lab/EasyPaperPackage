const SAMPLE_SOURCE = `%epp=0.4%
@meta title="EPP v0.4 Feature Test"
@meta author="SD"
@watermark "DRAFT" {rotate=40, size=150, color=gray, opacity=18}
@header "EPP v0.4 Feature Test"
@footer "Page [page]"
@page 1
@heading "EPP v0.4 — All Features" {bold,align=center}
@text "This document tests every v0.4 feature. Use the arrows to step through pages."
@space
@heading "New in v0.4"
@bullet "Watermarks — @watermark with rotate, size, opacity, color" {type=arrow}
@bullet "Sign blocks — @sign page-scoped signatory" {type=arrow}
@bullet "Document close — @signandclose" {type=arrow}
@bullet "Extension namespace — @ex: commands ignored gracefully" {type=arrow}
@space
@callout "The DRAFT watermark is visible behind this content." {color=gray}
@sign "RICK" {ORG-001}
@newpage
@page 2
@watermark "CONFIDENTIAL" {rotate=40, size=140, color=red, opacity=22}
@heading "Watermark Override" {bold}
@text "This page overrides the document watermark with a red CONFIDENTIAL stamp."
@space
@sign "ALICE" {ORG-002}
@sign "BOB" {ORG-003}
@newpage
@page 3
@heading "Extension Namespace" {bold}
@text "The @ex: commands below are silently ignored by the parser."
@code "@ex:graph \\"data.csv\\" {type=bar}[newline]@ex:qrcode \\"https://example.com\\""
@ex:graph "data.csv" {type=bar, color=blue}
@ex:qrcode "https://example.com"
@space
@text "Rendering continues normally after ignored @ex: commands." {highlight=green}
@signandclose "RICK" {ORG-001}
`;

/* ── UI helpers ── */
const root     = document.getElementById('epp-root');
const statusEl = document.getElementById('epp-status');
const msgEl    = document.getElementById('status-msg');
const urlEl    = document.getElementById('status-url');
const retryBtn = document.getElementById('status-retry');

function showStatus(icon, msg, url, allowRetry) {
  root.style.display = 'none';
  statusEl.classList.add('visible');
  statusEl.querySelector('.status-icon').textContent = icon;
  msgEl.textContent = msg;
  urlEl.textContent = url || '';
  retryBtn.style.display = allowRetry ? 'inline-block' : 'none';
}
function hideStatus() {
  statusEl.classList.remove('visible');
  root.style.display = '';
}

/* ── Render a source string ── */
function renderSource(text, sourceUrl) {
  if (!/^\s*%epp=/.test(text)) {
    showStatus('❓', "This doesn't look like an EPP document (missing %epp=…% header).", sourceUrl, false);
    return;
  }
  let doc;
  try { doc = parseEPP(text); } catch (err) {
    showStatus('❌', 'Parse error: ' + err.message, sourceUrl, false);
    return;
  }
  if (doc.title) document.title = doc.title + ' — EPP';
  hideStatus();
  mountViewer(root, doc, { showOpenButton: true, sourceUrl: sourceUrl });
}

/* ── Load from a URL ──
   Chrome blocks fetch() on file:// from extension pages,
   so we use XMLHttpRequest which works with the file:// permission. */
function loadFromUrl(src) {
  showStatus('⏳', 'Loading…', src, false);
  const xhr = new XMLHttpRequest();
  xhr.open('GET', src, true);
  xhr.responseType = 'text';
  xhr.onload = function () {
    if (xhr.status === 200 || xhr.status === 0) { // 0 = file:// success
      renderSource(xhr.responseText, src);
    } else {
      showStatus('⚠️', 'Could not load document: HTTP ' + xhr.status, src, true);
      retryBtn.onclick = () => loadFromUrl(src);
    }
  };
  xhr.onerror = function () {
    showStatus('⚠️', 'Could not load document. Check the file exists and the extension has file access enabled.', src, true);
    retryBtn.onclick = () => loadFromUrl(src);
  };
  xhr.send();
}

/* ── Boot ── */
const params = new URLSearchParams(window.location.search);
const src    = params.get('src');

if (src) {
  loadFromUrl(decodeURIComponent(src));
} else {
  hideStatus();
  mountViewer(root, parseEPP(SAMPLE_SOURCE), { showOpenButton: true });
}
