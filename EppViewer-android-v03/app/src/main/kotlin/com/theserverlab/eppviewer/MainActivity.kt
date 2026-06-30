package com.theserverlab.eppviewer

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.progressindicator.LinearProgressIndicator
import org.json.JSONException
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    // ── Views ─────────────────────────────────────────────────────────────
    private lateinit var toolbar: MaterialToolbar
    private lateinit var progressBar: LinearProgressIndicator
    private lateinit var webView: WebView

    // ── State ─────────────────────────────────────────────────────────────
    private var currentUri: Uri? = null
    private var pageCount: Int = 0

    // ── File picker ───────────────────────────────────────────────────────
    private val filePicker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { openEppUri(it) }
    }

    // ─────────────────────────────────────────────────────────────────────
    // Lifecycle
    // ─────────────────────────────────────────────────────────────────────

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        toolbar     = findViewById(R.id.toolbar)
        progressBar = findViewById(R.id.progress_bar)
        webView     = findViewById(R.id.web_view)

        setSupportActionBar(toolbar)
        setupWebView()

        // Handle files launched from an external file manager
        if (intent?.action == Intent.ACTION_VIEW) {
            intent.data?.let { openEppUri(it) }
        } else {
            // Fresh launch — show the welcome screen
            webView.loadUrl("file:///android_asset/viewer.html")
        }
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        if (intent?.action == Intent.ACTION_VIEW) {
            intent.data?.let { openEppUri(it) }
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // Menu
    // ─────────────────────────────────────────────────────────────────────

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        R.id.action_open   -> { filePicker.launch("*/*"); true }
        R.id.action_share  -> { shareCurrentFile(); true }
        R.id.action_about  -> { showAboutDialog(); true }
        else               -> super.onOptionsItemSelected(item)
    }

    // ─────────────────────────────────────────────────────────────────────
    // WebView setup
    // ─────────────────────────────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        with(webView.settings) {
            javaScriptEnabled        = true
            allowFileAccess          = true
            @Suppress("DEPRECATION")
            allowFileAccessFromFileURLs = true
            domStorageEnabled        = true
            builtInZoomControls      = true
            displayZoomControls      = false
            useWideViewPort          = true
            loadWithOverviewMode     = true
        }

        webView.addJavascriptInterface(EppJsBridge(), "EppBridge")

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) {
                // If we have a queued file (e.g. intent before WebView was ready), inject it now
                currentUri?.let { injectEppSource(it) }
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // File loading
    // ─────────────────────────────────────────────────────────────────────

    private fun openEppUri(uri: Uri) {
        currentUri = uri
        progressBar.isVisible = true

        // Reset the viewer to show the loading spinner, then inject content
        webView.loadUrl("file:///android_asset/viewer.html")
        // injectEppSource() will be called from onPageFinished
    }

    private fun injectEppSource(uri: Uri) {
        try {
            val source = contentResolver.openInputStream(uri)?.use { stream ->
                stream.bufferedReader(Charsets.UTF_8).readText()
            } ?: run {
                showError("Could not read file.")
                return
            }

            // Safely encode the source as a JSON string so any quotes /
            // backslashes / newlines in the EPP text don't break the JS call.
            val jsonSource = try {
                // JSONObject.quote() wraps in double-quotes and escapes correctly
                JSONObject.quote(source)
            } catch (e: JSONException) {
                showError("Failed to encode file content: ${e.message}")
                return
            }

            // Call the loadEPP() function defined in viewer.html
            webView.evaluateJavascript("loadEPP($jsonSource);", null)
            progressBar.isVisible = false

        } catch (e: Exception) {
            progressBar.isVisible = false
            showError("Error reading file: ${e.message}")
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // Share
    // ─────────────────────────────────────────────────────────────────────

    private fun shareCurrentFile() {
        val uri = currentUri ?: run {
            Toast.makeText(this, "No file open", Toast.LENGTH_SHORT).show()
            return
        }
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, "Share EPP document"))
    }

    // ─────────────────────────────────────────────────────────────────────
    // Dialogs
    // ─────────────────────────────────────────────────────────────────────

    private fun showError(message: String) {
        runOnUiThread {
            progressBar.isVisible = false
            Toast.makeText(this, message, Toast.LENGTH_LONG).show()
        }
    }

    private fun showAboutDialog() {
        AlertDialog.Builder(this)
            .setTitle("EPP Viewer")
            .setMessage(
                "Easy Paper Package viewer\nv1.3\n\n" +
                "A lightweight viewer for .epp plain-text documents.\n\n" +
                "© 2026 Sourasish Das"
            )
            .setPositiveButton("OK", null)
            .show()
    }

    // ─────────────────────────────────────────────────────────────────────
    // JavaScript → Kotlin bridge
    // ─────────────────────────────────────────────────────────────────────

    inner class EppJsBridge {

        /** Called by viewer.html once a document has been parsed & rendered. */
        @JavascriptInterface
        fun onDocumentReady(title: String, pages: Int) {
            pageCount = pages
            runOnUiThread {
                val label = title.ifBlank { "EPP Document" }
                supportActionBar?.title    = label
                supportActionBar?.subtitle = if (pages > 1) "$pages pages" else null
                progressBar.isVisible      = false
            }
        }

        /** Called by viewer.html when parsing fails. */
        @JavascriptInterface
        fun onError(message: String) {
            runOnUiThread {
                progressBar.isVisible = false
                Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
            }
        }
    }
}
