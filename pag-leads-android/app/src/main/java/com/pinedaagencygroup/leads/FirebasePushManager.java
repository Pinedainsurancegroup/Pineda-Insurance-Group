package com.pinedaagencygroup.leads;

import android.content.Context;
import android.content.SharedPreferences;

import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.FieldValue;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public final class FirebasePushManager {
    private static final String PREFS = "pag_native";
    private static final String KEY_PENDING = "pending_fcm_token";
    private static final String KEY_DEVICE_ID = "firebase_device_id";
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
            registerFirestoreAsync(app, pending.trim());
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
        registerFirestoreAsync(app, fcmToken.trim());
    }

    public static boolean ensureInitialized(Context context) {
        if (!initialized) initialized = initFirebase(context.getApplicationContext());
        return initialized;
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

    private static void registerFirestoreAsync(Context context, String fcmToken) {
        // This is only a request; a trusted administrator must approve devices
        // before a sender may use them. Never send tokens to the legacy API.
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) return;
        SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String deviceId = p.getString(KEY_DEVICE_ID, "");
        if (deviceId == null || deviceId.isEmpty()) {
            deviceId = UUID.randomUUID().toString();
            p.edit().putString(KEY_DEVICE_ID, deviceId).apply();
        }
        Map<String, Object> request = new HashMap<>();
        request.put("fcmToken", fcmToken);
        request.put("platform", "android");
        request.put("appVersion", "1.8");
        request.put("updatedAt", FieldValue.serverTimestamp());
        FirebaseFirestore.getInstance().collection("users").document(user.getUid())
                .collection("deviceRequests").document(deviceId).set(request)
                .addOnSuccessListener(unused -> {
                    SharedPreferences current = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
                    // Do not discard a newer token delivered while the write was pending.
                    if (fcmToken.equals(current.getString(KEY_PENDING, ""))) {
                        current.edit().remove(KEY_PENDING).apply();
                    }
                });
    }
}
