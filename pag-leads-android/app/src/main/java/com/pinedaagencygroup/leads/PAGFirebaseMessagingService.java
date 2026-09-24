package com.pinedaagencygroup.leads;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

public class PAGFirebaseMessagingService extends FirebaseMessagingService {
    private static final String CHANNEL_ID = "pag_fcm_new_leads";

    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        FirebasePushManager.saveAndRegister(this, token);
    }

    @Override
    public void onMessageReceived(RemoteMessage message) {
        super.onMessageReceived(message);
        createChannel();

        String title = message.getData().get("title");
        String body = message.getData().get("body");
        String leadId = message.getData().get("lead_id");

        if (title == null || title.trim().isEmpty()) title = "PAG Leads — Nuevo agente";
        if (body == null || body.trim().isEmpty()) body = "Nuevo lead recibido. Toca para abrir PAG Leads.";

        Intent open = new Intent(this, MainActivity.class);
        if (leadId != null && !leadId.trim().isEmpty()) open.putExtra("lead_id", leadId);
        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        PendingIntent pi = PendingIntent.getActivity(
                this, 1808, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        Notification n = b.setContentTitle(title)
                .setContentText(body)
                .setSmallIcon(R.drawable.ic_launcher)
                .setAutoCancel(true)
                .setContentIntent(pi)
                .build();

        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify((int) (System.currentTimeMillis() & 0x7fffffff), n);
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager nm = getSystemService(NotificationManager.class);
        NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID,
                "Nuevos leads · Firebase",
                NotificationManager.IMPORTANCE_HIGH
        );
        ch.setDescription("Notificaciones push inmediatas de PAG Leads.");
        ch.enableVibration(true);
        nm.createNotificationChannel(ch);
    }
}
