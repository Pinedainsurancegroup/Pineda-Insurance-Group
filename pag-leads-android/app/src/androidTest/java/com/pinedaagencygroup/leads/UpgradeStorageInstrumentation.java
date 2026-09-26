package com.pinedaagencygroup.leads;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** Runs only in a separate test APK with synthetic CI data; never shipped. */
public class UpgradeStorageInstrumentation extends Instrumentation {
    public static final class ClosedGate {
        @JavascriptInterface public boolean isSessionActive() { return false; }
    }
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
    private void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            Context context = getTargetContext();
            require(context.getPackageName().equals("com.pinedaagencygroup.leads"), "wrong target");
            require(context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionCode == 14,
                    "candidate version not installed");
            SharedPreferences prefs = context.getSharedPreferences("pag_native", Context.MODE_PRIVATE);
            require(prefs.getString("url", "").equals("https://example.invalid/legacy"), "private URL lost");
            require(prefs.getString("token", "").equals("synthetic-upgrade-only"), "legacy credential lost");
            require(!prefs.getBoolean("auto", true) && prefs.getBoolean("notifications", false), "preferences lost");
            require(prefs.getBoolean("monitor_initialized", false), "monitor baseline lost");
            require(prefs.getStringSet("seen_ids", java.util.Collections.emptySet()).size() == 2, "seen IDs lost");
            int resource = context.getResources().getIdentifier("pag_owner_gateway_url", "string", context.getPackageName());
            require(context.getString(resource).startsWith("https://script.google.com/macros/s/"), "release gateway missing");

            CountDownLatch finished = new CountDownLatch(1);
            AtomicReference<String> actual = new AtomicReference<>();
            AtomicReference<WebView> browser = new AtomicReference<>();
            runOnMainSync(() -> {
                WebView view = new WebView(context); browser.set(view);
                view.getSettings().setJavaScriptEnabled(true);
                view.getSettings().setDomStorageEnabled(true);
                view.getSettings().setAllowFileAccess(true);
                // Production page stays behind a closed test gate; no Firebase/network access.
                view.addJavascriptInterface(new ClosedGate(), "PAGNative");
                view.setWebViewClient(new WebViewClient() {
                    @Override public void onPageFinished(WebView v, String url) {
                        v.evaluateJavascript("[localStorage.getItem('pagov'),localStorage.getItem('pagset12')]",
                                value -> { actual.set(value); finished.countDown(); });
                    }
                });
                view.loadUrl("file:///android_asset/index.html");
            });
            require(finished.await(30, TimeUnit.SECONDS), "WebView storage check timed out");
            JSONArray storage = new JSONArray(actual.get());
            JSONObject notes = new JSONObject(storage.getString(0)).getJSONObject("PAG-A-2");
            require(notes.getString("status").equals("Seguimiento"), "local state lost");
            require(notes.getString("note").equals("Nota local v1.7 — acción"), "local note changed");
            require(notes.getString("updatedAt").equals("2026-09-25T22:37:00Z"), "local timestamp changed");
            JSONObject settings = new JSONObject(storage.getString(1));
            require(settings.getString("tok").equals("synthetic-upgrade-only"), "WebView settings lost");
            require(!settings.getBoolean("auto") && settings.getBoolean("notify"), "WebView preferences lost");
            runOnMainSync(() -> browser.get().destroy());
            result.putString("stream", "PAG_UPGRADE_STORAGE_PASS: v8 to v14; native settings, monitor state, WebView notes and preferences retained.\n");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("stream", "PAG_UPGRADE_STORAGE_FAIL: " + error.getClass().getSimpleName() + ": " + error.getMessage());
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
