const vscode = require('vscode');

/** Tracks the single preview panel per source document URI, so re-running
 * the preview command on a doc that already has one open just reveals it
 * instead of creating duplicates. */
const activePanels = new Map(); // uriString -> { panel, document }

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand('epp.showPreview', () => openPreview(context, vscode.ViewColumn.Active)),
    vscode.commands.registerCommand('epp.showPreviewToSide', () => openPreview(context, vscode.ViewColumn.Beside))
  );

  // Live update: whenever any tracked document's text changes, re-render
  // its preview (if open) with the new content.
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const key = event.document.uri.toString();
      const entry = activePanels.get(key);
      if (entry) {
        postUpdate(entry.panel, event.document);
      }
    })
  );

  // Clean up tracking when an editor's underlying document closes.
  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((document) => {
      const key = document.uri.toString();
      const entry = activePanels.get(key);
      if (entry) {
        entry.panel.dispose();
        activePanels.delete(key);
      }
    })
  );
}

function getActiveEppDocument() {
  const editor = vscode.window.activeTextEditor;
  if (editor && editor.document.languageId === 'epp') return editor.document;
  // Fall back to any already-open .epp document (covers "preview" being
  // triggered from a context where focus isn't the editor itself).
  const fallback = vscode.workspace.textDocuments.find((d) => d.languageId === 'epp');
  return fallback || null;
}

function openPreview(context, viewColumn) {
  const document = getActiveEppDocument();
  if (!document) {
    vscode.window.showWarningMessage('Open an .epp file first to preview it.');
    return;
  }

  const key = document.uri.toString();
  const existing = activePanels.get(key);
  if (existing) {
    existing.panel.reveal(viewColumn);
    return;
  }

  const panel = vscode.window.createWebviewPanel(
    'eppPreview',
    `Preview: ${baseName(document.fileName)}`,
    viewColumn,
    {
      enableScripts: true,
      retainContextWhenHidden: true,
      localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'media')],
    }
  );

  panel.webview.html = buildHtml(panel.webview, context, document);

  panel.webview.onDidReceiveMessage((message) => {
    if (message && message.type === 'ready') {
      postUpdate(panel, document);
    }
  });

  panel.onDidDispose(() => {
    activePanels.delete(key);
  });

  activePanels.set(key, { panel, document });
}

function postUpdate(panel, document) {
  panel.webview.postMessage({ type: 'update', text: document.getText() });
}

function baseName(p) {
  const parts = p.split(/[\\/]/);
  return parts[parts.length - 1];
}

function buildHtml(webview, context, document) {
  const mediaUri = (file) =>
    webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'media', file));

  const nonce = getNonce();
  const csp = [
    `default-src 'none'`,
    `img-src ${webview.cspSource} https: data:`,
    `style-src ${webview.cspSource} 'unsafe-inline'`,
    `script-src 'nonce-${nonce}'`,
    `font-src ${webview.cspSource}`,
  ].join('; ');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <link rel="stylesheet" href="${mediaUri('epp-style.css')}">
  <link rel="stylesheet" href="${mediaUri('webview-chrome.css')}">
  <title>EPP Preview</title>
</head>
<body>
  <div id="epp-toolbar">
    <div id="epp-brand">EPP document</div>
    <div id="epp-nav">
      <button id="epp-prev" class="epp-nav-btn" title="Previous page">&#8249;</button>
      <span id="epp-indicator"></span>
      <button id="epp-next" class="epp-nav-btn" title="Next page">&#8250;</button>
    </div>
  </div>
  <div id="epp-error-banner"></div>
  <div id="epp-pages"></div>

  <script nonce="${nonce}" src="${mediaUri('epp-core.js')}"></script>
  <script nonce="${nonce}" src="${mediaUri('preview.js')}"></script>
</body>
</html>`;
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}

function deactivate() {}

module.exports = { activate, deactivate };
