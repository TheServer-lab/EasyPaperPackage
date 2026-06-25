/* EPP Viewer — background service worker
 *
 * Intercepts any navigation to a URL whose path ends with .epp
 * (on http://, https://, or file://) and redirects the tab to
 * the built-in viewer, passing the original URL as a query param.
 *
 * Local file:// .epp files are also handled by content.js, but
 * this redirect path gives the same experience as remote URLs.
 */

const VIEWER = chrome.runtime.getURL('viewer.html');

/* Open viewer when the toolbar button is clicked */
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: VIEWER });
});

/* Intercept navigations to *.epp URLs */
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  // Only act on top-level navigations (frameId 0)
  if (details.frameId !== 0) return;

  const url = details.url;

  // Already in our viewer — don't loop
  if (url.startsWith(VIEWER)) return;

  // Check if the URL path ends with .epp (ignore query/hash)
  let pathname = '';
  try {
    pathname = new URL(url).pathname;
  } catch (e) {
    return;
  }

  if (!pathname.toLowerCase().endsWith('.epp')) return;

  // Redirect to viewer with the original URL encoded as ?src=
  const viewerUrl = VIEWER + '?src=' + encodeURIComponent(url);
  chrome.tabs.update(details.tabId, { url: viewerUrl });
});
