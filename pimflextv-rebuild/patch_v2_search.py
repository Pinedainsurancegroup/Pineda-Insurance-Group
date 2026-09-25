from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

field = '    private int sleepTimerMinutes = 0;\n'
extra = '''    private JSONArray globalSearchLive = new JSONArray();
    private JSONArray globalSearchVod = new JSONArray();
    private JSONArray globalSearchSeries = new JSONArray();
    private String lastGlobalQuery = "";
'''
if field not in s:
    raise SystemExit('sleep timer field marker not found')
s = s.replace(field, field + extra, 1)

tile = '        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);\n'
if tile not in s:
    raise SystemExit('dashboard account tile marker not found')
s = s.replace(tile, '''        addDashboardTile(menu, "🔎  BUSCAR", this::loadGlobalSearch, cols);
        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);
''', 1)

marker = '    private String accountScope() {\n'
methods = r'''    private void loadGlobalSearch() {
        showLoading("Preparando búsqueda global…");
        io.execute(() -> {
            try {
                globalSearchLive = new JSONArray(request("get_live_streams", null));
                globalSearchVod = new JSONArray(request("get_vod_streams", null));
                globalSearchSeries = new JSONArray(request("get_series", null));
                ui.post(() -> showGlobalSearch(lastGlobalQuery));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo preparar la búsqueda", e, this::showDashboard));
            }
        });
    }

    private void showGlobalSearch(String initialQuery) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("🔎 BÚSQUEDA GLOBAL", 27);
        addSubtitle("Canales · Películas · Series");

        EditText input = input("Escribe al menos 2 caracteres", false);
        input.setText(initialQuery == null ? "" : initialQuery);
        input.setSelection(input.getText().length());
        root.addView(input);

        LinearLayout results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        root.addView(results);

        renderGlobalSearch(results, input.getText().toString());
        input.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence text, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                String q = text == null ? "" : text.toString();
                lastGlobalQuery = q;
                renderGlobalSearch(results, q);
            }
            @Override public void afterTextChanged(Editable editable) {}
        });
    }

    private void renderGlobalSearch(LinearLayout results, String query) {
        results.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        if (q.length() < 2) {
            results.addView(cardText("Escribe 2 o más caracteres para buscar en todo PIMFLEX TV."));
            return;
        }

        int shown = 0;
        shown += addGlobalMatches(results, "live", globalSearchLive, q, Math.max(0, 80 - shown));
        shown += addGlobalMatches(results, "vod", globalSearchVod, q, Math.max(0, 80 - shown));
        shown += addGlobalMatches(results, "series", globalSearchSeries, q, Math.max(0, 80 - shown));

        if (shown == 0) results.addView(cardText("No encontré resultados para “" + query.trim() + "”."));
        else {
            TextView count = label("Resultados mostrados: " + shown);
            count.setTextColor(primary);
            count.setGravity(Gravity.CENTER_HORIZONTAL);
            count.setPadding(0, dp(8), 0, dp(8));
            results.addView(count, 0);
        }
    }

    private int addGlobalMatches(LinearLayout results, String type, JSONArray source, String q, int remaining) {
        if (remaining <= 0 || source == null) return 0;
        int added = 0;
        for (int i = 0; i < source.length() && added < remaining; i++) {
            JSONObject item = source.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("name", item.optString("title", "Contenido"));
            if (!name.toLowerCase(Locale.ROOT).contains(q)) continue;

            String id = itemId(type, item);
            String prefix = "live".equals(type) ? "📺  " : "vod".equals(type) ? "🎬  " : "▶  ";
            Button b = listButton(prefix + name);
            if ("live".equals(type)) {
                String ts = liveUrl(id, "ts");
                String hls = liveUrl(id, "m3u8");
                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        playStream(name, ts, hls, () -> showGlobalSearch(lastGlobalQuery))));
            } else if ("vod".equals(type)) {
                String ext = safeExt(item.optString("container_extension", "mp4"));
                String art = item.optString("stream_icon", item.optString("cover_big", item.optString("cover", "")));
                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadVodDetails(id, name, ext, art, () -> showGlobalSearch(lastGlobalQuery))));
            } else {
                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadGlobalSeriesEpisodes(id, name)));
            }
            results.addView(b);
            added++;
        }
        return added;
    }

    private void loadGlobalSeriesEpisodes(String seriesId, String seriesName) {
        showLoading("Cargando " + seriesName + "…");
        io.execute(() -> {
            try {
                JSONObject info = new JSONObject(request("get_series_info", "series_id=" + enc(seriesId)));
                ui.post(() -> showGlobalSeriesEpisodes(seriesName, info));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar la serie", e,
                        () -> showGlobalSearch(lastGlobalQuery)));
            }
        });
    }

    private void showGlobalSeriesEpisodes(String seriesName, JSONObject info) {
        Runnable back = () -> showGlobalSearch(lastGlobalQuery);
        systemBack = back;
        root = baseScreen();
        addBack(back);
        addTitle(seriesName, 26);
        addSubtitle("Episodios");
        addSeriesInfoHeader(info);

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
                b.setOnClickListener(v -> runWithParentalGate(title, () ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showGlobalSeriesEpisodes(seriesName, info))));
                root.addView(b);
            }
        }
    }

'''
if marker not in s:
    raise SystemExit('accountScope marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 global search patch applied')
