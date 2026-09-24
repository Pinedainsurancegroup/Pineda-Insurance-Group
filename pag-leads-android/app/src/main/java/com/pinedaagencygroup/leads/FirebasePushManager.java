package com.pinedaagencygroup.leads;

import android.content.Context;
import android.content.SharedPreferences;

import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public final class FirebasePushManager {
    private static final String PREFS = "pag_native";
    private static final String KEY_PENDING = "pending_fcm_token";
    private static volatile boolean initialized = false;

    private FirebasePushManager() {}

    public static void initialize(Context context) {
        Context app = context.getApplicationContext();
        if (!initialized) {
            initialized = initFirebase(app);
        }
        if (!initialized) return;

        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null) return;
            saveAndRegister(app, task.getResult());
        });
    }

    public static void syncRegistration(Context context) {
        Context app = context.getApplicationContext();
        if (!initialized) initialized = initFirebase(app);
        if (!initialized) return;

        SharedPreferences p = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String pending = p.getString(KEY_PENDING, "");
        if (pending != null && !pending.trim().isEmpty()) {
            registerAsync(app, pending.trim());
        } else {
            FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
                if (!task.isSuccessful() || task.getResult() == null) return;
                saveAndRegister(app, task.getResult());
            });
        }
    }

    public static void saveAndRegister(Context context, String fcmToken) {
        if (fcmToken == null || fcmToken.trim().isEmpty()) return;
        Context app = context.getApplicationContext();
        app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString(KEY_PENDING, fcmToken.trim()).apply();
        registerAsync(app, fcmToken.trim());
    }

    private static boolean initFirebase(Context context) {
        try {
            if (!FirebaseApp.getApps(context).isEmpty()) return true;

            String projectId = context.getString(R.string.pag_firebase_project_id).trim();
            String appId = context.getString(R.string.pag_firebase_application_id).trim();
            String apiKey = context.getString(R.string.pag_firebase_api_key).trim();
            String senderId = context.getString(R.string.pag_firebase_sender_id).trim();

            if (projectId.isEmpty() || appId.isEmpty() || apiKey.isEmpty() || senderId.isEmpty()) {
                return false;
            }

            FirebaseOptions options = new FirebaseOptions.Builder()
                    .setProjectId(projectId)
                    .setApplicationId(appId)
                    .setApiKey(apiKey)
                    .setGcmSenderId(senderId)
                    .build();
            FirebaseApp.initializeApp(context, options);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static void registerAsync(Context context, String fcmToken) {
        SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String endpoint = p.getString("url", "");
        String apiToken = p.getString("token", "");
        if (endpoint == null || endpoint.trim().isEmpty() ||
            apiToken == null || apiToken.trim().isEmpty()) {
            return;
        }

        new Thread(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("action", "registerDevice");
                body.put("token", apiToken.trim());
                body.put("deviceToken", fcmToken);
                body.put("platform", "android");
                body.put("appVersion", "1.8");

                JSONObject response = new JSONObject(post(endpoint.trim(), body.toString()));
                if (response.optBoolean("ok", false)) {
                    context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                            .edit().remove(KEY_PENDING).apply();
                }
            } catch (Exception ignored) {}
        }, "PAG-FCM-register").start();
    }

    private static String post(String endpoint, String json) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(endpoint).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(20000);
        c.setInstanceFollowRedirects(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("Content-Type", "text/plain;charset=utf-8");
        c.setRequestProperty("Accept", "application/json");
        c.setDoOutput(true);

        try (OutputStream os = c.getOutputStream()) {
            os.write(json.getBytes(StandardCharsets.UTF_8));
        }

        int code = c.getResponseCode();
        InputStream is = code >= 200 && code < 400 ? c.getInputStream() : c.getErrorStream();
        if (is == null) throw new IllegalStateException("Sin respuesta");

        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
        }
        return sb.toString();
    }
}
