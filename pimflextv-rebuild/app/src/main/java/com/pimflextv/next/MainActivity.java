package com.pimflextv.next;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.MediaController;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private LinearLayout root;
    private EditText serverInput;
    private EditText userInput;
    private EditText passInput;
    private TextView statusText;

    private String server = "";
    private String username = "";
    private String password = "";
    private JSONObject accountInfo;

    private final int bg = Color.rgb(8, 10, 18);
    private final int panel = Color.rgb(20, 24, 38);
    private final int primary = Color.rgb(76, 201, 240);
    private final int accent = Color.rgb(126, 87, 194);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showLogin();
    }

    @Override
    protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }

    private void showLogin() {
        root = baseScreen();
        addTitle("PIMFLEX TV", 34);
        addSubtitle("Nueva edición independiente · Android + Android TV");

        TextView badge = label("XTREAM LOGIN");
        badge.setTextColor(primary);
        badge.setTypeface(Typeface.DEFAULT_BOLD);
        badge.setGravity(Gravity.CENTER_HORIZONTAL);
        badge.setPadding(0, dp(16), 0, dp(8));
        root.addView(badge);

        serverInput = input("Server URL", false);
        serverInput.setText("http://my-flashtv.com:8080");
        userInput = input("Usuario", false);
        passInput = input("Contraseña", true);

        root.addView(serverInput);
        root.addView(userInput);
        root.addView(passInput);

        Button login = actionButton("ENTRAR");
        login.setOnClickListener(v -> authenticate());
        root.addView(login);

        statusText = label("Introduce tus datos para validar el servidor.");
        statusText.setTextColor(Color.LTGRAY);
        statusText.setPadding(0, dp(14), 0, 0);
        statusText.setGravity(Gravity.CENTER_HORIZONTAL);
        root.addView(statusText);
    }

    private void authenticate() {
        server = normalizeServer(serverInput.getText().toString());
        username = userInput.getText().toString().trim();
        password = passInput.getText().toString();

        if (server.isEmpty() || username.isEmpty() || password.isEmpty()) {
            statusText.setText("Completa servidor, usuario y contraseña.");
            return;
        }

        setBusy("Conectando con el servidor…");
        io.execute(() -> {
            try {
                String body = request(null, null);
                JSONObject json = new JSONObject(body);
                JSONObject user = json.optJSONObject("user_info");
                if (user == null) throw new Exception("El servidor no devolvió user_info.");

                String auth = String.valueOf(user.opt("auth"));
                String status = user.optString("status", "");
                if (!("1".equals(auth) || "Active".equalsIgnoreCase(status))) {
                    throw new Exception("Credenciales rechazadas. Estado: " + status);
                }

                accountInfo = user;
                ui.post(this::showDashboard);
            } catch (Exception e) {
                ui.post(() -> {
                    statusText.setText("Error: " + cleanError(e));
                    Toast.makeText(this, "No fue posible iniciar sesión", Toast.LENGTH_LONG).show();
                });
            }
        });
    }

    private void showDashboard() {
        root = baseScreen();
        addTitle("PIMFLEX TV", 30);
        addSubtitle("Conectado como " + username);

        String status = accountInfo == null ? "" : accountInfo.optString("status", "");
        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));
        TextView account = cardText("Cuenta: " + status + (exp.isEmpty() ? "" : "  ·  Expira: " + exp));
        root.addView(account);

        Button live = actionButton("📺  LIVE TV");
        live.setOnClickListener(v -> loadCategories("live"));
        root.addView(live);

        Button movies = actionButton("🎬  MOVIES / VOD");
        movies.setOnClickListener(v -> loadCategories("vod"));
        root.addView(movies);

        Button series = actionButton("▶  SERIES");
        series.setOnClickListener(v -> loadCategories("series"));
        root.addView(series);

        Button epg = actionButton("🗓  TV GUIDE / EPG");
        epg.setOnClickListener(v -> loadEpgChannels());
        root.addView(epg);

        Button accountBtn = actionButton("👤  MI CUENTA");
        accountBtn.setOnClickListener(v -> showAccount());
        root.addView(accountBtn);

        Button logout = secondaryButton("CAMBIAR CUENTA");
        logout.setOnClickListener(v -> showLogin());
        root.addView(logout);
    }

    private void loadCategories(String type) {
        String action;
        if ("live".equals(type)) action = "get_live_categories";
        else if ("vod".equals(type)) action = "get_vod_categories";
        else action = "get_series_categories";

        showLoading("Cargando categorías…");
        io.execute(() -> {
            try {
                JSONArray arr = new JSONArray(request(action, null));
                ui.post(() -> showCategories(type, arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudieron cargar las categorías", e, () -> showDashboard()));
            }
        });
    }

    private void showCategories(String type, JSONArray arr) {
        root = baseScreen();
        addBack(() -> showDashboard());
        addTitle(typeTitle(type), 28);
        addSubtitle("Categorías disponibles: " + arr.length());

        if (arr.length() == 0) {
            root.addView(cardText("No hay categorías disponibles."));
            return;
        }

        for (int i = 0; i < arr.length(); i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String id = item.optString("category_id", "");
            String name = item.optString("category_name", "Categoría");
            Button b = listButton(name);
            b.setOnClickListener(v -> loadItems(type, id, name));
            root.addView(b);
        }
    }

    private void loadItems(String type, String categoryId, String categoryName) {
        String action;
        if ("live".equals(type)) action = "get_live_streams";
        else if ("vod".equals(type)) action = "get_vod_streams";
        else action = "get_series";

        showLoading("Cargando " + categoryName + "…");
        io.execute(() -> {
            try {
                String extra = "category_id=" + enc(categoryId);
                JSONArray arr = new JSONArray(request(action, extra));
                ui.post(() -> showItems(type, categoryId, categoryName, arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar el contenido", e,
                        () -> loadCategories(type)));
            }
        });
    }

    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        root = baseScreen();
        addBack(() -> loadCategories(type));
        addTitle(categoryName, 26);
        addSubtitle("Elementos: " + arr.length());

        int limit = Math.min(arr.length(), 800);
        for (int i = 0; i < limit; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", item.optString("title", "Contenido"));
            Button b = listButton(name);

            if ("live".equals(type)) {
                String streamId = String.valueOf(item.opt("stream_id"));
                b.setOnClickListener(v -> playStream(name,
                        server + "/live/" + encPath(username) + "/" + encPath(password) + "/" + streamId + ".ts",
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else if ("vod".equals(type)) {
                String streamId = String.valueOf(item.opt("stream_id"));
                String ext = item.optString("container_extension", "mp4");
                b.setOnClickListener(v -> playStream(name,
                        server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + streamId + "." + safeExt(ext),
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else {
                String seriesId = String.valueOf(item.opt("series_id"));
                b.setOnClickListener(v -> loadSeriesEpisodes(seriesId, name, categoryId, categoryName, arr));
            }
            root.addView(b);
        }

        if (arr.length() > limit) {
            root.addView(cardText("Mostrando los primeros " + limit + " elementos de " + arr.length() + "."));
        }
    }

    private void loadSeriesEpisodes(String seriesId, String seriesName, String categoryId, String categoryName, JSONArray parentList) {
        showLoading("Cargando episodios de " + seriesName + "…");
        io.execute(() -> {
            try {
                JSONObject obj = new JSONObject(request("get_series_info", "series_id=" + enc(seriesId)));
                ui.post(() -> showSeriesEpisodes(seriesName, obj, categoryId, categoryName, parentList));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudieron cargar los episodios", e,
                        () -> showItems("series", categoryId, categoryName, parentList)));
            }
        });
    }

    private void showSeriesEpisodes(String seriesName, JSONObject info, String categoryId, String categoryName, JSONArray parentList) {
        root = baseScreen();
        addBack(() -> showItems("series", categoryId, categoryName, parentList));
        addTitle(seriesName, 26);
        addSubtitle("Episodios");

        JSONObject episodes = info.optJSONObject("episodes");
        if (episodes == null || episodes.length() == 0) {
            root.addView(cardText("No se encontraron episodios."));
            return;
        }

        List<String> seasons = new ArrayList<>();
        Iterator<String> keys = episodes.keys();
        while (keys.hasNext()) seasons.add(keys.next());
        Collections.sort(seasons);

        for (String season : seasons) {
            TextView header = label("Temporada " + season);
            header.setTextColor(primary);
            header.setTypeface(Typeface.DEFAULT_BOLD);
            header.setTextSize(20);
            header.setPadding(0, dp(18), 0, dp(8));
            root.addView(header);

            JSONArray eps = episodes.optJSONArray(season);
            if (eps == null) continue;
            for (int i = 0; i < eps.length(); i++) {
                JSONObject ep = eps.optJSONObject(i);
                if (ep == null) continue;
                String id = String.valueOf(ep.opt("id"));
                String title = ep.optString("title", "Episodio " + (i + 1));
                String ext = ep.optString("container_extension", "mp4");
                Button b = listButton(title);
                b.setOnClickListener(v -> playStream(title,
                        server + "/series/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + safeExt(ext),
                        () -> showSeriesEpisodes(seriesName, info, categoryId, categoryName, parentList)));
                root.addView(b);
            }
        }
    }

    private void loadEpgChannels() {
        showLoading("Cargando canales para EPG…");
        io.execute(() -> {
            try {
                JSONArray arr = new JSONArray(request("get_live_streams", null));
                ui.post(() -> showEpgChannels(arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar el EPG", e, this::showDashboard));
            }
        });
    }

    private void showEpgChannels(JSONArray arr) {
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("TV GUIDE / EPG", 28);
        addSubtitle("Selecciona un canal");

        int limit = Math.min(arr.length(), 400);
        for (int i = 0; i < limit; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", "Canal");
            String id = String.valueOf(item.opt("stream_id"));
            Button b = listButton(name);
            b.setOnClickListener(v -> loadChannelEpg(id, name, arr));
            root.addView(b);
        }
    }

    private void loadChannelEpg(String streamId, String channelName, JSONArray parent) {
        showLoading("Cargando guía de " + channelName + "…");
        io.execute(() -> {
            try {
                JSONObject obj = new JSONObject(request("get_short_epg", "stream_id=" + enc(streamId) + "&limit=20"));
                ui.post(() -> showChannelEpg(channelName, obj, parent));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar la guía", e, () -> showEpgChannels(parent)));
            }
        });
    }

    private void showChannelEpg(String channelName, JSONObject obj, JSONArray parent) {
        root = baseScreen();
        addBack(() -> showEpgChannels(parent));
        addTitle(channelName, 26);
        addSubtitle("Programación");

        JSONArray listings = obj.optJSONArray("epg_listings");
        if (listings == null || listings.length() == 0) {
            root.addView(cardText("Este canal no devolvió programación EPG."));
            return;
        }
        for (int i = 0; i < listings.length(); i++) {
            JSONObject row = listings.optJSONObject(i);
            if (row == null) continue;
            String title = decodeMaybeBase64(row.optString("title", "Programa"));
            String start = row.optString("start", "");
            String end = row.optString("end", "");
            root.addView(cardText(title + (start.isEmpty() ? "" : "\n" + start + " → " + end)));
        }
    }

    private void showAccount() {
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("MI CUENTA", 28);
        if (accountInfo == null) {
            root.addView(cardText("No hay información de cuenta disponible."));
            return;
        }

        root.addView(cardText("Estado: " + accountInfo.optString("status", "—")));
        root.addView(cardText("Usuario: " + accountInfo.optString("username", username)));
        root.addView(cardText("Expiración: " + formatEpoch(accountInfo.optString("exp_date", ""))));
        root.addView(cardText("Conexiones activas: " + accountInfo.optString("active_cons", "—")));
        root.addView(cardText("Máximo de conexiones: " + accountInfo.optString("max_connections", "—")));
        root.addView(cardText("Servidor: " + server));
    }

    private void playStream(String title, String url, Runnable back) {
        setContentView(new LinearLayout(this));
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.BLACK);
        screen.setPadding(dp(10), dp(10), dp(10), dp(10));
        setContentView(screen);

        Button backBtn = secondaryButton("← VOLVER");
        backBtn.setOnClickListener(v -> back.run());
        screen.addView(backBtn, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        TextView name = label(title);
        name.setTextSize(18);
        name.setTextColor(Color.WHITE);
        name.setGravity(Gravity.CENTER_HORIZONTAL);
        name.setPadding(0, dp(8), 0, dp(8));
        screen.addView(name);

        VideoView video = new VideoView(this);
        LinearLayout.LayoutParams vp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        screen.addView(video, vp);

        MediaController controls = new MediaController(this);
        controls.setAnchorView(video);
        video.setMediaController(controls);
        video.setVideoURI(Uri.parse(url));
        video.setOnPreparedListener(mp -> {
            mp.setLooping(false);
            video.start();
        });
        video.setOnErrorListener((mp, what, extra) -> {
            Toast.makeText(this, "Error de reproducción (" + what + "/" + extra + ")", Toast.LENGTH_LONG).show();
            return true;
        });
        video.requestFocus();
    }

    private String request(String action, String extra) throws Exception {
        StringBuilder u = new StringBuilder(server)
                .append("/player_api.php?username=").append(enc(username))
                .append("&password=").append(enc(password));
        if (action != null && !action.isEmpty()) u.append("&action=").append(enc(action));
        if (extra != null && !extra.isEmpty()) u.append("&").append(extra);

        HttpURLConnection conn = (HttpURLConnection) new URL(u.toString()).openConnection();
        conn.setConnectTimeout(12000);
        conn.setReadTimeout(20000);
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Accept", "application/json, text/plain, */*");
        conn.setRequestProperty("User-Agent", "PIMFLEXTV/1.0 (Android)");
        conn.setInstanceFollowRedirects(true);

        int code = conn.getResponseCode();
        InputStream in = code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream();
        String body = readAll(in);
        conn.disconnect();

        if (code < 200 || code >= 300) {
            throw new Exception("HTTP " + code + (body.isEmpty() ? "" : " · " + body.substring(0, Math.min(body.length(), 180))));
        }
        if (body.trim().isEmpty()) throw new Exception("Respuesta vacía del servidor.");
        return body;
    }

    private LinearLayout baseScreen() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(bg);
        scroll.setFillViewport(true);

        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(22), dp(28), dp(22), dp(40));
        scroll.addView(body, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);
        return body;
    }

    private void showLoading(String msg) {
        root = baseScreen();
        addTitle("PIMFLEX TV", 28);
        TextView t = cardText(msg);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        root.addView(t);
    }

    private void showErrorScreen(String title, Exception e, Runnable back) {
        root = baseScreen();
        addTitle(title, 25);
        root.addView(cardText(cleanError(e)));
        Button b = secondaryButton("← VOLVER");
        b.setOnClickListener(v -> back.run());
        root.addView(b);
    }

    private void addBack(Runnable back) {
        Button b = secondaryButton("← VOLVER");
        b.setOnClickListener(v -> back.run());
        root.addView(b);
    }

    private void addTitle(String text, int size) {
        TextView t = label(text);
        t.setTextColor(Color.WHITE);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setTextSize(size);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        t.setPadding(0, dp(8), 0, dp(4));
        root.addView(t);
    }

    private void addSubtitle(String text) {
        TextView t = label(text);
        t.setTextColor(Color.rgb(190, 194, 210));
        t.setTextSize(15);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        t.setPadding(0, 0, 0, dp(18));
        root.addView(t);
    }

    private EditText input(String hint, boolean passwordField) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setHintTextColor(Color.rgb(145, 150, 170));
        e.setTextColor(Color.WHITE);
        e.setTextSize(17);
        e.setSingleLine(true);
        e.setPadding(dp(16), 0, dp(16), 0);
        e.setBackgroundColor(panel);
        e.setSelectAllOnFocus(false);
        if (passwordField) e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        else e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58));
        p.setMargins(0, dp(7), 0, dp(7));
        e.setLayoutParams(p);
        return e;
    }

    private Button actionButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(18);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setAllCaps(false);
        b.setBackgroundColor(accent);
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(62));
        p.setMargins(0, dp(8), 0, dp(8));
        b.setLayoutParams(p);
        return b;
    }

    private Button secondaryButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(15);
        b.setAllCaps(false);
        b.setBackgroundColor(Color.rgb(39, 45, 64));
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52));
        p.setMargins(0, dp(6), 0, dp(6));
        b.setLayoutParams(p);
        return b;
    }

    private Button listButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(16);
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setPadding(dp(18), 0, dp(18), 0);
        b.setAllCaps(false);
        b.setBackgroundColor(panel);
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58));
        p.setMargins(0, dp(4), 0, dp(4));
        b.setLayoutParams(p);
        return b;
    }

    private TextView cardText(String text) {
        TextView t = label(text);
        t.setTextColor(Color.WHITE);
        t.setTextSize(16);
        t.setPadding(dp(16), dp(15), dp(16), dp(15));
        t.setBackgroundColor(panel);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(0, dp(6), 0, dp(6));
        t.setLayoutParams(p);
        return t;
    }

    private TextView label(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        return t;
    }

    private void setBusy(String text) {
        statusText.setText(text);
    }

    private String typeTitle(String type) {
        if ("live".equals(type)) return "LIVE TV";
        if ("vod".equals(type)) return "MOVIES / VOD";
        return "SERIES";
    }

    private String normalizeServer(String value) {
        String s = value == null ? "" : value.trim();
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        if (!s.isEmpty() && !(s.startsWith("http://") || s.startsWith("https://"))) s = "http://" + s;
        return s;
    }

    private String enc(String s) throws Exception {
        return URLEncoder.encode(s == null ? "" : s, StandardCharsets.UTF_8.name());
    }

    private String encPath(String s) {
        try {
            return URLEncoder.encode(s == null ? "" : s, StandardCharsets.UTF_8.name()).replace("+", "%20");
        } catch (Exception e) {
            return s == null ? "" : s;
        }
    }

    private String safeExt(String ext) {
        if (ext == null || ext.isEmpty()) return "mp4";
        return ext.replaceAll("[^A-Za-z0-9]", "");
    }

    private String readAll(InputStream in) throws Exception {
        if (in == null) return "";
        BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        return sb.toString();
    }

    private String cleanError(Exception e) {
        String m = e.getMessage();
        return m == null || m.trim().isEmpty() ? e.getClass().getSimpleName() : m;
    }

    private String formatEpoch(String raw) {
        if (raw == null || raw.isEmpty() || "null".equalsIgnoreCase(raw)) return "—";
        try {
            long seconds = Long.parseLong(raw);
            return DateFormat.getDateInstance(DateFormat.MEDIUM, Locale.getDefault()).format(new Date(seconds * 1000L));
        } catch (Exception ignored) {
            return raw;
        }
    }

    private String decodeMaybeBase64(String s) {
        if (s == null || s.isEmpty()) return "Programa";
        try {
            byte[] decoded = android.util.Base64.decode(s, android.util.Base64.DEFAULT);
            String candidate = new String(decoded, StandardCharsets.UTF_8).trim();
            if (!candidate.isEmpty() && candidate.chars().allMatch(c -> c == '\n' || c == '\r' || c == '\t' || c >= 32)) return candidate;
        } catch (Exception ignored) { }
        return s;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
