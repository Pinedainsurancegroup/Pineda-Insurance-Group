from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import android.app.Activity;\n', 'import android.app.Activity;\nimport android.content.SharedPreferences;\n')
s = s.replace('import android.text.InputType;\n', 'import android.text.InputType;\nimport android.text.Editable;\nimport android.text.TextWatcher;\n')
s = s.replace('import android.widget.Button;\n', 'import android.widget.Button;\nimport android.widget.CheckBox;\n')
s = s.replace('import java.util.Date;\n', 'import java.util.Date;\nimport java.util.HashSet;\nimport java.util.Set;\n')

s = s.replace('    private TextView statusText;\n', '''    private TextView statusText;\n    private CheckBox rememberCheck;\n    private SharedPreferences prefs;\n''')

old_oncreate = '''    @Override\n    protected void onCreate(Bundle savedInstanceState) {\n        super.onCreate(savedInstanceState);\n        showLogin();\n    }\n'''
new_oncreate = '''    @Override\n    protected void onCreate(Bundle savedInstanceState) {\n        super.onCreate(savedInstanceState);\n        prefs = getSharedPreferences("pimflex_settings", MODE_PRIVATE);\n        showLogin();\n        if (prefs.getBoolean("remember", false)) {\n            String savedPassword = SecureStore.loadPassword(this, prefs);\n            if (!savedPassword.isEmpty()) {\n                passInput.setText(savedPassword);\n                authenticate();\n            }\n        }\n    }\n'''
if old_oncreate not in s:
    raise SystemExit('onCreate block not found')
s = s.replace(old_oncreate, new_oncreate)

old_login = '''    private void showLogin() {\n        systemBack = null;\n        root = baseScreen();\n        addTitle("PIMFLEX TV", 34);\n        addSubtitle("Nueva edición independiente · Android + Android TV");\n\n        TextView badge = label("XTREAM LOGIN");\n        badge.setTextColor(primary);\n        badge.setTypeface(Typeface.DEFAULT_BOLD);\n        badge.setGravity(Gravity.CENTER_HORIZONTAL);\n        badge.setPadding(0, dp(16), 0, dp(8));\n        root.addView(badge);\n\n        serverInput = input("Server URL", false);\n        serverInput.setText("http://my-flashtv.com:8080");\n        userInput = input("Usuario", false);\n        passInput = input("Contraseña", true);\n\n        root.addView(serverInput);\n        root.addView(userInput);\n        root.addView(passInput);\n\n        Button login = actionButton("ENTRAR");\n        login.setOnClickListener(v -> authenticate());\n        root.addView(login);\n\n        statusText = label("Introduce tus datos para validar el servidor.");\n        statusText.setTextColor(Color.LTGRAY);\n        statusText.setPadding(0, dp(14), 0, 0);\n        statusText.setGravity(Gravity.CENTER_HORIZONTAL);\n        root.addView(statusText);\n    }\n'''
new_login = '''    private void showLogin() {\n        systemBack = null;\n        root = baseScreen();\n        addTitle("PIMFLEX TV", 34);\n        addSubtitle("Live TV · Movies · Series · EPG");\n\n        TextView badge = label("XTREAM LOGIN");\n        badge.setTextColor(primary);\n        badge.setTypeface(Typeface.DEFAULT_BOLD);\n        badge.setGravity(Gravity.CENTER_HORIZONTAL);\n        badge.setPadding(0, dp(16), 0, dp(8));\n        root.addView(badge);\n\n        serverInput = input("Server URL", false);\n        serverInput.setText(prefs == null ? "http://my-flashtv.com:8080" : prefs.getString("server", "http://my-flashtv.com:8080"));\n        userInput = input("Usuario", false);\n        if (prefs != null) userInput.setText(prefs.getString("username", ""));\n        passInput = input("Contraseña", true);\n\n        root.addView(serverInput);\n        root.addView(userInput);\n        root.addView(passInput);\n\n        rememberCheck = new CheckBox(this);\n        rememberCheck.setText("Recordar sesión en este dispositivo");\n        rememberCheck.setTextColor(Color.LTGRAY);\n        rememberCheck.setChecked(prefs != null && prefs.getBoolean("remember", false));\n        rememberCheck.setFocusable(true);\n        root.addView(rememberCheck);\n\n        Button login = actionButton("ENTRAR");\n        login.setOnClickListener(v -> authenticate());\n        root.addView(login);\n\n        statusText = label("Introduce tus datos para validar el servidor.");\n        statusText.setTextColor(Color.LTGRAY);\n        statusText.setPadding(0, dp(14), 0, 0);\n        statusText.setGravity(Gravity.CENTER_HORIZONTAL);\n        root.addView(statusText);\n    }\n'''
if old_login not in s:
    raise SystemExit('showLogin block not found')
s = s.replace(old_login, new_login)

old_auth_head = '''        statusText.setText("Conectando con el servidor…");\n        io.execute(() -> {\n'''
new_auth_head = '''        final boolean rememberSession = rememberCheck != null && rememberCheck.isChecked();\n        statusText.setText("Conectando con el servidor…");\n        io.execute(() -> {\n'''
if old_auth_head not in s:
    raise SystemExit('authenticate head not found')
s = s.replace(old_auth_head, new_auth_head, 1)

old_auth_success = '''                accountInfo = user;\n                ui.post(this::showDashboard);\n'''
new_auth_success = '''                accountInfo = user;\n                if (prefs != null) {\n                    prefs.edit()\n                            .putString("server", server)\n                            .putString("username", username)\n                            .putBoolean("remember", rememberSession)\n                            .apply();\n                    if (rememberSession) SecureStore.savePassword(this, prefs, password);\n                    else SecureStore.clearPassword(prefs);\n                }\n                ui.post(this::showDashboard);\n'''
if old_auth_success not in s:
    raise SystemExit('authenticate success not found')
s = s.replace(old_auth_success, new_auth_success, 1)

old_dashboard = '''    private void showDashboard() {\n        systemBack = this::showLogin;\n        root = baseScreen();\n        addTitle("PIMFLEX TV", 30);\n        addSubtitle("Conectado como " + username);\n\n        String status = accountInfo == null ? "" : accountInfo.optString("status", "");\n        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));\n        root.addView(cardText("Cuenta: " + status + (exp.isEmpty() ? "" : "  ·  Expira: " + exp)));\n\n        Button live = actionButton("📺  LIVE TV");\n        live.setOnClickListener(v -> loadCategories("live"));\n        root.addView(live);\n\n        Button movies = actionButton("🎬  MOVIES / VOD");\n        movies.setOnClickListener(v -> loadCategories("vod"));\n        root.addView(movies);\n\n        Button series = actionButton("▶  SERIES");\n        series.setOnClickListener(v -> loadCategories("series"));\n        root.addView(series);\n\n        Button epg = actionButton("🗓  TV GUIDE / EPG");\n        epg.setOnClickListener(v -> loadEpgChannels());\n        root.addView(epg);\n\n        Button accountBtn = actionButton("👤  MI CUENTA");\n        accountBtn.setOnClickListener(v -> showAccount());\n        root.addView(accountBtn);\n\n        Button logout = secondaryButton("CAMBIAR CUENTA");\n        logout.setOnClickListener(v -> showLogin());\n        root.addView(logout);\n    }\n'''
new_dashboard = '''    private void showDashboard() {\n        systemBack = this::showLogin;\n        root = baseScreen();\n        addTitle("PIMFLEX TV", 30);\n        addSubtitle("Conectado como " + username);\n\n        String status = accountInfo == null ? "" : accountInfo.optString("status", "");\n        String exp = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));\n        root.addView(cardText("Cuenta: " + status + (exp.isEmpty() ? "" : "  ·  Expira: " + exp)));\n\n        Button live = actionButton("📺  LIVE TV");\n        live.setOnClickListener(v -> loadCategories("live"));\n        root.addView(live);\n\n        Button movies = actionButton("🎬  MOVIES / VOD");\n        movies.setOnClickListener(v -> loadCategories("vod"));\n        root.addView(movies);\n\n        Button series = actionButton("▶  SERIES");\n        series.setOnClickListener(v -> loadCategories("series"));\n        root.addView(series);\n\n        Button favorites = actionButton("★  FAVORITOS");\n        favorites.setOnClickListener(v -> loadFavorites());\n        root.addView(favorites);\n\n        Button epg = actionButton("🗓  TV GUIDE / EPG");\n        epg.setOnClickListener(v -> loadEpgChannels());\n        root.addView(epg);\n\n        Button accountBtn = secondaryButton("👤  MI CUENTA");\n        accountBtn.setOnClickListener(v -> showAccount());\n        root.addView(accountBtn);\n\n        Button logout = secondaryButton("CAMBIAR CUENTA");\n        logout.setOnClickListener(v -> {\n            if (prefs != null) prefs.edit().putBoolean("remember", false).apply();\n            if (prefs != null) SecureStore.clearPassword(prefs);\n            password = "";\n            showLogin();\n        });\n        root.addView(logout);\n    }\n'''
if old_dashboard not in s:
    raise SystemExit('dashboard block not found')
s = s.replace(old_dashboard, new_dashboard)

pattern = r'    private void showItems\(String type, String categoryId, String categoryName, JSONArray arr\) \{.*?\n    \}\n\n    private void loadSeriesEpisodes'
replacement = r'''    private void showItems(String type, String categoryId, String categoryName, JSONArray arr) {
        Runnable back = () -> loadCategories(type);
        systemBack = back;
        root = baseScreen();
        addBack(back);
        addTitle(categoryName, 26);
        addSubtitle("Elementos: " + arr.length());

        EditText search = input("Buscar en " + categoryName, false);
        root.addView(search);

        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);
        renderItems(list, type, categoryId, categoryName, arr, "");

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                renderItems(list, type, categoryId, categoryName, arr, s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void renderItems(LinearLayout list, String type, String categoryId, String categoryName,
                             JSONArray arr, String query) {
        list.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        int shown = 0;
        int limit = Math.min(arr.length(), 1200);

        for (int i = 0; i < limit; i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", item.optString("title", "Contenido"));
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

            String id = itemId(type, item);
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);

            Button b = listButton(name);
            LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(0, dp(58), 1f);
            bp.setMargins(0, dp(3), dp(5), dp(3));
            b.setLayoutParams(bp);

            if ("live".equals(type)) {
                String ts = liveUrl(id, "ts");
                String hls = liveUrl(id, "m3u8");
                b.setOnClickListener(v -> playStream(name, ts, hls,
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else if ("vod".equals(type)) {
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                b.setOnClickListener(v -> playStream(name, url, null,
                        () -> showItems(type, categoryId, categoryName, arr)));
            } else {
                b.setOnClickListener(v -> loadSeriesEpisodes(id, name, categoryId, categoryName, arr));
            }
            row.addView(b);

            Button fav = secondaryButton(isFavorite(type, id) ? "★" : "☆");
            LinearLayout.LayoutParams fp = new LinearLayout.LayoutParams(dp(62), dp(58));
            fp.setMargins(0, dp(3), 0, dp(3));
            fav.setLayoutParams(fp);
            fav.setTextSize(22);
            fav.setOnClickListener(v -> {
                toggleFavorite(type, id);
                fav.setText(isFavorite(type, id) ? "★" : "☆");
            });
            row.addView(fav);
            list.addView(row);

            shown++;
            if (shown >= 500) break;
        }

        if (shown == 0) {
            list.addView(cardText(q.isEmpty() ? "No hay contenido disponible." : "No se encontraron resultados."));
        }
    }

    private void loadSeriesEpisodes'''
s, n = re.subn(pattern, replacement, s, flags=re.S)
if n != 1:
    raise SystemExit(f'showItems replacement count={n}')

marker = '    private void loadEpgChannels() {'
favorites_code = r'''    private String itemId(String type, JSONObject item) {
        if ("series".equals(type)) return String.valueOf(item.opt("series_id"));
        return String.valueOf(item.opt("stream_id"));
    }

    private Set<String> getFavorites() {
        if (prefs == null) return new HashSet<>();
        Set<String> stored = prefs.getStringSet("favorites", Collections.emptySet());
        return new HashSet<>(stored == null ? Collections.emptySet() : stored);
    }

    private boolean isFavorite(String type, String id) {
        return getFavorites().contains(type + ":" + id);
    }

    private void toggleFavorite(String type, String id) {
        if (prefs == null || id == null || id.isEmpty() || "null".equals(id)) return;
        Set<String> favs = getFavorites();
        String key = type + ":" + id;
        if (favs.contains(key)) favs.remove(key); else favs.add(key);
        prefs.edit().putStringSet("favorites", favs).apply();
    }

    private void loadFavorites() {
        Set<String> favs = getFavorites();
        if (favs.isEmpty()) {
            systemBack = this::showDashboard;
            root = baseScreen();
            addBack(this::showDashboard);
            addTitle("FAVORITOS", 28);
            root.addView(cardText("Todavía no tienes favoritos. Usa ☆ en Live TV, Movies o Series para agregarlos."));
            return;
        }

        showLoading("Cargando favoritos…");
        io.execute(() -> {
            try {
                JSONArray merged = new JSONArray();
                collectFavorites("live", new JSONArray(request("get_live_streams", null)), favs, merged);
                collectFavorites("vod", new JSONArray(request("get_vod_streams", null)), favs, merged);
                collectFavorites("series", new JSONArray(request("get_series", null)), favs, merged);
                ui.post(() -> showFavorites(merged));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudieron cargar los favoritos", e, this::showDashboard));
            }
        });
    }

    private void collectFavorites(String type, JSONArray source, Set<String> favs, JSONArray out) {
        for (int i = 0; i < source.length(); i++) {
            JSONObject item = source.optJSONObject(i);
            if (item == null) continue;
            String id = itemId(type, item);
            if (!favs.contains(type + ":" + id)) continue;
            try {
                item.put("__type", type);
                out.put(item);
            } catch (Exception ignored) {}
        }
    }

    private void showFavorites(JSONArray arr) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("★ FAVORITOS", 28);
        addSubtitle("Guardados: " + arr.length());

        EditText search = input("Buscar en favoritos", false);
        root.addView(search);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);
        renderFavorites(list, arr, "");

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                renderFavorites(list, arr, s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void renderFavorites(LinearLayout list, JSONArray arr, String query) {
        list.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        int shown = 0;
        for (int i = 0; i < arr.length(); i++) {
            JSONObject item = arr.optJSONObject(i);
            if (item == null) continue;
            String type = item.optString("__type", "live");
            String id = itemId(type, item);
            if (!isFavorite(type, id)) continue;
            String name = item.optString("name", item.optString("title", "Contenido"));
            if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            Button b = listButton(("live".equals(type) ? "📺  " : "vod".equals(type) ? "🎬  " : "▶  ") + name);
            LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(0, dp(58), 1f);
            bp.setMargins(0, dp(3), dp(5), dp(3));
            b.setLayoutParams(bp);

            if ("live".equals(type)) {
                String ts = liveUrl(id, "ts");
                String hls = liveUrl(id, "m3u8");
                b.setOnClickListener(v -> playStream(name, ts, hls, () -> showFavorites(arr)));
            } else if ("vod".equals(type)) {
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                b.setOnClickListener(v -> playStream(name, url, null, () -> showFavorites(arr)));
            } else {
                b.setOnClickListener(v -> loadFavoriteSeriesEpisodes(id, name, arr));
            }
            row.addView(b);

            Button remove = secondaryButton("★");
            LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(dp(62), dp(58));
            rp.setMargins(0, dp(3), 0, dp(3));
            remove.setLayoutParams(rp);
            remove.setTextSize(22);
            remove.setOnClickListener(v -> {
                toggleFavorite(type, id);
                renderFavorites(list, arr, query);
            });
            row.addView(remove);
            list.addView(row);
            shown++;
        }
        if (shown == 0) list.addView(cardText("No hay favoritos que coincidan con la búsqueda."));
    }

    private void loadFavoriteSeriesEpisodes(String seriesId, String seriesName, JSONArray favorites) {
        showLoading("Cargando episodios de " + seriesName + "…");
        io.execute(() -> {
            try {
                JSONObject obj = new JSONObject(request("get_series_info", "series_id=" + enc(seriesId)));
                ui.post(() -> showFavoriteSeriesEpisodes(seriesName, obj, favorites));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudieron cargar los episodios", e, () -> showFavorites(favorites)));
            }
        });
    }

    private void showFavoriteSeriesEpisodes(String seriesName, JSONObject info, JSONArray favorites) {
        Runnable back = () -> showFavorites(favorites);
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
                        () -> showFavoriteSeriesEpisodes(seriesName, info, favorites)));
                root.addView(b);
            }
        }
    }

'''
if marker not in s:
    raise SystemExit('EPG marker not found')
s = s.replace(marker, favorites_code + marker, 1)

marker2 = '    private String normalizeServer(String value) {'
helpers = r'''    private void decorateFocus(Button b, int normalColor) {
        b.setOnFocusChangeListener((v, hasFocus) -> {
            b.setBackgroundColor(hasFocus ? Color.rgb(83, 106, 210) : normalColor);
            float scale = hasFocus ? 1.025f : 1.0f;
            b.animate().scaleX(scale).scaleY(scale).setDuration(90).start();
        });
    }

'''
if marker2 not in s:
    raise SystemExit('normalize marker not found')
s = s.replace(marker2, helpers + marker2, 1)

s = s.replace('''        b.setBackgroundColor(Color.rgb(55, 84, 170));\n        b.setFocusable(true);\n''', '''        int normal = Color.rgb(55, 84, 170);\n        b.setBackgroundColor(normal);\n        b.setFocusable(true);\n        decorateFocus(b, normal);\n''')
s = s.replace('''        b.setBackgroundColor(Color.rgb(42, 47, 62));\n        b.setFocusable(true);\n''', '''        int normal = Color.rgb(42, 47, 62);\n        b.setBackgroundColor(normal);\n        b.setFocusable(true);\n        decorateFocus(b, normal);\n''')
s = s.replace('''        b.setBackgroundColor(panel);\n        b.setFocusable(true);\n''', '''        b.setBackgroundColor(panel);\n        b.setFocusable(true);\n        decorateFocus(b, panel);\n''')

p.write_text(s)
print('Feature patch applied')
