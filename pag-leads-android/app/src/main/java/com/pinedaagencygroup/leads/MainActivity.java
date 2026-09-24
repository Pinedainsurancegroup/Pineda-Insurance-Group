package com.pinedaagencygroup.leads;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

public class MainActivity extends Activity {
    private static final int REQ_NOTIFICATIONS = 1401;
    private WebView webView;
    private boolean pageReady = false;
    private PAGAuthGate authGate;
    private boolean ownerVerified = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        authGate = new PAGAuthGate(this, new PAGAuthGate.Listener() {
            @Override public void onOwnerVerified() {
                ownerVerified = true;
                openRecruitment();
            }

            @Override public void onAccessRevoked() {
                ownerVerified = false;
                stopService(new Intent(MainActivity.this, LeadMonitorService.class));
                if (webView != null) {
                    webView.loadUrl("about:blank");
                    webView.clearCache(true);
                    webView = null;
                    pageReady = false;
                }
                setContentView(authGate.view());
            }
        });
        setContentView(authGate.view());
    }

    private void openRecruitment() {
        FirebasePushManager.initialize(this);
        SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
        if (p.getBoolean("notifications", true) && !p.getString("url", "").isEmpty() &&
                !p.getString("token", "").isEmpty()) {
            Intent monitor = new Intent(this, LeadMonitorService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(monitor);
            else startService(monitor);
        }
        if (webView != null) {
            setContentView(webView);
            if (pageReady) webView.evaluateJavascript("window.PAGAutoStart && window.PAGAutoStart();", null);
            return;
        }

        webView = new WebView(this);
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);

        webView.addJavascriptInterface(new PAGNativeBridge(), "PAGNative");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url == null) return false;
                if (url.startsWith("tel:") || url.startsWith("mailto:") ||
                    url.startsWith("https://wa.me/") || url.startsWith("https://api.whatsapp.com/")) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                    } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                pageReady = true;
                view.evaluateJavascript("window.PAGAutoStart && window.PAGAutoStart();", null);
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Recheck against the server before showing data after every return to the app.
        setContentView(authGate.view());
        authGate.verify();
    }

    private class PAGNativeBridge {
        @JavascriptInterface
        public String getSettingsJson() {
            if (!ownerVerified) return "{}";
            SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
            try {
                JSONObject j = new JSONObject();
                j.put("url", p.getString("url", ""));
                j.put("tok", p.getString("token", ""));
                j.put("auto", p.getBoolean("auto", true));
                j.put("notify", p.getBoolean("notifications", true));
                j.put("configured",
                        !p.getString("url", "").trim().isEmpty() &&
                        !p.getString("token", "").trim().isEmpty());
                return j.toString();
            } catch (Exception ignored) {
                return "{}";
            }
        }

        @JavascriptInterface
        public void saveSettings(String url, String token, boolean autoRefresh, boolean notificationsEnabled) {
            if (!ownerVerified) return;
            SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
            p.edit()
                .putString("url", url == null ? "" : url.trim())
                .putString("token", token == null ? "" : token.trim())
                .putBoolean("auto", autoRefresh)
                .putBoolean("notifications", notificationsEnabled)
                .apply();

            FirebasePushManager.syncRegistration(MainActivity.this);

            runOnUiThread(() -> {
                if (notificationsEnabled) {
                    requestNotificationPermissionIfNeeded();
                    Intent i = new Intent(MainActivity.this, LeadMonitorService.class);
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(i);
                    else startService(i);
                } else {
                    stopService(new Intent(MainActivity.this, LeadMonitorService.class));
                }
            });
        }
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFICATIONS);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
