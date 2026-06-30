/* Webview bootstrap for the EPP live preview panel.
 * Uses parseEPP() and renderDocumentHTML() from epp-core.js (the original,
 * unmodified parser/renderer) and adapts them to VS Code's webview
 * messaging API instead of a standalone toolbar + file input.
 */
(function () {
  const vscode = acquireVsCodeApi();

  const pagesEl = document.getElementById('epp-pages');
  const brandEl = document.getElementById('epp-brand');
  const indicatorEl = document.getElementById('epp-indicator');
  const prevBtn = document.getElementById('epp-prev');
  const nextBtn = document.getElementById('epp-next');
  const errorBanner = document.getElementById('epp-error-banner');

  let doc = { title: null, header: null, footer: null, meta: {}, pages: [{ number: null, blocks: [] }] };
  let currentIndex = 0;
  // Restore page position across re-renders triggered by edits, within a session.
  const previousState = vscode.getState();
  if (previousState && typeof previousState.currentIndex === 'number') {
    currentIndex = previousState.currentIndex;
  }

  function renderPages() {
    pagesEl.innerHTML = renderDocumentHTML(doc);
  }

  function updateNav() {
    const total = doc.pages.length;
    currentIndex = Math.max(0, Math.min(currentIndex, total - 1));
    const page = doc.pages[currentIndex];
    const label = page && page.number ? page.number : String(currentIndex + 1);
    indicatorEl.textContent = `${label} / ${total}`;
    [...pagesEl.children].forEach((el, i) => {
      el.style.display = i === currentIndex ? 'block' : 'none';
    });
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex === total - 1;
    vscode.setState({ currentIndex });
  }

  function setDoc(newDoc, opts) {
    opts = opts || {};
    doc = newDoc;
    if (!opts.preserveIndex) currentIndex = 0;
    brandEl.textContent = doc.title || 'EPP document';
    renderPages();
    updateNav();
  }

  prevBtn.addEventListener('click', () => { currentIndex--; updateNav(); });
  nextBtn.addEventListener('click', () => { currentIndex++; updateNav(); });

  window.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { currentIndex++; updateNav(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { currentIndex--; updateNav(); }
  });

  window.addEventListener('message', (event) => {
    const message = event.data;
    if (message.type === 'update') {
      errorBanner.style.display = 'none';
      try {
        const parsed = parseEPP(message.text);
        setDoc(parsed, { preserveIndex: true });
      } catch (err) {
        errorBanner.textContent = 'Could not parse this document: ' + (err && err.message ? err.message : err);
        errorBanner.style.display = 'block';
      }
    }
  });

  vscode.postMessage({ type: 'ready' });
})();
