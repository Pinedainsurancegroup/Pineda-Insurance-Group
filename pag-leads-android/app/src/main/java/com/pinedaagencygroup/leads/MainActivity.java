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
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

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
    private volatile int requestGeneration;
    private boolean resumed;
    private String viewUid;
    private FirebaseAuth.AuthStateListener accountWatch;
    private volatile int preferenceRevision;
    private RecruitmentSync recruitmentSync;
    private AgentWorkspace workspace;
    private boolean workspaceSelected = true;
    private final Map<String, Map<String,Object>> recruitmentContacts = new HashMap<>();
    private final Set<String> recruitmentIds = new HashSet<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Permit owner-requested screenshots in the isolated Staging app only.
        // Production and other packages continue to block screen capture.
        if (StagingPolicy.allowsScreenshots(getPackageName())) {
            getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        } else {
            getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        }
        // Keep the recent-apps preview blocked where Android supports it.
        if (Build.VERSION.SDK_INT >= 33) setRecentsScreenshotEnabled(false);
        authGate = new PAGAuthGate(this, new PAGAuthGate.Listener() {
            @Override public void onOwnerVerified() {
                if (!resumed) return;
                FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
                if (user == null) return;
                if (viewUid != null && !viewUid.equals(user.getUid())) discardRecruitmentView();
                viewUid = user.getUid();
                ownerVerified = true;
                // Preferences and token registration must not delay the first lead request.
                if (workspaceSelected) openWorkspace(); else openRecruitment();
                loadOperationalPreferences();
                requestNotificationPermissionIfNeeded();
            }

            @Override public void onAgentVerified(com.google.firebase.firestore.DocumentSnapshot profile) {
                if (!resumed) return;
                ownerVerified = false;
                discardRecruitmentView();
                viewUid = profile.getId();
                FirebasePushManager.initialize(MainActivity.this);
                requestNotificationPermissionIfNeeded();
                showWorkspace(profile);
            }

            @Override public void onAccessRevoked() {
                ownerVerified = false;
                closeWorkspace();
                stopService(new Intent(MainActivity.this, LeadMonitorService.class));
                setContentView(authGate.view());
                discardRecruitmentView();
            }
        });
        setContentView(authGate.view());
        if (FirebasePushManager.ensureInitialized(this)) {
            accountWatch = auth -> {
                FirebaseUser user = auth.getCurrentUser();
                if (viewUid != null && (user == null || !viewUid.equals(user.getUid()))) {
                    ownerVerified = false;
                    requestGeneration++;
                    setContentView(authGate.view());
                    closeWorkspace();
                    discardRecruitmentView();
                    if (resumed) authGate.verify();
                }
            };
            FirebaseAuth.getInstance().addAuthStateListener(accountWatch);
        }
    }

    private void closeWorkspace() {
        if (workspace != null) workspace.close(); workspace = null;
    }
    private void showWorkspace(com.google.firebase.firestore.DocumentSnapshot profile) {
        closeWorkspace();
        workspace = new AgentWorkspace(this, profile, () -> {
            if (!resumed || !ownerVerified) return;
            if (stagingBaseMissing()) { showStagingBaseMissing(); return; }
            closeWorkspace(); workspaceSelected = false; openRecruitment();
        });
        setContentView(workspace.view());
    }
    private void openWorkspace() {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (!resumed || !ownerVerified || user == null) return;
        final int generation = requestGeneration; final String uid = user.getUid();
        FirebaseFirestore.getInstance().collection("users").document(uid).get(Source.SERVER)
            .addOnCompleteListener(this, t -> {
                FirebaseUser latest = FirebaseAuth.getInstance().getCurrentUser();
                if (!resumed || !ownerVerified || generation != requestGeneration || latest == null || !uid.equals(latest.getUid())) return;
                if (t.isSuccessful() && t.getResult().exists()) showWorkspace(t.getResult());
                else authGate.verify();
            });
    }

    private void loadOperationalPreferences() {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) { ownerVerified = false; authGate.verify(); return; }
        String uid = user.getUid();
        final int revision = preferenceRevision;
        FirebaseFirestore.getInstance().collection("users").document(uid)
                .collection("preferences").document("operational").get(Source.SERVER)
                .addOnCompleteListener(this, task -> {
                    FirebaseUser current = FirebaseAuth.getInstance().getCurrentUser();
                    if (!ownerVerified || revision != preferenceRevision || current == null || !uid.equals(current.getUid())) return;
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
                    if (pageReady && webView != null)
                        webView.evaluateJavascript("window.PAGPreferencesChanged && window.PAGPreferencesChanged();", null);
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

    private boolean stagingBaseMissing() {
        return getResources().getBoolean(R.bool.pag_staging_build) &&
            getString(R.string.pag_owner_gateway_url).trim().isEmpty();
    }
    private void showStagingBaseMissing() {
        new android.app.AlertDialog.Builder(this).setTitle("Base de pruebas no configurada")
            .setMessage("Esta compilación no tiene un gateway de datos sintéticos. Puedes usar Reclutamiento asignado cuando sus reglas estén habilitadas en staging.")
            .setPositiveButton("Volver", null).show();
    }
    private void openRecruitment() {
        if (stagingBaseMissing()) {
            workspaceSelected = true;
            openWorkspace();
            showStagingBaseMissing();
            return;
        }
        FirebasePushManager.initialize(this);
        SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
        if (!getResources().getBoolean(R.bool.pag_qa_build) &&
                p.getBoolean("notifications", true) && !p.getString("url", "").isEmpty() &&
                !TokenVault.read(p).isEmpty()) {
            Intent monitor = new Intent(this, LeadMonitorService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(monitor);
            else startService(monitor);
        }
        if (webView != null) {
            setContentView(webView);
            webView.onResume();
            if (pageReady) resumePage();
            return;
        }

        webView = new WebView(this);
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setAllowFileAccessFromFileURLs(false);
        s.setAllowUniversalAccessFromFileURLs(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        // Read the previous origin with no native bridge and an inert document.
        final boolean[] migrating = {true};
        final String[] oldStorage = {"{}"};

        final androidx.webkit.WebViewAssetLoader assets = new androidx.webkit.WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new androidx.webkit.WebViewAssetLoader.AssetsPathHandler(this)).build();
        webView.setWebViewClient(new WebViewClient() {
            @Override public android.webkit.WebResourceResponse shouldInterceptRequest(WebView view, android.webkit.WebResourceRequest request) {
                android.webkit.WebResourceResponse response = assets.shouldInterceptRequest(request.getUrl());
                if (response != null) {
                    java.util.Map<String,String> headers = new java.util.HashMap<>();
                    headers.put("Content-Security-Policy", "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'");
                    response.setResponseHeaders(headers);
                    return response;
                }
                return new android.webkit.WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", java.util.Collections.emptyMap(), new java.io.ByteArrayInputStream(new byte[0]));
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if ("https://appassets.androidplatform.net/assets/index.html".equals(url)) return false;
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
                if (view != webView) return;
                if (migrating[0] && "file:///android_asset/index.html".equals(url)) {
                    migrating[0] = false;
                    view.evaluateJavascript("JSON.stringify(Object.fromEntries(Object.keys(localStorage).filter(k=>k==='pagov'||k==='pagset12'||k.startsWith('pagcloud:')).map(k=>[k,localStorage.getItem(k)])))", value -> {
                        if (view != webView) return;
                        try {
                            JSONObject stored = new JSONObject(new org.json.JSONTokener(value).nextValue().toString());
                            if (stored.has("pagset12")) {
                                JSONObject settings = new JSONObject(stored.getString("pagset12"));
                                String oldToken = settings.optString("tok", "");
                                SharedPreferences nativePrefs = getSharedPreferences("pag_native", MODE_PRIVATE);
                                if (!oldToken.isEmpty() && TokenVault.read(nativePrefs).isEmpty()) {
                                    if (!TokenVault.save(nativePrefs, oldToken)) { migrationFailed(view); return; }
                                    if (!nativePrefs.edit().putString("url", settings.optString("url", "")).commit()) { migrationFailed(view); return; }
                                }
                                settings.remove("tok"); settings.remove("url");
                                stored.put("pagset12", settings.toString());
                                view.evaluateJavascript("localStorage.setItem('pagset12'," + JSONObject.quote(settings.toString()) + ")", null);
                            }
                            oldStorage[0] = stored.toString();
                        }
                        catch (Exception ignored) { migrationFailed(view); return; }
                        view.addJavascriptInterface(new PAGNativeBridge(), "PAGNative");
                        view.loadUrl("https://appassets.androidplatform.net/assets/index.html");
                    });
                    return;
                }
                if (!"https://appassets.androidplatform.net/assets/index.html".equals(url)) return;
                String migration = "(()=>{const old=JSON.parse(" + JSONObject.quote(oldStorage[0]) + ");for(const k of Object.keys(old)){if(localStorage.getItem(k)===null)localStorage.setItem(k,old[k]);}return true;})()";
                view.evaluateJavascript(migration, result -> {
                    if (view != webView) return;
                    if (!"true".equals(result)) { migrationFailed(view); return; }
                    pageReady = true;
                    if (ownerVerified) resumePage();
                });
            }
        });

        // Asset URLs are not guaranteed to invoke shouldInterceptRequest.
        // Supply the inert migration document directly, retaining the old origin.
        webView.loadDataWithBaseURL("file:///android_asset/index.html",
                "<!doctype html><title>Migration</title>", "text/html", "UTF-8", null);
    }

    private void migrationFailed(WebView view) {
        if (view != webView) return;
        pageReady = false;
        view.removeJavascriptInterface("PAGNative");
        android.widget.TextView message = new android.widget.TextView(this);
        message.setText("No se pudo recuperar el almacenamiento local. Los datos originales se conservan. Cierre y abra la aplicación para reintentar; si continúa, contacte soporte.");
        message.setPadding(24, 24, 24, 24);
        setContentView(message);
    }

    private void resumePage() {
        boolean force = getIntent().getBooleanExtra("pag_refresh", false);
        getIntent().removeExtra("pag_refresh");
        webView.evaluateJavascript("window.PAGResume && window.PAGResume(" + force + ");", null);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (resumed && authGate.openInvitation(intent)) return;
        if (ownerVerified && pageReady && webView != null) resumePage();
    }

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        // Recheck against the server before showing data after every return to the app.
        ownerVerified = false;
        setContentView(authGate.view());
        if (!authGate.openInvitation(getIntent())) authGate.verify();
    }

    @Override
    protected void onPause() {
        resumed = false;
        ownerVerified = false;
        requestGeneration++;
        authGate.pause();
        closeWorkspace();
        stopRecruitmentSync();
        if (webView != null) {
            webView.evaluateJavascript("window.PAGSuspend && window.PAGSuspend();", null);
            webView.onPause();
        }
        setContentView(authGate.view());
        super.onPause();
    }

    @Override protected void onDestroy() {
        authGate.pause();
        closeWorkspace();
        if (accountWatch != null) FirebaseAuth.getInstance().removeAuthStateListener(accountWatch);
        discardRecruitmentView();
        super.onDestroy();
    }

    private void discardRecruitmentView() {
        stopRecruitmentSync();
        recruitmentIds.clear();
        recruitmentContacts.clear();
        if (webView == null) return;
        webView.stopLoading();
        webView.loadUrl("about:blank");
        webView.clearCache(true);
        webView.destroy();
        webView = null;
        pageReady = false;
        viewUid = null;
    }

    private URL legacyUrl() {
        if (getResources().getBoolean(R.bool.pag_staging_build)) return null;
        try {
            URL url = new URL(getSharedPreferences("pag_native", MODE_PRIVATE).getString("url", ""));
            if ("https".equals(url.getProtocol()) && "script.google.com".equals(url.getHost()) &&
                url.getUserInfo() == null && (url.getPort() == -1 || url.getPort() == 443) &&
                url.getPath().matches("/macros/s/[^/]+/exec")) return url;
        } catch (Exception ignored) {}
        return null;
    }

    private URL gatewayUrl() {
        try {
            URL url = new URL(getString(R.string.pag_owner_gateway_url).trim());
            if ("https".equals(url.getProtocol()) && "script.google.com".equals(url.getHost()) &&
                    url.getPath().matches("/macros/s/[^/]+/exec")) return url;
        } catch (Exception ignored) {}
        return null;
    }

    private void deliverRecruitment(WebView requestView, int generation, String requestId, boolean ok, String payload) {
        if (!ownerVerified || requestGeneration != generation || webView != requestView || !pageReady) return;
        if (ok) {
            try {
                JSONArray leads = new JSONObject(payload).optJSONArray("leads");
                if (leads != null) {
                    recruitmentIds.clear();
                    for (int i = 0; i < leads.length(); i++) {
                        String id = leads.getJSONObject(i).optString("stableId", "");
                        if (RecruitmentSync.validId(id)) {
                            recruitmentIds.add(id);
                            JSONObject lead = leads.getJSONObject(i);
                            Map<String,Object> contact = new HashMap<>();
                            contact.put("name", lead.optString("name", "")); contact.put("phone", lead.optString("phone", ""));
                            contact.put("email", lead.optString("email", "")); contact.put("region", lead.optString("state", ""));
                            recruitmentContacts.put(id, contact);
                        }
                    }
                }
            } catch (Exception ignored) {}
        }
        requestView.evaluateJavascript("window.PAGNativeRecruitmentResult && " +
                "window.PAGNativeRecruitmentResult(" + JSONObject.quote(requestId) + "," +
                ok + "," + JSONObject.quote(payload) + ");", null);
    }

    // Apps Script ContentService redirects its JSON response to a Google content host.
    // The ID token stays exclusively in the initial POST body, never in a redirect.
    static String readGatewayResponse(HttpURLConnection initial) throws Exception {
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

    private void stopRecruitmentSync() {
        if (recruitmentSync != null) recruitmentSync.stop();
        recruitmentSync = null;
    }
    private RecruitmentSync syncClient() {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (!ownerVerified || user == null || !pageReady || webView == null) return null;
        if (recruitmentSync == null) {
            String device = getSharedPreferences("pag_native", MODE_PRIVATE).getString("firebase_device_id", "");
            if (device.length() < 16) return null;
            recruitmentSync = new RecruitmentSync(user.getUid(), device);
        }
        return recruitmentSync;
    }

    private class PAGNativeBridge {
        @JavascriptInterface public void openAgentWorkspace() {
            runOnUiThread(() -> { if (resumed && ownerVerified) { workspaceSelected = true; openWorkspace(); } });
        }
        @JavascriptInterface public void prepareAssignment(String id) {
            runOnUiThread(() -> {
                if (!resumed || !ownerVerified || !recruitmentContacts.containsKey(id)) return;
                Map<String,Object> contact = new HashMap<>(recruitmentContacts.get(id));
                FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser(); if (user == null) return;
                final int generation = requestGeneration;
                FirebaseFirestore.getInstance().collection("users").document(user.getUid()).get(Source.SERVER)
                    .addOnCompleteListener(MainActivity.this, t -> {
                        if (!resumed || !ownerVerified || generation != requestGeneration || !t.isSuccessful() || FirebaseAuth.getInstance().getCurrentUser() == null || !user.getUid().equals(FirebaseAuth.getInstance().getCurrentUser().getUid()) || t.getResult() == null || !t.getResult().exists()) return;
                        workspaceSelected = true; showWorkspace(t.getResult()); workspace.importRecruitment(contact, id);
                    });
            });
        }

        @JavascriptInterface public void configureOwnerPassword() {
            runOnUiThread(() -> {
                if (resumed && ownerVerified) authGate.configureOwnerPassword();
            });
        }
        @JavascriptInterface public String getSyncUid() {
            FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
            return ownerVerified && user != null ? user.getUid() : "";
        }
        @JavascriptInterface public String newSyncId() { return UUID.randomUUID().toString(); }
        @JavascriptInterface public void watchRecruitmentState(String serializedIds) {
            runOnUiThread(() -> {
                RecruitmentSync client = syncClient(); if (client == null) return;
                final WebView view = webView; final int generation = requestGeneration;
                try {
                    JSONArray input = new JSONArray(serializedIds);
                    if (input.length() > 500) throw new IllegalArgumentException();
                    ArrayList<String> ids = new ArrayList<>();
                    for (int i = 0; i < input.length(); i++) {
                        String id = input.getString(i);
                        if (!recruitmentIds.contains(id) || ids.contains(id)) throw new IllegalArgumentException();
                        ids.add(id);
                    }
                    client.watch(ids, payload -> {
                        if (ownerVerified && generation == requestGeneration && webView == view && pageReady)
                            view.evaluateJavascript("window.PAGCloudState && window.PAGCloudState(" + payload + ");", null);
                    });
                } catch (Exception ignored) {
                    if (ownerVerified && webView == view)
                        view.evaluateJavascript("window.PAGCloudState && window.PAGCloudState({error:true,all:true});", null);
                }
            });
        }
        @JavascriptInterface public void requestLeadSync(String serialized, String requestId) {
            if (requestId == null || !requestId.matches("[0-9]{1,12}") || serialized == null || serialized.length() > 24000) return;
            runOnUiThread(() -> {
                RecruitmentSync client = syncClient();
                final WebView view = webView; final int generation = requestGeneration;
                RecruitmentSync.Reply reply = (ok, payload) -> {
                    if (ownerVerified && generation == requestGeneration && view != null && webView == view && pageReady)
                        view.evaluateJavascript("window.PAGSyncResult && window.PAGSyncResult(" + JSONObject.quote(requestId) + "," + ok + "," + payload + ");", null);
                };
                try {
                    JSONObject input = new JSONObject(serialized);
                    if (client == null || !recruitmentIds.contains(input.getString("leadId"))) throw new IllegalArgumentException();
                    if ("save".equals(input.optString("action"))) client.save(input, reply);
                    else if ("history".equals(input.optString("action"))) client.history(input, reply);
                    else throw new IllegalArgumentException();
                } catch (Exception ignored) { reply.done(false, new JSONObject()); }
            });
        }

        @JavascriptInterface
        public boolean hasOwnerGateway() {
            return ownerVerified && (gatewayUrl() != null || (legacyUrl() != null && !TokenVault.read(getSharedPreferences("pag_native", MODE_PRIVATE)).isEmpty()));
        }

        @JavascriptInterface
        public boolean isSessionActive() { return ownerVerified && pageReady; }

        @JavascriptInterface
        public void requestRecruitment(String action, String requestId) {
            if (!ownerVerified || webView == null || !pageReady ||
                    !("ping".equals(action) || "list".equals(action)) ||
                    requestId == null || !requestId.matches("[0-9]{1,12}")) return;
            final WebView requestView = webView;
            final int generation = requestGeneration;
            final boolean legacy = gatewayUrl() == null;
            final URL endpoint = legacy ? legacyUrl() : gatewayUrl();
            FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
            if (endpoint == null || user == null) {
                runOnUiThread(() -> deliverRecruitment(requestView, generation, requestId, false, "{}"));
                return;
            }
            final String uid = user.getUid();
            user.getIdToken(false).addOnCompleteListener(MainActivity.this::runOnUiThread, task -> {
                FirebaseUser current = FirebaseAuth.getInstance().getCurrentUser();
                if (!ownerVerified || generation != requestGeneration || current == null || !uid.equals(current.getUid()) ||
                        !task.isSuccessful() || task.getResult() == null ||
                        task.getResult().getToken() == null) {
                    deliverRecruitment(requestView, generation, requestId, false, "{}"); return;
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
                        connection.setReadTimeout(20000);
                        connection.setDoOutput(true);
                        connection.setInstanceFollowRedirects(false);
                        JSONObject request = new JSONObject();
                        request.put("action", action);
                        request.put(legacy ? "token" : "idToken", legacy ? TokenVault.read(getSharedPreferences("pag_native", MODE_PRIVATE)) : token);
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
                            deliverRecruitment(requestView, generation, requestId, success, payload);
                    });
                }).start();
            });
        }

        @JavascriptInterface
        public String getBuildLabel() {
            return getResources().getBoolean(R.bool.pag_qa_build)
                    ? "PAG LEADS v1.9 · PRUEBA AGENTES QA2" : "PAG LEADS v1.9 · CANDIDATA AGENTES";
        }

        @JavascriptInterface
        public String getSettingsJson() {
            if (!ownerVerified) return "{}";
            SharedPreferences p = getSharedPreferences("pag_native", MODE_PRIVATE);
            try {
                JSONObject j = new JSONObject();
                j.put("url", p.getString("url", ""));
                // Credentials stay native; JavaScript receives only configuration status.
                j.put("auto", p.getBoolean("auto", true));
                j.put("notify", p.getBoolean("notifications", true));
                j.put("configured",
                        !p.getString("url", "").trim().isEmpty() &&
                        !TokenVault.read(p).trim().isEmpty());
                return j.toString();
            } catch (Exception ignored) {
                return "{}";
            }
        }

        @JavascriptInterface
        public void savePreferences(boolean autoRefresh, boolean notificationsEnabled) {
            if (!ownerVerified) return;
            preferenceRevision++;
            SharedPreferences prefs = getSharedPreferences("pag_native", MODE_PRIVATE);
            prefs.edit().putBoolean("auto", autoRefresh)
                    .putBoolean("notifications", notificationsEnabled).apply();
            saveOperationalPreferences(autoRefresh, notificationsEnabled);
            runOnUiThread(() -> {
                if (getResources().getBoolean(R.bool.pag_qa_build)) return;
                if (notificationsEnabled && !prefs.getString("url", "").isEmpty()
                        && !TokenVault.read(prefs).isEmpty()) {
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
            if (!TokenVault.save(p, token == null ? "" : token.trim())) return;
            p.edit()
                .putString("url", url == null ? "" : url.trim())
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
