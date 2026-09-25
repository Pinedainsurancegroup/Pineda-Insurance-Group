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

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.FieldValue;
import com.google.firebase.firestore.Source;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends Activity {
    private static final int REQ_NOTIFICATIONS = 1401;
    private WebView webView;
    private boolean pageReady = false;
    private PAGAuthGate authGate;
    private volatile boolean ownerVerified = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        authGate = new PAGAuthGate(this, new PAGAuthGate.Listener() {
            @Override public void onOwnerVerified() {
                ownerVerified = true;
                requestNotificationPermissionIfNeeded();
                loadOperationalPreferences();
            }

            @Override public void onAccessRevoked() {
                ownerVerified = false;
                stopService(new Intent(MainActivity.this, LeadMonitorService.class));
                setContentView(authGate.view());
                discardRecruitmentView();
            }
        });
        setContentView(authGate.view());
    }

    private void loadOperationalPreferences() {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) { ownerVerified = false; authGate.verify(); return; }
        String uid = user.getUid();
        FirebaseFirestore.getInstance().collection("users").document(uid)
                .collection("preferences").document("operational").get(Source.SERVER)
                .addOnCompleteListener(this, task -> {
                    FirebaseUser current = FirebaseAuth.getInstance().getCurrentUser();
                    if (!ownerVerified || current == null || !uid.equals(current.getUid())) return;
                    SharedPreferences prefs = getSharedPreferences("pag_native", MODE_PRIVATE);
                    if (task.isSuccessful() && task.getResult() != null) {
                        if (task.getResult().exists()) {
                            Boolean auto = task.getResult().getBoolean("autoRefresh");
                            Boolean notifications = task.getResult().getBoolean("notifications");
                            if (auto != null && notifications != null) {
                                prefs.edit().putBoolean("auto", auto)
                                        .putBoolean("notifications", notifications).apply();
                            }
                        } else {
                            // First login transfers only nonsecret operational preferences.
                            saveOperationalPreferences(prefs.getBoolean("auto", true),
                                    prefs.getBoolean("notifications", true));
                        }
                    }
                    openRecruitment();
                });
    }

    private void saveOperationalPreferences(boolean auto, boolean notifications) {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (!ownerVerified || user == null) return;
        Map<String, Object> fields = new HashMap<>();
        fields.put("autoRefresh", auto);
        fields.put("notifications", notifications);
        fields.put("updatedAt", FieldValue.serverTimestamp());
        FirebaseFirestore.getInstance().collection("users").document(user.getUid())
                .collection("preferences").document("operational").set(fields);
    }

    private void openRecruitment() {
        FirebasePushManager.initialize(this);
        SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
        if (!getResources().getBoolean(R.bool.pag_qa_build) &&
                p.getBoolean("notifications", true) && !p.getString("url", "").isEmpty() &&
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
                if ("file:///android_asset/index.html".equals(url)) return false;
                if (url == null) return true;
                Uri target = Uri.parse(url);
                String scheme = target.getScheme();
                // Never let remote pages acquire the PAGNative bridge or private credentials.
                if ("tel".equals(scheme) || "mailto".equals(scheme) ||
                        "https".equals(scheme)) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, target));
                    } catch (Exception ignored) {}
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (!ownerVerified || view != webView || !"file:///android_asset/index.html".equals(url)) return;
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
        ownerVerified = false;
        setContentView(authGate.view());
        discardRecruitmentView();
        authGate.verify();
    }

    @Override
    protected void onPause() {
        ownerVerified = false;
        super.onPause();
    }

    private void discardRecruitmentView() {
        if (webView == null) return;
        webView.stopLoading();
        webView.loadUrl("about:blank");
        webView.clearCache(true);
        webView.destroy();
        webView = null;
        pageReady = false;
    }

    private URL gatewayUrl() {
        try {
            URL url = new URL(getString(R.string.pag_owner_gateway_url).trim());
            if ("https".equals(url.getProtocol()) && "script.google.com".equals(url.getHost()) &&
                    url.getPath().matches("/macros/s/[^/]+/exec")) return url;
        } catch (Exception ignored) {}
        return null;
    }

    private void deliverRecruitment(WebView requestView, String requestId, boolean ok, String payload) {
        if (!ownerVerified || webView != requestView || !pageReady) return;
        requestView.evaluateJavascript("window.PAGNativeRecruitmentResult && " +
                "window.PAGNativeRecruitmentResult(" + JSONObject.quote(requestId) + "," +
                ok + "," + JSONObject.quote(payload) + ");", null);
    }

    // Apps Script ContentService redirects its JSON response to a Google content host.
    // The ID token stays exclusively in the initial POST body, never in a redirect.
    private String readGatewayResponse(HttpURLConnection initial) throws Exception {
        HttpURLConnection connection = initial;
        try {
            for (int redirect = 0; redirect <= 2; redirect++) {
                int status = connection.getResponseCode();
                if (status == 200) {
                    try (InputStream in = connection.getInputStream();
                         ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = in.read(buffer)) != -1) {
                            if (output.size() + read > 2_000_000) throw new IllegalStateException("Response too large");
                            output.write(buffer, 0, read);
                        }
                        return output.toString("UTF-8");
                    }
                }
                if (status != 302 && status != 303) throw new IllegalStateException("Gateway unavailable");
                URL next = new URL(connection.getHeaderField("Location"));
                if (!"https".equals(next.getProtocol()) ||
                        !("script.googleusercontent.com".equals(next.getHost()) ||
                                "script.google.com".equals(next.getHost())))
                    throw new IllegalStateException("Unexpected redirect");
                connection.disconnect();
                connection = (HttpURLConnection) next.openConnection();
                connection.setInstanceFollowRedirects(false);
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(10000);
            }
            throw new IllegalStateException("Too many redirects");
        } finally {
            connection.disconnect();
        }
    }

    private class PAGNativeBridge {
        @JavascriptInterface
        public boolean hasOwnerGateway() {
            return ownerVerified && gatewayUrl() != null;
        }

        @JavascriptInterface
        public void requestRecruitment(String action, String requestId) {
            if (!ownerVerified || webView == null || !pageReady ||
                    !("ping".equals(action) || "list".equals(action)) ||
                    requestId == null || !requestId.matches("[0-9]{1,12}")) return;
            final WebView requestView = webView;
            URL endpoint = gatewayUrl();
            FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
            if (endpoint == null || user == null) {
                runOnUiThread(() -> deliverRecruitment(requestView, requestId, false, "{}"));
                return;
            }
            final String uid = user.getUid();
            user.getIdToken(true).addOnCompleteListener(MainActivity.this, task -> {
                FirebaseUser current = FirebaseAuth.getInstance().getCurrentUser();
                if (!ownerVerified || current == null || !uid.equals(current.getUid()) ||
                        !task.isSuccessful() || task.getResult() == null ||
                        task.getResult().getToken() == null) {
                    deliverRecruitment(requestView, requestId, false, "{}"); return;
                }
                final String token = task.getResult().getToken();
                new Thread(() -> {
                    String response = "{}";
                    boolean ok = false;
                    HttpURLConnection connection = null;
                    try {
                        connection = (HttpURLConnection) endpoint.openConnection();
                        connection.setRequestMethod("POST");
                        connection.setRequestProperty("Content-Type", "text/plain;charset=utf-8");
                        connection.setConnectTimeout(10000);
                        connection.setReadTimeout(10000);
                        connection.setDoOutput(true);
                        connection.setInstanceFollowRedirects(false);
                        JSONObject request = new JSONObject();
                        request.put("action", action);
                        request.put("idToken", token);
                        byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                        connection.setFixedLengthStreamingMode(body.length);
                        try (OutputStream out = connection.getOutputStream()) { out.write(body); }
                        response = readGatewayResponse(connection);
                        ok = new JSONObject(response).optBoolean("ok", false);
                    } catch (Exception ignored) {
                        // No credentials, server data or private URL in logs.
                    } finally {
                        if (connection != null) connection.disconnect();
                    }
                    final boolean success = ok;
                    final String payload = response;
                    runOnUiThread(() -> {
                        FirebaseUser latest = FirebaseAuth.getInstance().getCurrentUser();
                        if (ownerVerified && latest != null && uid.equals(latest.getUid()))
                            deliverRecruitment(requestView, requestId, success, payload);
                    });
                }).start();
            });
        }

        @JavascriptInterface
        public String getBuildLabel() {
            return getResources().getBoolean(R.bool.pag_qa_build)
                    ? "PAG LEADS v1.8 QA" : "PAG LEADS v1.8";
        }

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
        public void savePreferences(boolean autoRefresh, boolean notificationsEnabled) {
            if (!ownerVerified) return;
            SharedPreferences prefs = getSharedPreferences("pag_native", MODE_PRIVATE);
            prefs.edit().putBoolean("auto", autoRefresh)
                    .putBoolean("notifications", notificationsEnabled).apply();
            saveOperationalPreferences(autoRefresh, notificationsEnabled);
            runOnUiThread(() -> {
                if (getResources().getBoolean(R.bool.pag_qa_build)) return;
                if (notificationsEnabled && !prefs.getString("url", "").isEmpty()
                        && !prefs.getString("token", "").isEmpty()) {
                    requestNotificationPermissionIfNeeded();
                    Intent monitor = new Intent(MainActivity.this, LeadMonitorService.class);
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(monitor);
                    else startService(monitor);
                } else {
                    stopService(new Intent(MainActivity.this, LeadMonitorService.class));
                }
            });
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
            saveOperationalPreferences(autoRefresh, notificationsEnabled);

            runOnUiThread(() -> {
                if (notificationsEnabled && !getResources().getBoolean(R.bool.pag_qa_build)) {
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
        if (ownerVerified && webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
