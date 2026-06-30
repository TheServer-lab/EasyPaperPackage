# Keep the JavaScript interface so WebView can call it after minification
-keepclassmembers class com.theserverlab.eppviewer.MainActivity$EppJsBridge {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebView JS interface annotations
-keepattributes JavascriptInterface
