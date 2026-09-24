package com.pinedaagencygroup.leads;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.IBinder;

import com.google.android.gms.tasks.Tasks;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.Source;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class LeadMonitorService extends Service {
    private static final String CH_MONITOR = "pag_monitor";
    private static final String CH_NEW = "pag_new_leads";
    private static final int FOREGROUND_ID = 4101;
    private ScheduledExecutorService executor;
    private SharedPreferences prefs;

    @Override
    public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences("pag_native", MODE_PRIVATE);
        createChannels();
        startForeground(FOREGROUND_ID, monitorNotification());
        executor = Executors.newSingleThreadScheduledExecutor();
        executor.scheduleWithFixedDelay(this::pollSafely, 3, 60, TimeUnit.SECONDS);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        boolean enabled = prefs.getBoolean("notifications", true);
        if (!enabled) {
            stopSelf();
            return START_NOT_STICKY;
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (executor != null) executor.shutdownNow();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = getSystemService(NotificationManager.class);

            NotificationChannel monitor = new NotificationChannel(
                    CH_MONITOR,
                    "PAG Leads activo",
                    NotificationManager.IMPORTANCE_LOW
            );
            monitor.setDescription("Mantiene activo el monitoreo privado de nuevos leads.");
            monitor.setSound(null, null);
            nm.createNotificationChannel(monitor);

            NotificationChannel leads = new NotificationChannel(
                    CH_NEW,
                    "Nuevos leads",
                    NotificationManager.IMPORTANCE_HIGH
            );
            leads.setDescription("Avisos cuando llega un nuevo lead a PAG Leads.");
            leads.enableVibration(true);
            nm.createNotificationChannel(leads);
        }
    }

    private Notification monitorNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CH_MONITOR)
                : new Notification.Builder(this);

        return b.setContentTitle("PAG Leads activo")
                .setContentText("Monitoreando nuevos leads cada minuto")
                .setSmallIcon(android.R.drawable.stat_notify_sync_noanim)
                .setOngoing(true)
                .setContentIntent(pi)
                .build();
    }

    private void pollSafely() {
        try {
            poll();
        } catch (Exception ignored) {
            // El monitor seguirá intentando en el siguiente ciclo.
        }
    }

    private void poll() throws Exception {
        if (!prefs.getBoolean("notifications", true)) return;
        // The legacy endpoint still accepts its old token. Never fetch it from a
        // suspended or unverified session; require a fresh server role check.
        if (!FirebasePushManager.ensureInitialized(this)) return;
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) { stopSelf(); return; }
        DocumentSnapshot profile = Tasks.await(FirebaseFirestore.getInstance()
                .collection("users").document(user.getUid()).get(Source.SERVER),
                20, TimeUnit.SECONDS);
        if (!profile.exists() || !"owner".equals(profile.getString("role")) ||
                !Boolean.TRUE.equals(profile.getBoolean("active")) ||
                Boolean.TRUE.equals(profile.getBoolean("suspended"))) {
            stopSelf();
            return;
        }

        String endpoint = prefs.getString("url", "");
        String token = prefs.getString("token", "");
        if (endpoint == null || endpoint.trim().isEmpty() || token == null || token.trim().isEmpty()) return;

        JSONObject body = new JSONObject();
        body.put("action", "list");
        body.put("token", token.trim());

        String response = post(endpoint.trim(), body.toString());
        JSONObject root = new JSONObject(response);
        if (!root.optBoolean("ok", false)) return;

        JSONArray leads = root.optJSONArray("leads");
        if (leads == null) leads = new JSONArray();

        Set<String> currentIds = new HashSet<>();
        for (int i = 0; i < leads.length(); i++) {
            JSONObject lead = leads.optJSONObject(i);
            if (lead == null) continue;
            String id = lead.optString("id", "");
            if (!id.isEmpty()) currentIds.add(id);
        }

        boolean initialized = prefs.getBoolean("monitor_initialized", false);
        Set<String> seenStored = prefs.getStringSet("seen_ids", Collections.emptySet());
        Set<String> seen = new HashSet<>(seenStored == null ? Collections.emptySet() : seenStored);

        if (!initialized) {
            seen.clear();
            seen.addAll(currentIds);
            saveSeen(seen);
            prefs.edit().putBoolean("monitor_initialized", true).apply();
            return;
        }

        for (int i = 0; i < leads.length(); i++) {
            JSONObject lead = leads.optJSONObject(i);
            if (lead == null) continue;
            String id = lead.optString("id", "");
            if (id.isEmpty() || seen.contains(id)) continue;

            String type = lead.optString("type", "agent");
            notifyLead(id, type);
            seen.add(id);
        }

        // Mantener un historial acotado y conservar todos los IDs actualmente visibles.
        if (seen.size() > 2500) {
            seen.clear();
            seen.addAll(currentIds);
        }
        saveSeen(seen);
    }

    private void saveSeen(Set<String> seen) {
        prefs.edit().putStringSet("seen_ids", new HashSet<>(seen)).apply();
    }

    private void notifyLead(String id, String type) {
        Intent open = new Intent(this, MainActivity.class);
        open.putExtra("lead_id", id);
        open.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        PendingIntent pi = PendingIntent.getActivity(
                this,
                Math.abs(id.hashCode()),
                open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        String title = "client".equals(type)
                ? "PAG Leads — Nuevo cliente"
                : "PAG Leads — Nuevo agente";

        String text = "Nuevo lead recibido. Toca para abrir PAG Leads.";

        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CH_NEW)
                : new Notification.Builder(this);

        Notification n = b.setContentTitle(title)
                .setContentText(text)
                .setSmallIcon(android.R.drawable.stat_notify_more)
                .setVisibility(Notification.VISIBILITY_PRIVATE)
                .setAutoCancel(true)
                .setContentIntent(pi)
                .build();

        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify(Math.abs(id.hashCode()), n);
    }

    private String post(String endpoint, String json) throws Exception {
        URL url = new URL(endpoint);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(20000);
        c.setInstanceFollowRedirects(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("Content-Type", "text/plain;charset=utf-8");
        c.setRequestProperty("Accept", "application/json");
        c.setDoOutput(true);

        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        try (OutputStream os = c.getOutputStream()) {
            os.write(bytes);
        }

        int code = c.getResponseCode();
        InputStream is = code >= 200 && code < 400 ? c.getInputStream() : c.getErrorStream();
        if (is == null) throw new IllegalStateException("Sin respuesta del endpoint");

        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
        }
        return sb.toString();
    }
}
