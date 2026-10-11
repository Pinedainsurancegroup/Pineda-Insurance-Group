package com.pimflextv.next;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

final class PortableBackupStore {
    static JSONObject capture(Context context, SharedPreferences prefs, boolean includePasswords) throws Exception {
        JSONArray saved = new JSONArray(prefs.getString("saved_accounts", "[]"));
        JSONArray accounts = new JSONArray();
        for (int i=0; i<saved.length(); i++) {
            JSONObject row = saved.getJSONObject(i);
            String server = row.getString("server"), user = row.getString("username");
            String id = PortableBackupData.accountId(server, user);
            String password = includePasswords ? SecureStore.loadSecret(context, prefs, "account_" + id) : "";
            accounts.put(new JSONObject().put("server", server).put("username", user).put("password", password));
        }
        JSONObject result = PortableBackupData.create(prefs.getAll(), accounts);
        PortableBackupData.parse(result); // Fail before writing if local data cannot be transferred safely.
        return result;
    }

    /** Validate and stage everything before one commit; existing accounts and settings win. */
    static int restore(Context context, SharedPreferences prefs, PortableBackupData.Parsed incoming) throws Exception {
        JSONArray existing = new JSONArray(prefs.getString("saved_accounts", "[]"));
        if (existing.length() > PortableBackupData.MAX_ACCOUNTS) throw new Exception("Hay demasiadas cuentas guardadas.");
        Set<String> ids = new HashSet<>();
        Map<String, String> identities = new java.util.HashMap<>();
        JSONArray merged = new JSONArray(existing.toString());
        for (int i=0; i<existing.length(); i++) {
            JSONObject row = existing.getJSONObject(i);
            String id = PortableBackupData.accountId(row.getString("server"), row.getString("username"));
            ids.add(id);
            identities.put(id, row.getString("server") + "\n" + row.getString("username"));
        }
        SharedPreferences.Editor editor = prefs.edit();
        int added = 0;
        for (int i=0; i<incoming.accounts.length(); i++) {
            JSONObject row = incoming.accounts.getJSONObject(i);
            String id = row.getString("id");
            if (ids.contains(id)) {
                if (!identities.get(id).equals(row.getString("server") + "\n" + row.getString("username")))
                    throw new Exception("Dos cuentas tienen un identificador en conflicto. No se cambió nada.");
                continue;
            }
            if (merged.length() >= PortableBackupData.MAX_ACCOUNTS)
                throw new Exception("No hay espacio para todas las cuentas (máximo 12). No se cambió nada.");
            String secret = row.getString("password");
            if (!secret.isEmpty()) {
                if (Build.VERSION.SDK_INT < 23)
                    throw new Exception("Para guardar contraseñas de cuentas se necesita Android 6 o superior.");
                SecureStore.stagePortableSecret(editor, "account_" + id, secret);
            }
            merged.put(new JSONObject().put("id", id).put("server", row.getString("server"))
                    .put("username", row.getString("username")).put("updated", System.currentTimeMillis()));
            ids.add(id);
            added++;
        }
        for (Map.Entry<String, Object> row : incoming.prefs.entrySet()) {
            String key = row.getKey(); Object value = row.getValue();
            if (value instanceof Set) {
                @SuppressWarnings("unchecked") Set<String> favoriteSet = new HashSet<>((Set<String>) value);
                favoriteSet.addAll(prefs.getStringSet(key, java.util.Collections.emptySet()));
                if (favoriteSet.size() > 5000) throw new Exception("Demasiados favoritos para combinar.");
                editor.putStringSet(key, favoriteSet);
            } else if (!prefs.contains(key)) {
                if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
                else if (value instanceof Integer) editor.putInt(key, (Integer) value);
                else if (value instanceof String) editor.putString(key, (String) value);
            }
        }
        editor.putString("saved_accounts", merged.toString());
        if (Thread.currentThread().isInterrupted()) throw new Exception("Restauración cancelada.");
        if (!editor.commit()) throw new Exception("No se pudo guardar el respaldo en este dispositivo.");
        return added;
    }
}
