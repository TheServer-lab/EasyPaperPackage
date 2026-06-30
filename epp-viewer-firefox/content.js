/* EPP Viewer — Firefox content script
 *
 * Firefox renders local .epp files as plain text in a <pre> tag,
 * same as Chrome. This script detects that, parses the EPP source,
 * and mounts the viewer in place.
 *
 * Firefox also sometimes wraps the <pre> in a <body> with extra
 * elements (encoding info bar), so we search for the pre more
 * broadly than just body.children[0].
 */
(function () {
  // Find the first <pre> on the page
  const pre = document.querySelector('pre');
  if (!pre) return;

  const text = pre.textContent || '';
  if (!/^\s*%epp=/.test(text)) return;

  let doc;
  try {
    doc = parseEPP(text);
  } catch (err) {
    return;
  }

  if (doc.title) document.title = doc.title + ' \u2014 EPP';

  // Remove all existing body content and mount the viewer
  document.body.innerHTML = '<div id="epp-root"></div>';
  mountViewer(document.getElementById('epp-root'), doc, { showOpenButton: false });
})();
