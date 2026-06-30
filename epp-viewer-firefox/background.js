/* EPP Viewer — Firefox background script
 *
 * Uses the WebExtensions `browser.*` API (Promise-based).
 * Falls back to `chrome.*` for any Chromium-based builds.
 *
 * Intercepts navigation to any URL ending in .epp and redirects
 * to the built-in viewer page, passing the original URL as ?src=
 */

const api    = typeof browser !== 'undefined' ? browser : chrome;
const VIEWER = api.runtime.getURL('viewer.html');

/* Open viewer when toolbar button is clicked */
api.browserAction.onClicked.addListener(() => {
  api.tabs.create({ url: VIEWER });
});

/* Intercept navigations to *.epp URLs */
api.webNavigation.onBeforeNavigate.addListener((details) => {
  if (details.frameId !== 0) return;

  const url = details.url;
  if (url.startsWith(VIEWER)) return;  // already in viewer — don't loop

  let pathname = '';
  try { pathname = new URL(url).pathname; } catch (e) { return; }
  if (!pathname.toLowerCase().endsWith('.epp')) return;

  const viewerUrl = VIEWER + '?src=' + encodeURIComponent(url);
  api.tabs.update(details.tabId, { url: viewerUrl });
});
