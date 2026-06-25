(function(){
  // Chrome renders local plain-text files as a single <pre> filling <body>.
  // Only take over the page if that's exactly what we see, and the content
  // actually looks like an EPP document (starts with the %epp=...% header).
  const body = document.body;
  if (!body || body.children.length !== 1) return;
  const pre = body.children[0];
  if (pre.tagName !== 'PRE') return;

  const text = pre.textContent || '';
  if (!/^\s*%epp=/.test(text)) return;

  let doc;
  try {
    doc = parseEPP(text);
  } catch (err) {
    return; // not a well-formed EPP file; leave Chrome's default view alone
  }

  if (doc.title) document.title = `${doc.title} \u2014 EPP`;

  body.innerHTML = '<div id="epp-root"></div>';
  mountViewer(document.getElementById('epp-root'), doc, { showOpenButton: false });
})();
