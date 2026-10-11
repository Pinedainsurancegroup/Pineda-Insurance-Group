package com.pimflextv.next;

import org.json.JSONArray;
import org.json.JSONObject;
import java.net.URI;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** A strict portable schema: device paths, PINs, tokens and keystore bytes are never imported. */
final class PortableBackupData {
    static final String FORMAT = "PIMFLEX_PORTABLE_2";
    static final int MAX_ACCOUNTS = 12;
    private static final Set<String> BOOLS = set("clone_autoboot", "clone_full_guide", "clone_subtitles_on",
            "clone_autonext", "clone_pip", "clone_clear_cache", "clone_epg_in_channel_list", "clone_clock_24",
            "clone_auto_content", "clone_auto_epg", "clone_software_decoder", "clone_opensl", "clone_opengl", "immersive_player");
    private static final Set<String> URLS = set("m3u_url", "xmltv_url", "stalker_portal", "stalker_endpoint");
    private static Set<String> set(String... values) { return new HashSet<>(Arrays.asList(values)); }

    static String accountId(String server, String username) {
        return Integer.toHexString((server + "|" + username).hashCode());
    }

    static JSONObject create(Map<String, ?> prefs, JSONArray accounts) throws Exception {
        JSONObject values = new JSONObject();
        for (Map.Entry<String, ?> e : prefs.entrySet()) {
            String type = type(e.getKey());
            if (type == null) continue;
            Object value = e.getValue();
            if (value instanceof Set) value = new JSONArray((Set<?>) value);
            if (valid(e.getKey(), value)) values.put(e.getKey(), new JSONObject().put("type", type).put("value", value));
        }
        return new JSONObject().put("format", FORMAT).put("created_at", System.currentTimeMillis())
                .put("prefs", values).put("accounts", accounts);
    }

    static JSONObject readJson(String text) throws Exception {
        // Bound nesting before org.json parsing, including unsupported fields in legacy files.
        int depth=0; boolean quoted=false, escape=false;
        for (int i=0; i<text.length(); i++) {
            char c=text.charAt(i);
            if (quoted) {
                if (escape) escape=false;
                else if (c == 92) escape=true;
                else if (c == 34) quoted=false;
            } else if (c == 34) quoted=true;
            else if (c == '{' || c == '[') { if (++depth > 16) throw new Exception("Respaldo demasiado complejo."); }
            else if (c == '}' || c == ']') depth--;
        }
        return new JSONObject(text);
    }

    static Parsed parse(JSONObject root) throws Exception {
        String format = root.optString("format");
        boolean legacy = "PIMFLEX_BACKUP_1".equals(format);
        if (!legacy && !FORMAT.equals(format)) throw new Exception("Formato de respaldo no reconocido.");
        JSONObject values = root.optJSONObject("prefs");
        if (values == null || values.length() > 2000) throw new Exception("Ajustes de respaldo inválidos.");
        Map<String, Object> accepted = new LinkedHashMap<>();
        int ignored = 0;
        for (Iterator<String> it = values.keys(); it.hasNext();) {
            String key = it.next();
            String expected = type(key);
            if (expected == null) { ignored++; continue; }
            Object value = values.get(key);
            if (legacy) {
                if (value instanceof JSONObject && "string_set".equals(((JSONObject) value).optString("_type")))
                    value = ((JSONObject) value).optJSONArray("value");
            } else {
                if (!(value instanceof JSONObject) || !expected.equals(((JSONObject) value).optString("type")))
                    throw new Exception("Tipo de ajuste incorrecto.");
                value = ((JSONObject) value).opt("value");
            }
            if (!valid(key, value)) throw new Exception("El archivo contiene un ajuste inválido.");
            if ("set".equals(expected)) {
                Set<String> strings = new HashSet<>();
                JSONArray array = (JSONArray) value;
                for (int i = 0; i < array.length(); i++) strings.add(array.getString(i));
                value = strings;
            }
            // Normalize numeric JSON values to their exact SharedPreferences type.
            if ("int".equals(expected)) value = ((Number) value).intValue();
            accepted.put(key, value);
        }
        JSONArray raw = legacy ? new JSONArray(values.optString("saved_accounts", "[]")) : root.optJSONArray("accounts");
        if (raw == null || raw.length() > MAX_ACCOUNTS) throw new Exception("Lista de cuentas inválida.");
        JSONArray accounts = new JSONArray();
        Set<String> seen = new HashSet<>();
        int secrets = 0;
        for (int i = 0; i < raw.length(); i++) {
            JSONObject row = raw.getJSONObject(i);
            String server = strictString(row, "server", 2048), user = strictString(row, "username", 256);
            if (!http(server) || user.trim().isEmpty()) throw new Exception("Datos de cuenta inválidos.");
            String id = accountId(server, user);
            if (!seen.add(id)) throw new Exception("Cuentas duplicadas o identificadores en conflicto.");
            String password = legacy ? "" : strictString(row, "password", 4096);
            if (!password.isEmpty()) secrets++;
            accounts.put(new JSONObject().put("id", id).put("server", server).put("username", user).put("password", password));
        }
        return new Parsed(accepted, accounts, legacy, ignored, secrets);
    }

    static final class Parsed {
        final Map<String, Object> prefs;
        final JSONArray accounts;
        final boolean legacy;
        final int ignored, secrets;
        Parsed(Map<String, Object> p, JSONArray a, boolean l, int i, int s) { prefs=p; accounts=a; legacy=l; ignored=i; secrets=s; }
    }

    static String type(String key) {
        if (BOOLS.contains(key)) return "bool";
        if ("network_cache_ms".equals(key) || "clone_epg_timeshift".equals(key)) return "int";
        if (URLS.contains(key) || set("stalker_mac", "clone_device_mode", "clone_stream_format", "multi_dns_json",
                "opensubtitles_languages", "player_mode", "player_mode_live", "player_mode_vod", "player_mode_series", "player_mode_catchup", "player_mode_recording").contains(key)) return "string";
        if (key.matches("favorites_[0-9a-f]{1,8}")) return "set";
        if (key.matches("(watch_history|preferred_audio_language|preferred_subtitle_language|subtitle_mode|vlc_audio_name|vlc_subtitle_mode|vlc_subtitle_name)_[0-9a-f]{1,8}")) return "string";
        return null;
    }

    private static boolean valid(String key, Object value) {
        String type = type(key);
        if (type == null || value == null || value == JSONObject.NULL) return false;
        if ("bool".equals(type)) return value instanceof Boolean;
        if ("int".equals(type)) {
            if (!(value instanceof Number)) return false;
            double n = ((Number) value).doubleValue();
            return n == Math.rint(n) && ("network_cache_ms".equals(key) ? n >= 0 && n <= 60000 : n >= -24 && n <= 24);
        }
        if ("set".equals(type)) {
            if (!(value instanceof JSONArray) || ((JSONArray) value).length() > 5000) return false;
            JSONArray a = (JSONArray) value;
            for (int i=0; i<a.length(); i++) if (!(a.opt(i) instanceof String) || ((String) a.opt(i)).length() > 2048) return false;
            return true;
        }
        if (!(value instanceof String)) return false;
        String s = (String) value;
        if (s.length() > 256_000) return false;
        if (URLS.contains(key)) return s.isEmpty() || (s.length() <= 8192 && http(s));
        if (key.startsWith("player_mode")) return set("auto", "exo", "vlc", "external").contains(s);
        if ("clone_device_mode".equals(key)) return set("auto", "tv", "mobile").contains(s);
        if ("clone_stream_format".equals(key)) return set("ts", "m3u8").contains(s);
        if ("stalker_mac".equals(key)) return s.isEmpty() || s.matches("(?i)[0-9a-f]{2}(:[0-9a-f]{2}){5}");
        if ("multi_dns_json".equals(key)) {
            try {
                JSONArray a = new JSONArray(s);
                if (a.length() > 100) return false;
                for (int i=0; i<a.length(); i++) if (!(a.opt(i) instanceof String) || a.getString(i).length() > 2048 || !http(a.getString(i))) return false;
            } catch (Exception e) { return false; }
        } else if (key.startsWith("watch_history_")) {
            try {
                JSONArray a = new JSONArray(s);
                if (a.length() > 40) return false;
                for (int i=0; i<a.length(); i++) {
                    JSONObject row = a.getJSONObject(i);
                    if (!set("vod", "series_episode").contains(row.optString("type")) || !(row.opt("id") instanceof String)) return false;
                    for (String field : new String[]{"key", "title", "ext", "art"})
                        if (!(row.opt(field) instanceof String) || row.getString(field).length() > 8192) return false;
                    for (String field : new String[]{"position", "duration", "updated"})
                        if (!(row.opt(field) instanceof Number) || row.getLong(field) < 0) return false;
                }
            } catch (Exception e) { return false; }
        } else if (s.length() > 256) return false;
        return true;
    }

    private static String strictString(JSONObject object, String key, int max) throws Exception {
        Object value = object.opt(key);
        if (!(value instanceof String) || ((String) value).length() > max) throw new Exception("Datos de cuenta inválidos.");
        return (String) value;
    }

    private static boolean http(String value) {
        try {
            URI uri = new URI(value);
            return ("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme()))
                    && uri.getHost() != null && uri.getUserInfo() == null;
        } catch (Exception e) { return false; }
    }
}
