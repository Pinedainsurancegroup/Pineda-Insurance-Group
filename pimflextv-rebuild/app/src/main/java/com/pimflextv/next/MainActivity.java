package com.pimflextv.next;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.util.Base64;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.media3.common.MediaItem;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.Player;
import androidx.media3.datasource.DefaultHttpDataSource;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.ui.PlayerView;

import org.json.JSONArray;
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

    private ExoPlayer player;
    private Runnable systemBack;

    private final int bg = Color.rgb(8, 10, 18);
    private final int panel = Color.rgb(20, 24, 38);
    private final int primary = Color.rgb(76, 201, 240);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showLogin();
    }

    @Override
    protected void onDestroy() {
        releasePlayer();
        io.shutdownNow();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (systemBack != null) {
            systemBack.run();
        } else {
            super.onBackPressed();
        }
    }

    private void showLogin() {
        systemBack = null;
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

        statusText.setText("Conectando con el servidor…");
        io.execute(() -> {
            try {
                JSONObject json = new JSONObject(request(null, null));
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
        systemBack = this::showLogin;
        root = baseScreen();
        addTitle("PIMFLEX TV", 30);
        addSubtitle("Conectado como " + username);

        String status = accountInfo == null ? "" : accountInfo.optString("status", "");
        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));
        root.addView(cardText("Cuenta: " + status + (exp.isEmpty() ? "" : "  ·  Expira: " + exp)));

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
        String action = "live".equals(type) ? "get_live_categories" :
                "vod".equals(type) ? "get_vod_categories" : "get_series_categories";
        showLoading("Cargando categorías…");
        io.execute(() -> {
            try {
                JSONArray arr = new JSONArray(request(action, null));
                ui.post(() -> showCategories(type, arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudieron cargar las categorías", e, this::showDashboard));
            }
        });
    }

    private void showCategories(String type, JSONArray arr) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
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
        String action = "live".equals(type) ? "get_live_streams" :
                "vod".equals(type) ? "get_vod_streams" : "get_series";
        showLoading("Cargando " + categoryName + "…");
        io.execute(() -> {
            try {
                JSONArray arr = new JSONArray(request(action, "category_id=" + enc(categoryId)));
                ui.post(() -> showItems(type, categoryId, categoryName, arr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar el contenido", e, () -> loadCategories(type)));
            }
        });
    }

    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        Runnable back = () -> loadCategories(type);
        systemBack = back;
        root = baseScreen();
        addBack(back);
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
                String ts = liveUrl(streamId, "ts");
                String hls = liveUrl(streamId, "m3u8");
                b.setOnClickListener(v -> playStream(name, ts, hls,
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else if ("vod".equals(type)) {
                String streamId = String.valueOf(item.opt("stream_id"));
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + streamId + "." + ext;
                b.setOnClickListener(v -> playStream(name, url, null,
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else {
                String seriesId = String.valueOf(item.opt("series_id"));
                b.setOnClickListener(v -> loadSeriesEpisodes(seriesId, name, categoryId, categoryName, arr));
            }
            root.addView(b);
        }
    }

    private void loadSeriesEpisodes(String seriesId, String seriesName, String categoryId,
                                    String categoryName, JSONArray parentList) {
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

    private void showSeriesEpisodes(String seriesName, JSONObject info, String categoryId,
                                    String categoryName, JSONArray parentList) {
        Runnable back = () -> showItems("series", categoryId, categoryName, parentList);
        systemBack = back;
        root = baseScreen();
        addBack(back);
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
                String ext = safeExt(ep.optString("container_extension", "mp4"));
                String url = server + "/series/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                Button b = listButton(title);
                b.setOnClickListener(v -> playStream(title, url, null,
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
        systemBack = this::showDashboard;
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
        Runnable back = () -> showEpgChannels(parent);
        systemBack = back;
        root = baseScreen();
        addBack(back);
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
        systemBack = this::showDashboard;
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

    private void playStream(String title, String primaryUrl, String fallbackUrl, Runnable back) {
        releasePlayer();
        systemBack = () -> {
            releasePlayer();
            back.run();
        };

        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.BLACK);
        screen.setPadding(dp(8), dp(8), dp(8), dp(8));
        setContentView(screen);

        Button backBtn = secondaryButton("← VOLVER");
        backBtn.setOnClickListener(v -> systemBack.run());
        screen.addView(backBtn, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        TextView name = label(title);
        name.setTextSize(18);
        name.setTextColor(Color.WHITE);
        name.setGravity(Gravity.CENTER_HORIZONTAL);
        name.setPadding(0, dp(6), 0, dp(6));
        screen.addView(name);

        TextView state = label("Conectando al stream…");
        state.setTextColor(Color.LTGRAY);
        state.setGravity(Gravity.CENTER_HORIZONTAL);
        screen.addView(state);

        PlayerView playerView = new PlayerView(this);
        playerView.setUseController(true);
        playerView.setKeepScreenOn(true);
        LinearLayout.LayoutParams vp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        screen.addView(playerView, vp);

        DefaultHttpDataSource.Factory httpFactory = new DefaultHttpDataSource.Factory()
                .setUserAgent("PIMFLEXTV/4.0.2 (Android)")
                .setAllowCrossProtocolRedirects(true)
                .setConnectTimeoutMs(15000)
                .setReadTimeoutMs(30000);

        DefaultMediaSourceFactory mediaSourceFactory = new DefaultMediaSourceFactory(this)
                .setDataSourceFactory(httpFactory);

        player = new ExoPlayer.Builder(this)
                .setMediaSourceFactory(mediaSourceFactory)
                .build();
        playerView.setPlayer(player);

        final boolean[] fallbackUsed = {false};
        player.addListener(new Player.Listener() {
            @Override
            public void onPlaybackStateChanged(int playbackState) {
                if (playbackState == Player.STATE_BUFFERING) {
                    state.setText("Cargando…");
                } else if (playbackState == Player.STATE_READY) {
                    state.setText("");
                } else if (playbackState == Player.STATE_ENDED) {
                    state.setText("Reproducción finalizada");
                }
            }

            @Override
            public void onPlayerError(PlaybackException error) {
                if (fallbackUrl != null && !fallbackUrl.isEmpty() && !fallbackUsed[0]) {
                    fallbackUsed[0] = true;
                    state.setText("Probando formato HLS…");
                    player.setMediaItem(MediaItem.fromUri(Uri.parse(fallbackUrl)));
                    player.prepare();
                    player.play();
                    return;
                }
                state.setText("No fue posible reproducir este stream");
                String detail = error.getErrorCodeName();
                Toast.makeText(MainActivity.this,
                        "Error de reproducción: " + detail,
                        Toast.LENGTH_LONG).show();
            }
        });

        player.setMediaItem(MediaItem.fromUri(Uri.parse(primaryUrl)));
        player.prepare();
        player.play();
    }

    private void releasePlayer() {
        if (player != null) {
            player.stop();
            player.release();
            player = null;
        }
    }

    private String liveUrl(String streamId, String extension) {
        return server + "/live/" + encPath(username) + "/" + encPath(password) + "/" + streamId + "." + extension;
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
        conn.setRequestProperty("User-Agent", "PIMFLEXTV/4.0.2 (Android)");
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
        releasePlayer();
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
        systemBack = this::showDashboard;
        root = baseScreen();
        addTitle("PIMFLEX TV", 28);
        TextView t = cardText(msg);
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        root.addView(t);
    }

    private void showErrorScreen(String title, Exception e, Runnable back) {
        systemBack = back;
        root = baseScreen();
        addTitle(title, 25);
        root.addView(cardText(cleanError(e)));
        addBack(back);
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

    private TextView label(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(16);
        t.setTextColor(Color.WHITE);
        return t;
    }

    private TextView cardText(String text) {
        TextView t = label(text);
        t.setTextColor(Color.WHITE);
        t.setBackgroundColor(panel);
        t.setPadding(dp(16), dp(16), dp(16), dp(16));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(0, dp(6), 0, dp(6));
        t.setLayoutParams(p);
        return t;
    }

    private EditText input(String hint, boolean passwordField) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setHintTextColor(Color.GRAY);
        e.setTextColor(Color.WHITE);
        e.setSingleLine(true);
        e.setFocusable(true);
        e.setBackgroundColor(panel);
        e.setPadding(dp(14), 0, dp(14), 0);
        if (passwordField) {
            e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        }
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58));
        p.setMargins(0, dp(6), 0, dp(6));
        e.setLayoutParams(p);
        return e;
    }

    private Button actionButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextSize(17);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(Color.rgb(55, 84, 170));
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(60));
        p.setMargins(0, dp(7), 0, dp(7));
        b.setLayoutParams(p);
        return b;
    }

    private Button secondaryButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(Color.rgb(42, 47, 62));
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(54));
        p.setMargins(0, dp(5), 0, dp(5));
        b.setLayoutParams(p);
        return b;
    }

    private Button listButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(15);
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setPadding(dp(16), 0, dp(12), 0);
        b.setBackgroundColor(panel);
        b.setFocusable(true);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(58));
        p.setMargins(0, dp(3), 0, dp(3));
        b.setLayoutParams(p);
        return b;
    }

    private String normalizeServer(String value) {
        String s = value == null ? "" : value.trim();
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        return s;
    }

    private String typeTitle(String type) {
        if ("live".equals(type)) return "LIVE TV";
        if ("vod".equals(type)) return "MOVIES / VOD";
        return "SERIES";
    }

    private String safeExt(String ext) {
        if (ext == null || ext.isEmpty()) return "mp4";
        return ext.replaceAll("[^A-Za-z0-9]", "");
    }

    private String enc(String s) {
        try {
            return URLEncoder.encode(s == null ? "" : s, StandardCharsets.UTF_8.name());
        } catch (Exception e) {
            return "";
        }
    }

    private String encPath(String s) {
        return Uri.encode(s == null ? "" : s);
    }

    private String readAll(InputStream in) throws Exception {
        if (in == null) return "";
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
        }
        return sb.toString();
    }

    private String cleanError(Exception e) {
        String m = e.getMessage();
        if (m == null || m.trim().isEmpty()) return e.getClass().getSimpleName();
        return m;
    }

    private String formatEpoch(String raw) {
        try {
            if (raw == null || raw.isEmpty() || "null".equalsIgnoreCase(raw)) return "";
            long sec = Long.parseLong(raw);
            return DateFormat.getDateInstance(DateFormat.MEDIUM, Locale.getDefault()).format(new Date(sec * 1000L));
        } catch (Exception e) {
            return raw == null ? "" : raw;
        }
    }

    private String decodeMaybeBase64(String value) {
        if (value == null || value.isEmpty()) return "";
        try {
            byte[] decoded = Base64.decode(value, Base64.DEFAULT);
            String s = new String(decoded, StandardCharsets.UTF_8).trim();
            if (!s.isEmpty()) return s;
        } catch (Exception ignored) {
        }
        return value;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
