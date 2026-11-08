package com.pimflextv.next;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.Environment;
import android.os.IBinder;

import androidx.core.app.NotificationCompat;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class RecordingService extends Service {
    public static final String ACTION_START = "com.pimflextv.next.action.START_RECORDING";
    public static final String ACTION_STOP = "com.pimflextv.next.action.STOP_RECORDING";
    public static final String EXTRA_URL = "stream_url";
    public static final String EXTRA_TITLE = "stream_title";

    private static final String CHANNEL_ID = "pimflex_recording";
    private static final int NOTIFICATION_ID = 7301;

    private static volatile boolean running = false;
    private static volatile String currentFilePath = "";
    private static volatile String currentTitle = "";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private volatile HttpURLConnection connection;

    public static boolean isRunning() {
        return running;
    }

    public static String getCurrentFilePath() {
        return currentFilePath;
    }

    public static String getCurrentTitle() {
        return currentTitle;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? "" : intent.getAction();
        if (ACTION_STOP.equals(action)) {
            stopCurrentRecording();
            stopSelf();
            return START_NOT_STICKY;
        }

        if (ACTION_START.equals(action)) {
            if (running) return START_NOT_STICKY;

            String url = intent.getStringExtra(EXTRA_URL);
            String title = intent.getStringExtra(EXTRA_TITLE);
            if (url == null || url.trim().isEmpty()) {
                stopSelf();
                return START_NOT_STICKY;
            }
            currentTitle = title == null || title.trim().isEmpty() ? "PIMFLEX TV" : title.trim();
            startForeground(NOTIFICATION_ID, buildNotification(currentTitle));
            running = true;
            executor.execute(() -> record(url, currentTitle));
        }
        return START_NOT_STICKY;
    }

    private void record(String url, String title) {
        HttpURLConnection conn = null;
        try {
            File movies = getExternalFilesDir(Environment.DIRECTORY_MOVIES);
            if (movies == null) throw new IllegalStateException("Storage unavailable");
            File dir = new File(movies, "Recordings");
            if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Cannot create Recordings");

            String safe = title.replaceAll("[^A-Za-z0-9._ -]", "_").trim();
            if (safe.isEmpty()) safe = "Canal";
            String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            File file = new File(dir, safe + "_" + stamp + ".ts");
            currentFilePath = file.getAbsolutePath();

            conn = (HttpURLConnection) new URL(url).openConnection();
            connection = conn;
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(0);
            conn.setInstanceFollowRedirects(true);
            conn.setRequestProperty("User-Agent", "PIMFLEXTV/4.0.2 (Android)");
            int code = conn.getResponseCode();
            if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);

            try (BufferedInputStream in = new BufferedInputStream(conn.getInputStream());
                 FileOutputStream out = new FileOutputStream(file)) {
                byte[] buffer = new byte[64 * 1024];
                while (running) {
                    int read = in.read(buffer);
                    if (read < 0) break;
                    out.write(buffer, 0, read);
                }
                out.flush();
            }
        } catch (Exception ignored) {
        } finally {
            running = false;
            connection = null;
            if (conn != null) conn.disconnect();
            stopForeground(true);
            stopSelf();
        }
    }

    private void stopCurrentRecording() {
        running = false;
        HttpURLConnection conn = connection;
        connection = null;
        if (conn != null) {
            try { conn.disconnect(); } catch (Exception ignored) {}
        }
    }

    private Notification buildNotification(String title) {
        Intent stop = new Intent(this, RecordingService.class);
        stop.setAction(ACTION_STOP);
        PendingIntent stopIntent = PendingIntent.getService(
                this, 73, stop,
                PendingIntent.FLAG_UPDATE_CURRENT |
                        (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0));

        Intent open = new Intent(this, MainActivity.class);
        PendingIntent openIntent = PendingIntent.getActivity(
                this, 74, open,
                PendingIntent.FLAG_UPDATE_CURRENT |
                        (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0));

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_launcher_pimflex)
                .setContentTitle("PIMFLEX TV · Grabando")
                .setContentText(title)
                .setContentIntent(openIntent)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .addAction(0, "Detener", stopIntent)
                .build();
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Grabaciones PIMFLEX TV", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Grabaciones de TV en directo");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(channel);
        }
    }

    @Override
    public void onDestroy() {
        stopCurrentRecording();
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
