from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Track content class so the player can be configured independently like the reference app.
field = '    private JSONArray zappingChannels;\n'
if field not in s:
    raise SystemExit('zappingChannels field marker not found')
if 'private String activeContentKind' not in s:
    s = s.replace(field, '    private String activeContentKind = "";\n' + field, 1)

# Reset content routing when returning to normal screens.
base = '''    private LinearLayout baseScreen() {
        releaseLivePreview();
        releaseMultiPlayers();
        releasePlayer();
'''
if base not in s:
    raise SystemExit('baseScreen v2.7 marker not found')
s = s.replace(base, '''    private LinearLayout baseScreen() {
        releaseLivePreview();
        releaseMultiPlayers();
        releasePlayer();
        activeContentKind = "";
''', 1)

# Content kind markers for per-section player choice.
live = '''        zappingChannels = channels;
        zappingIndex = normalized;
        zappingBack = back;

        String ts = liveUrl(id, "ts");
'''
if live not in s:
    raise SystemExit('playLiveWithZapping marker not found')
s = s.replace(live, '''        zappingChannels = channels;
        zappingIndex = normalized;
        zappingBack = back;
        activeContentKind = "live";

        String ts = liveUrl(id, "ts");
''', 1)

catchup = '''    private void playCatchup(String streamId, String title, long startSec, int durationMin, Runnable back) {
        SimpleDateFormat pathFormat'''
if catchup not in s:
    raise SystemExit('playCatchup marker not found')
s = s.replace(catchup, '''    private void playCatchup(String streamId, String title, long startSec, int durationMin, Runnable back) {
        activeContentKind = "catchup";
        SimpleDateFormat pathFormat''', 1)

tracked = '''        currentWatchType = type == null ? "" : type;
        currentWatchId = id == null ? "" : id;
'''
if tracked not in s:
    raise SystemExit('startTrackedPlayback marker not found')
s = s.replace(tracked, '''        currentWatchType = type == null ? "" : type;
        activeContentKind = "series_episode".equals(currentWatchType) ? "series" : "vod";
        currentWatchId = id == null ? "" : id;
''', 1)

# External player can now be a saved choice per section.
play_head = '''    private void playStream(String title, String primaryUrl, String fallbackUrl, Runnable back) {
        releasePlayer();
        systemBack = () -> {
'''
if play_head not in s:
    raise SystemExit('playStream head marker not found')
s = s.replace(play_head, '''    private void playStream(String title, String primaryUrl, String fallbackUrl, Runnable back) {
        releasePlayer();
        activePlaybackUrl = primaryUrl == null ? "" : primaryUrl;
        if ("external".equals(resolveContentPlayerMode())) {
            systemBack = back;
            openExternalPlayer();
            return;
        }
        systemBack = () -> {
''', 1)

# Use per-section mode instead of only global player_mode.
old_mode = '''        String configuredPlayerMode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        final String playerMode = (!pendingExternalSubtitlePath.isEmpty() && "vlc".equals(configuredPlayerMode))
'''
if old_mode not in s:
    raise SystemExit('configuredPlayerMode marker not found')
s = s.replace(old_mode, '''        String configuredPlayerMode = resolveContentPlayerMode();
        final String playerMode = (!pendingExternalSubtitlePath.isEmpty() && "vlc".equals(configuredPlayerMode))
''', 1)

# Replace visual player picker with real per-content choices.
picker_pattern = r'''    private void showClonePlayerPicker\(\) \{.*?
    \}

    private void showCloneDecoderSettings'''
m = re.search(picker_pattern, s, flags=re.S)
if not m:
    raise SystemExit('showClonePlayerPicker block not found')
picker = r'''    private String resolveContentPlayerMode() {
        String global = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        if (activeContentKind == null || activeContentKind.isEmpty() || prefs == null) return global;
        return prefs.getString("player_mode_" + activeContentKind, global);
    }

    private String contentPlayerLabel(String mode) {
        if ("exo".equals(mode)) return "ExoPlayer";
        if ("vlc".equals(mode)) return "VLC Player";
        if ("external".equals(mode)) return "External Player";
        return "Built-in Player (Auto Exo/VLC)";
    }

    private void showClonePlayerPicker() {
        systemBack = this::showCloneGeneralSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Elige Reproductor", this::showCloneGeneralSettings);

        root.addView(cardText("Puedes elegir un reproductor distinto para cada sección. "
                + "AUTOMÁTICO conserva el fallback ExoPlayer → VLC que ya está estable."));

        String[] labels = {"DIRECTO", "CINE", "SERIES", "CATCH UP", "GRABACIÓN"};
        String[] keys = {"live", "vod", "series", "catchup", "recording"};

        for (int i = 0; i < labels.length; i++) {
            String labelText = labels[i];
            String key = keys[i];

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);

            TextView label = label(labelText);
            label.setTypeface(Typeface.DEFAULT_BOLD);
            label.setTextSize(18);
            row.addView(label, new LinearLayout.LayoutParams(dp(280), dp(76)));

            String global = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
            String current = prefs == null ? global : prefs.getString("player_mode_" + key, global);
            Button choose = new Button(this);
            choose.setText(contentPlayerLabel(current));
            choose.setTextColor(Color.rgb(25, 25, 25));
            choose.setTextSize(17);
            choose.setAllCaps(false);
            choose.setBackgroundColor(Color.rgb(168, 176, 195));
            choose.setOnClickListener(v -> showContentPlayerChoice(labelText, key));
            row.addView(choose, new LinearLayout.LayoutParams(0, dp(64), 1f));
            root.addView(row);
        }
    }

    private void showContentPlayerChoice(String title, String key) {
        String global = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        String current = prefs == null ? global : prefs.getString("player_mode_" + key, global);
        String[] values = {"auto", "exo", "vlc", "external"};
        String[] labels = {
                "Built-in Player · Auto Exo/VLC",
                "ExoPlayer",
                "VLC Player",
                "Reproductor externo"
        };
        int selected = 0;
        for (int i = 0; i < values.length; i++) if (values[i].equals(current)) selected = i;

        new AlertDialog.Builder(this)
                .setTitle(title)
                .setSingleChoiceItems(labels, selected, (dialog, which) -> {
                    if (prefs != null) prefs.edit()
                            .putString("player_mode_" + key, values[which])
                            .apply();
                    dialog.dismiss();
                    showClonePlayerPicker();
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void showCloneDecoderSettings'''
s = s[:m.start()] + picker + s[m.end():]

# Turn the Stalker/MAG entry screen into Live + Movies + Series.
stalker_screen_pattern = r'''    private void showStalkerScreen\(\) \{.*?
    \}

    private String stalkerEndpoint'''
m = re.search(stalker_screen_pattern, s, flags=re.S)
if not m:
    raise SystemExit('showStalkerScreen block not found')
stalker_screen = r'''    private void showStalkerScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("STALKER / MAG", this::showSettings);

        EditText portal = input("Portal URL", false);
        EditText mac = input("MAC · 00:1A:79:XX:XX:XX", false);
        if (prefs != null) {
            portal.setText(prefs.getString("stalker_portal", ""));
            mac.setText(prefs.getString("stalker_mac", ""));
        }
        root.addView(portal);
        root.addView(mac);

        Runnable save = () -> {
            if (prefs != null) prefs.edit()
                    .putString("stalker_portal", portal.getText().toString().trim())
                    .putString("stalker_mac", mac.getText().toString().trim().toUpperCase(Locale.US))
                    .apply();
        };

        Button live = cloneGreenButton("TV EN DIRECTO");
        live.setOnClickListener(v -> {
            String purl = portal.getText().toString().trim();
            String maddr = mac.getText().toString().trim().toUpperCase(Locale.US);
            if (!validStalkerInput(purl, maddr)) return;
            save.run();
            loadStalkerChannelsV2(purl, maddr);
        });
        root.addView(live);

        Button movies = cloneGrayButton("PELÍCULAS / VOD");
        movies.setOnClickListener(v -> {
            String purl = portal.getText().toString().trim();
            String maddr = mac.getText().toString().trim().toUpperCase(Locale.US);
            if (!validStalkerInput(purl, maddr)) return;
            save.run();
            loadStalkerCategoriesV2(purl, maddr, "vod", "PELÍCULAS");
        });
        root.addView(movies);

        Button series = cloneGrayButton("SERIES");
        series.setOnClickListener(v -> {
            String purl = portal.getText().toString().trim();
            String maddr = mac.getText().toString().trim().toUpperCase(Locale.US);
            if (!validStalkerInput(purl, maddr)) return;
            save.run();
            loadStalkerCategoriesV2(purl, maddr, "series", "SERIES");
        });
        root.addView(series);

        root.addView(cardText("Compatibilidad con portales Stalker/MAG autorizados. "
                + "Se prueban automáticamente las rutas comunes portal.php y stalker_portal/server/load.php."));
    }

    private boolean validStalkerInput(String portal, String mac) {
        if (portal == null || portal.trim().isEmpty() || mac == null || mac.trim().isEmpty()) {
            Toast.makeText(this, "Completa portal y MAC.", Toast.LENGTH_SHORT).show();
            return false;
        }
        return true;
    }

    private String stalkerEndpoint'''
s = s[:m.start()] + stalker_screen + s[m.end():]

# Add full Stalker compatibility helpers before existing loadStalkerChannels.
marker = '    private void loadStalkerChannels(String portal, String mac) {\n'
if marker not in s:
    raise SystemExit('loadStalkerChannels marker not found')
methods = r'''    private JSONObject openStalkerSessionV2(String portal, String mac) throws Exception {
        java.util.LinkedHashSet<String> candidates = new java.util.LinkedHashSet<>();
        String normalized = normalizeServer(portal);

        if (normalized.endsWith(".php")) candidates.add(normalized);

        String base = normalized;
        if (base.endsWith("/c")) base = base.substring(0, base.length() - 2);
        if (base.contains("/stalker_portal")) {
            base = base.substring(0, base.indexOf("/stalker_portal"));
        }

        candidates.add(base + "/portal.php");
        candidates.add(base + "/stalker_portal/server/load.php");
        candidates.add(base + "/server/load.php");

        String savedEndpoint = prefs == null ? "" : prefs.getString("stalker_endpoint", "");
        if (!savedEndpoint.isEmpty()) {
            java.util.LinkedHashSet<String> ordered = new java.util.LinkedHashSet<>();
            ordered.add(savedEndpoint);
            ordered.addAll(candidates);
            candidates = ordered;
        }

        Exception last = null;
        for (String endpoint : candidates) {
            try {
                String handshakeUrl = endpoint + "?type=stb&action=handshake&token=&JsHttpRequest=1-xml";
                JSONObject handshake = new JSONObject(stalkerGet(handshakeUrl, mac, ""));
                JSONObject hjs = handshake.optJSONObject("js");
                String token = hjs == null ? "" : hjs.optString("token", "");
                if (token.isEmpty()) continue;

                try {
                    stalkerGet(endpoint + "?type=stb&action=get_profile&JsHttpRequest=1-xml", mac, token);
                } catch (Exception ignored) {}

                if (prefs != null) prefs.edit().putString("stalker_endpoint", endpoint).apply();
                JSONObject session = new JSONObject();
                session.put("endpoint", endpoint);
                session.put("token", token);
                return session;
            } catch (Exception e) {
                last = e;
            }
        }
        throw last == null ? new Exception("No se pudo iniciar sesión con el portal.") : last;
    }

    private JSONArray stalkerDataArray(JSONObject response) {
        if (response == null) return new JSONArray();
        Object jsObj = response.opt("js");
        if (jsObj instanceof JSONArray) return (JSONArray) jsObj;
        if (jsObj instanceof JSONObject) {
            JSONObject js = (JSONObject) jsObj;
            JSONArray data = js.optJSONArray("data");
            if (data != null) return data;
            JSONArray channels = js.optJSONArray("channels");
            if (channels != null) return channels;
            JSONArray categories = js.optJSONArray("categories");
            if (categories != null) return categories;
        }
        return new JSONArray();
    }

    private void loadStalkerChannelsV2(String portal, String mac) {
        showLoading("Conectando Stalker/MAG…");
        io.execute(() -> {
            try {
                JSONObject session = openStalkerSessionV2(portal, mac);
                String endpoint = session.optString("endpoint", "");
                String token = session.optString("token", "");
                JSONObject channelsJson = new JSONObject(stalkerGet(endpoint +
                        "?type=itv&action=get_all_channels&JsHttpRequest=1-xml", mac, token));
                JSONArray channels = stalkerDataArray(channelsJson);
                ui.post(() -> showStalkerChannelsV2(portal, mac, endpoint, token, channels));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, this::showStalkerScreen));
            }
        });
    }

    private void showStalkerChannelsV2(String portal, String mac, String endpoint,
                                       String token, JSONArray channels) {
        systemBack = this::showStalkerScreen;
        root = cloneScreen();
        addCloneHeader("STALKER / MAG · LIVE", this::showStalkerScreen);

        EditText search = input("Buscar canal", false);
        root.addView(search);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);

        Runnable render = () -> {
            list.removeAllViews();
            String q = search.getText().toString().trim().toLowerCase(Locale.ROOT);
            int shown = 0;
            for (int i = 0; i < channels.length() && shown < 600; i++) {
                JSONObject row = channels.optJSONObject(i);
                if (row == null) continue;
                String name = row.optString("name", "Canal");
                if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;
                String cmd = row.optString("cmd", "");
                Button b = listButton(name);
                b.setOnClickListener(v -> createAndPlayStalkerLinkV2(endpoint, mac, token,
                        "itv", cmd, row.optString("id", ""), name,
                        () -> showStalkerChannelsV2(portal, mac, endpoint, token, channels)));
                list.addView(b);
                shown++;
            }
            if (shown == 0) list.addView(cardText("No se encontraron canales."));
        };
        render.run();

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render.run(); }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void loadStalkerCategoriesV2(String portal, String mac, String type, String title) {
        showLoading("Cargando " + title + "…");
        io.execute(() -> {
            try {
                JSONObject session = openStalkerSessionV2(portal, mac);
                String endpoint = session.optString("endpoint", "");
                String token = session.optString("token", "");
                JSONObject json = new JSONObject(stalkerGet(endpoint +
                        "?type=" + enc(type) + "&action=get_categories&JsHttpRequest=1-xml", mac, token));
                JSONArray categories = stalkerDataArray(json);

                if (categories.length() == 0 && "series".equals(type)) {
                    // Some Stalker portals expose series inside the VOD catalog.
                    JSONObject vod = new JSONObject(stalkerGet(endpoint +
                            "?type=vod&action=get_categories&JsHttpRequest=1-xml", mac, token));
                    categories = stalkerDataArray(vod);
                }
                JSONArray finalCategories = categories;
                ui.post(() -> showStalkerCategoriesV2(portal, mac, endpoint, token,
                        type, title, finalCategories));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, this::showStalkerScreen));
            }
        });
    }

    private void showStalkerCategoriesV2(String portal, String mac, String endpoint, String token,
                                         String type, String title, JSONArray categories) {
        systemBack = this::showStalkerScreen;
        root = cloneScreen();
        addCloneHeader("STALKER · " + title, this::showStalkerScreen);

        Button all = listButton("TODO");
        all.setBackgroundColor(Color.rgb(47, 146, 230));
        all.setOnClickListener(v -> loadStalkerItemsV2(portal, mac, endpoint, token,
                type, "0", "TODO", title, categories));
        root.addView(all);

        for (int i = 0; i < categories.length(); i++) {
            JSONObject row = categories.optJSONObject(i);
            if (row == null) continue;
            String id = row.optString("id", row.optString("category_id", row.optString("genre_id", "")));
            String name = row.optString("title", row.optString("name",
                    row.optString("category_name", "Categoría")));
            Button b = listButton(name);
            b.setOnClickListener(v -> loadStalkerItemsV2(portal, mac, endpoint, token,
                    type, id, name, title, categories));
            root.addView(b);
        }

        if (categories.length() == 0) root.addView(cardText("El portal no devolvió categorías."));
    }

    private void loadStalkerItemsV2(String portal, String mac, String endpoint, String token,
                                    String type, String categoryId, String categoryName,
                                    String sectionTitle, JSONArray categories) {
        showLoading("Cargando " + categoryName + "…");
        io.execute(() -> {
            try {
                JSONArray items = new JSONArray();
                String[] params = {
                        "category=" + enc(categoryId),
                        "genre=" + enc(categoryId),
                        ""
                };
                Exception last = null;
                for (String p : params) {
                    try {
                        String suffix = p.isEmpty() ? "" : "&" + p;
                        JSONObject json = new JSONObject(stalkerGet(endpoint +
                                "?type=" + enc(type) + "&action=get_ordered_list&p=1" + suffix +
                                "&JsHttpRequest=1-xml", mac, token));
                        items = stalkerDataArray(json);
                        if (items.length() > 0) break;
                    } catch (Exception e) {
                        last = e;
                    }
                }

                // Series often live in type=vod with is_series=1.
                if (items.length() == 0 && "series".equals(type)) {
                    JSONObject json = new JSONObject(stalkerGet(endpoint +
                            "?type=vod&action=get_ordered_list&p=1&genre=" + enc(categoryId) +
                            "&JsHttpRequest=1-xml", mac, token));
                    JSONArray raw = stalkerDataArray(json);
                    JSONArray onlySeries = new JSONArray();
                    for (int i = 0; i < raw.length(); i++) {
                        JSONObject row = raw.optJSONObject(i);
                        if (row == null) continue;
                        String flag = String.valueOf(row.opt("is_series"));
                        if ("1".equals(flag) || "true".equalsIgnoreCase(flag)) onlySeries.put(row);
                    }
                    items = onlySeries.length() > 0 ? onlySeries : raw;
                }

                JSONArray finalItems = items;
                ui.post(() -> showStalkerItemsV2(portal, mac, endpoint, token, type,
                        categoryId, categoryName, sectionTitle, categories, finalItems));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e,
                        () -> showStalkerCategoriesV2(portal, mac, endpoint, token,
                                type, sectionTitle, categories)));
            }
        });
    }

    private void showStalkerItemsV2(String portal, String mac, String endpoint, String token,
                                    String type, String categoryId, String categoryName,
                                    String sectionTitle, JSONArray categories, JSONArray items) {
        Runnable back = () -> showStalkerCategoriesV2(portal, mac, endpoint, token,
                type, sectionTitle, categories);
        systemBack = back;
        root = cloneScreen();
        addCloneHeader(categoryName, back);

        EditText search = input("Buscar", false);
        root.addView(search);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);

        Runnable render = () -> {
            list.removeAllViews();
            String q = search.getText().toString().trim().toLowerCase(Locale.ROOT);
            int shown = 0;
            for (int i = 0; i < items.length() && shown < 500; i++) {
                JSONObject row = items.optJSONObject(i);
                if (row == null) continue;
                String name = row.optString("name", row.optString("title", "Contenido"));
                if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;

                String id = row.optString("id", row.optString("movie_id", ""));
                String cmd = row.optString("cmd", "");
                String seriesFlag = String.valueOf(row.opt("is_series"));
                boolean isSeries = "series".equals(type) || "1".equals(seriesFlag)
                        || "true".equalsIgnoreCase(seriesFlag);

                Button b = listButton((isSeries ? "▶  " : "🎬  ") + name);
                if (isSeries) {
                    b.setOnClickListener(v -> loadStalkerEpisodesV2(portal, mac, endpoint, token,
                            id, name, cmd, () -> showStalkerItemsV2(portal, mac, endpoint, token,
                                    type, categoryId, categoryName, sectionTitle, categories, items)));
                } else {
                    b.setOnClickListener(v -> createAndPlayStalkerLinkV2(endpoint, mac, token,
                            "vod", cmd, id, name,
                            () -> showStalkerItemsV2(portal, mac, endpoint, token,
                                    type, categoryId, categoryName, sectionTitle, categories, items)));
                }
                list.addView(b);
                shown++;
            }
            if (shown == 0) list.addView(cardText("No se encontró contenido."));
        };
        render.run();

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render.run(); }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void loadStalkerEpisodesV2(String portal, String mac, String endpoint, String token,
                                       String movieId, String seriesName, String seriesCmd, Runnable back) {
        showLoading("Cargando episodios…");
        io.execute(() -> {
            try {
                JSONArray episodes = new JSONArray();
                String[] queries = {
                        "?type=vod&action=get_ordered_list&movie_id=" + enc(movieId) + "&p=1&JsHttpRequest=1-xml",
                        "?type=series&action=get_ordered_list&series_id=" + enc(movieId) + "&p=1&JsHttpRequest=1-xml",
                        "?type=vod&action=get_movie_details&movie_id=" + enc(movieId) + "&JsHttpRequest=1-xml"
                };
                for (String query : queries) {
                    try {
                        JSONObject json = new JSONObject(stalkerGet(endpoint + query, mac, token));
                        episodes = stalkerDataArray(json);
                        if (episodes.length() > 0) break;

                        JSONObject js = json.optJSONObject("js");
                        if (js != null) {
                            JSONArray seasons = js.optJSONArray("seasons");
                            if (seasons != null && seasons.length() > 0) {
                                episodes = seasons;
                                break;
                            }
                        }
                    } catch (Exception ignored) {}
                }

                JSONArray finalEpisodes = episodes;
                ui.post(() -> showStalkerEpisodesV2(endpoint, mac, token, movieId,
                        seriesName, seriesCmd, finalEpisodes, back));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, back));
            }
        });
    }

    private void showStalkerEpisodesV2(String endpoint, String mac, String token, String movieId,
                                       String seriesName, String seriesCmd, JSONArray episodes, Runnable back) {
        systemBack = back;
        root = cloneScreen();
        addCloneHeader(seriesName, back);

        if (episodes.length() == 0) {
            root.addView(cardText("El portal no devolvió episodios separados. "
                    + "Se intentará abrir el enlace principal si está disponible."));
            if (seriesCmd != null && !seriesCmd.isEmpty()) {
                Button play = cloneGreenButton("REPRODUCIR");
                play.setOnClickListener(v -> createAndPlayStalkerLinkV2(endpoint, mac, token,
                        "vod", seriesCmd, movieId, seriesName, back));
                root.addView(play);
            }
            return;
        }

        for (int i = 0; i < episodes.length(); i++) {
            JSONObject row = episodes.optJSONObject(i);
            if (row == null) continue;
            String id = row.optString("id", row.optString("episode_id",
                    row.optString("season_id", "")));
            String name = row.optString("name", row.optString("title",
                    "Episodio " + (i + 1)));
            String cmd = row.optString("cmd", "");
            Button b = listButton(name);
            b.setOnClickListener(v -> createAndPlayStalkerLinkV2(endpoint, mac, token,
                    "vod", cmd, id, name, () -> showStalkerEpisodesV2(endpoint, mac, token,
                            movieId, seriesName, seriesCmd, episodes, back)));
            root.addView(b);
        }
    }

    private void createAndPlayStalkerLinkV2(String endpoint, String mac, String token,
                                            String type, String cmd, String id,
                                            String name, Runnable back) {
        String candidate = cleanStalkerPlayUrl(cmd);
        if (candidate.startsWith("http://") || candidate.startsWith("https://")) {
            activeContentKind = "itv".equals(type) ? "live" : "vod";
            playStream(name, candidate, null, back);
            return;
        }

        String finalCmd = cmd == null ? "" : cmd.trim();
        if (finalCmd.isEmpty() && id != null && !id.isEmpty() && !"itv".equals(type)) {
            finalCmd = "/media/file_" + id + ".mpg";
        }
        if (finalCmd.isEmpty()) {
            Toast.makeText(this, "El portal no proporcionó comando de reproducción.", Toast.LENGTH_LONG).show();
            return;
        }

        String command = finalCmd;
        showLoading("Creando enlace de reproducción…");
        io.execute(() -> {
            try {
                String url = endpoint + "?type=" + enc(type) + "&action=create_link&cmd=" + enc(command)
                        + "&series=0&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml";
                JSONObject response = new JSONObject(stalkerGet(url, mac, token));
                JSONObject js = response.optJSONObject("js");
                String play = "";
                if (js != null) play = js.optString("url", js.optString("cmd", ""));
                play = cleanStalkerPlayUrl(play);
                if (play.isEmpty()) throw new Exception("No se pudo crear el enlace.");
                String finalPlay = play;
                ui.post(() -> {
                    activeContentKind = "itv".equals(type) ? "live" : "vod";
                    playStream(name, finalPlay, null, back);
                });
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, back));
            }
        });
    }

'''
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2.7 Stalker VOD/Series and per-section player patch applied')
