from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

tile = '        addDashboardTile(menu, "🚀  SPEED TEST", this::runSpeedTest, cols);\n'
if tile not in s:
    raise SystemExit('speed tile marker not found')
s = s.replace(tile, '''        addDashboardTile(menu, "🚀  SPEED TEST", this::runSpeedTest, cols);
        addDashboardTile(menu, "☰  M3U", this::showM3uScreen, cols);
''', 1)

marker = '    private void runSpeedTest() {\n'
methods = r'''    private void showM3uScreen() {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("☰ M3U PLAYER", 27);
        addSubtitle("Carga una playlist M3U/M3U8 por URL");

        EditText url = input("URL M3U / M3U8", false);
        if (prefs != null) url.setText(prefs.getString("m3u_url", ""));
        root.addView(url);

        Button load = actionButton("CARGAR PLAYLIST");
        load.setOnClickListener(v -> {
            String value = url.getText().toString().trim();
            if (value.isEmpty()) {
                Toast.makeText(this, "Introduce la URL de la playlist.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit().putString("m3u_url", value).apply();
            loadM3uPlaylist(value);
        });
        root.addView(load);

        root.addView(cardText("Compatible con entradas #EXTINF y URLs HTTP/HTTPS. "
                + "La playlist queda guardada localmente para volver a abrirla."));
    }

    private void loadM3uPlaylist(String url) {
        showLoading("Cargando playlist M3U…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(25000);
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/2.0 Android");
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
                String body = readAll(conn.getInputStream());
                JSONArray entries = parseM3u(body);
                ui.post(() -> showM3uChannels(url, entries));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar la playlist", e, this::showM3uScreen));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private JSONArray parseM3u(String text) {
        JSONArray out = new JSONArray();
        String pendingName = "";
        String pendingGroup = "";
        String[] lines = text == null ? new String[0] : text.replace("\r", "").split("\n");
        for (String raw : lines) {
            String line = raw == null ? "" : raw.trim();
            if (line.isEmpty()) continue;
            if (line.startsWith("#EXTINF")) {
                int comma = line.lastIndexOf(',');
                pendingName = comma >= 0 && comma + 1 < line.length()
                        ? line.substring(comma + 1).trim() : "Canal";
                pendingGroup = m3uAttr(line, "group-title");
            } else if (!line.startsWith("#") &&
                    (line.startsWith("http://") || line.startsWith("https://"))) {
                try {
                    JSONObject row = new JSONObject();
                    row.put("name", pendingName.isEmpty() ? "Canal" : pendingName);
                    row.put("group", pendingGroup);
                    row.put("url", line);
                    out.put(row);
                } catch (Exception ignored) {}
                pendingName = "";
                pendingGroup = "";
            }
        }
        return out;
    }

    private String m3uAttr(String line, String key) {
        String token = key + "=\"";
        int start = line.indexOf(token);
        if (start < 0) return "";
        start += token.length();
        int end = line.indexOf('"', start);
        if (end <= start) return "";
        return line.substring(start, end);
    }

    private void showM3uChannels(String playlistUrl, JSONArray entries) {
        systemBack = this::showM3uScreen;
        root = baseScreen();
        addBack(this::showM3uScreen);
        addTitle("☰ M3U PLAYER", 27);
        addSubtitle("Entradas: " + entries.length());

        EditText search = input("Buscar en playlist", false);
        root.addView(search);

        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);
        renderM3uChannels(list, playlistUrl, entries, "");

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence text, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                renderM3uChannels(list, playlistUrl, entries, text == null ? "" : text.toString());
            }
            @Override public void afterTextChanged(Editable editable) {}
        });
    }

    private void renderM3uChannels(LinearLayout list, String playlistUrl, JSONArray entries, String query) {
        list.removeAllViews();
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        int shown = 0;
        for (int i = 0; i < entries.length() && shown < 500; i++) {
            JSONObject row = entries.optJSONObject(i);
            if (row == null) continue;
            String name = row.optString("name", "Canal");
            String group = row.optString("group", "");
            String streamUrl = row.optString("url", "");
            String haystack = (name + " " + group).toLowerCase(Locale.ROOT);
            if (!q.isEmpty() && !haystack.contains(q)) continue;

            Button b = listButton((group.isEmpty() ? "" : "[" + group + "]  ") + name);
            b.setOnClickListener(v -> playStream(name, streamUrl, null,
                    () -> showM3uChannels(playlistUrl, entries)));
            list.addView(b);
            shown++;
        }
        if (shown == 0) list.addView(cardText("No se encontraron entradas."));
    }

'''
if marker not in s:
    raise SystemExit('speed method marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 M3U patch applied')
