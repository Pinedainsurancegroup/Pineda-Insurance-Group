from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import org.json.JSONObject;\n',
              'import org.json.JSONObject;\nimport org.xmlpull.v1.XmlPullParser;\n')
s = s.replace('import java.util.concurrent.ExecutorService;\n',
              'import java.util.concurrent.ExecutorService;\nimport java.util.TimeZone;\n')

# Fields/constants for local M3U import.
field = '    private File activeRecordingFile;\n'
if field not in s:
    raise SystemExit('activeRecordingFile marker not found')
extra = '''    private static final int REQ_M3U_FILE = 4101;
    private Uri pendingM3uUri;
'''
if 'REQ_M3U_FILE' not in s:
    s = s.replace(field, field + extra, 1)

# Add activity result handler before showLogin.
marker = '    private void showLogin() {\n'
if marker not in s:
    raise SystemExit('showLogin marker not found')
activity_result = r'''    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_M3U_FILE && resultCode == RESULT_OK && data != null && data.getData() != null) {
            Uri uri = data.getData();
            pendingM3uUri = uri;
            try {
                getContentResolver().takePersistableUriPermission(uri,
                        data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
            } catch (Exception ignored) {}
            loadM3uFromUri(uri);
        }
    }

'''
s = s.replace(marker, activity_result + marker, 1)

# Add source/settings tiles.
settings_marker = '        addCloneSettingsTile(grid, "⬇", "DESCARGAS", this::showDownloadsLibrary);\n'
settings_add = '''        addCloneSettingsTile(grid, "⬇", "DESCARGAS", this::showDownloadsLibrary);
        addCloneSettingsTile(grid, "☰", "M3U / ARCHIVO", this::showM3uScreen);
        addCloneSettingsTile(grid, "EPG", "XMLTV EXTERNO", this::showXmltvScreen);
        addCloneSettingsTile(grid, "DNS", "MULTI-DNS", this::showMultiDnsScreen);
        addCloneSettingsTile(grid, "MAG", "STALKER / MAG", this::showStalkerScreen);
'''
if settings_marker not in s:
    raise SystemExit('settings source tile marker not found')
s = s.replace(settings_marker, settings_add, 1)

# Enhance M3U screen with local import.
m3u_marker = '''        root.addView(load);

        root.addView(cardText("Compatible con entradas #EXTINF y URLs HTTP/HTTPS. "
                + "La playlist queda guardada localmente para volver a abrirla."));
'''
m3u_repl = '''        root.addView(load);

        Button importFile = secondaryButton("IMPORTAR ARCHIVO .M3U / .M3U8");
        importFile.setOnClickListener(v -> openM3uFilePicker());
        root.addView(importFile);

        Button xmltv = secondaryButton("CONFIGURAR XMLTV / EPG EXTERNO");
        xmltv.setOnClickListener(v -> showXmltvScreen());
        root.addView(xmltv);

        root.addView(cardText("Compatible con URL HTTP/HTTPS y archivos locales #EXTM3U. "
                + "Las playlists locales se leen desde el selector de archivos de Android."));
'''
if m3u_marker not in s:
    raise SystemExit('M3U screen marker not found')
s = s.replace(m3u_marker, m3u_repl, 1)

# Extend M3U parser with tvg-id/logo metadata.
old_extinf = '''                pendingName = comma >= 0 && comma + 1 < line.length()
                        ? line.substring(comma + 1).trim() : "Canal";
                pendingGroup = m3uAttr(line, "group-title");
'''
new_extinf = '''                pendingName = comma >= 0 && comma + 1 < line.length()
                        ? line.substring(comma + 1).trim() : "Canal";
                pendingGroup = m3uAttr(line, "group-title");
                pendingTvgId = m3uAttr(line, "tvg-id");
                pendingLogo = m3uAttr(line, "tvg-logo");
'''
if old_extinf not in s:
    raise SystemExit('M3U EXTINF marker not found')
s = s.replace('''        String pendingName = "";
        String pendingGroup = "";
''', '''        String pendingName = "";
        String pendingGroup = "";
        String pendingTvgId = "";
        String pendingLogo = "";
''', 1)
s = s.replace(old_extinf, new_extinf, 1)
old_put = '''                    row.put("name", pendingName.isEmpty() ? "Canal" : pendingName);
                    row.put("group", pendingGroup);
                    row.put("url", line);
                    out.put(row);
'''
new_put = '''                    row.put("name", pendingName.isEmpty() ? "Canal" : pendingName);
                    row.put("group", pendingGroup);
                    row.put("tvg_id", pendingTvgId);
                    row.put("logo", pendingLogo);
                    row.put("url", line);
                    out.put(row);
'''
if old_put not in s:
    raise SystemExit('M3U row marker not found')
s = s.replace(old_put, new_put, 1)
s = s.replace('''                pendingName = "";
                pendingGroup = "";
''', '''                pendingName = "";
                pendingGroup = "";
                pendingTvgId = "";
                pendingLogo = "";
''', 1)

# Insert sources methods before runSpeedTest.
marker2 = '    private void runSpeedTest() {\n'
if marker2 not in s:
    raise SystemExit('runSpeedTest marker not found')
methods = r'''    private void openM3uFilePicker() {
        try {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("*/*");
            intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                    "audio/x-mpegurl", "application/x-mpegURL", "application/vnd.apple.mpegurl",
                    "text/plain", "application/octet-stream"
            });
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(intent, REQ_M3U_FILE);
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo abrir el selector de archivos.", Toast.LENGTH_LONG).show();
        }
    }

    private void loadM3uFromUri(Uri uri) {
        showLoading("Leyendo archivo M3U…");
        io.execute(() -> {
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                String body = readAll(in);
                JSONArray entries = parseM3u(body);
                if (entries.length() == 0) throw new Exception("El archivo no contiene entradas compatibles.");
                ui.post(() -> showM3uChannels(uri.toString(), entries));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo importar M3U", e, this::showM3uScreen));
            }
        });
    }

    private void showXmltvScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("XMLTV / EPG EXTERNO", this::showSettings);

        EditText url = input("URL XMLTV / XML", false);
        if (prefs != null) url.setText(prefs.getString("xmltv_url", ""));
        root.addView(url);

        Button load = cloneGreenButton("CARGAR XMLTV");
        load.setOnClickListener(v -> {
            String value = url.getText().toString().trim();
            if (value.isEmpty()) {
                Toast.makeText(this, "Introduce una URL XMLTV.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit().putString("xmltv_url", value).apply();
            loadXmltvUrl(value);
        });
        root.addView(load);

        root.addView(cardText("XMLTV externo permite consultar la programación de una fuente EPG "
                + "independiente del servidor Xtream."));
    }

    private void loadXmltvUrl(String url) {
        showLoading("Descargando XMLTV…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(30000);
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/4.0.2 (Android)");
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
                JSONArray programs = parseXmltv(conn.getInputStream());
                ui.post(() -> showXmltvPrograms(programs));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("XMLTV", e, this::showXmltvScreen));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private JSONArray parseXmltv(InputStream in) throws Exception {
        JSONArray out = new JSONArray();
        XmlPullParser parser = android.util.Xml.newPullParser();
        parser.setInput(in, "UTF-8");

        String channel = "";
        String start = "";
        String stop = "";
        String title = "";
        String desc = "";
        String tag = "";

        int event = parser.getEventType();
        while (event != XmlPullParser.END_DOCUMENT && out.length() < 2500) {
            if (event == XmlPullParser.START_TAG) {
                tag = parser.getName();
                if ("programme".equals(tag)) {
                    channel = parser.getAttributeValue(null, "channel");
                    start = parser.getAttributeValue(null, "start");
                    stop = parser.getAttributeValue(null, "stop");
                    title = "";
                    desc = "";
                }
            } else if (event == XmlPullParser.TEXT) {
                String text = parser.getText();
                if ("title".equals(tag)) title += text;
                else if ("desc".equals(tag)) desc += text;
            } else if (event == XmlPullParser.END_TAG) {
                String end = parser.getName();
                if ("programme".equals(end)) {
                    long startMs = parseXmltvTime(start);
                    long stopMs = parseXmltvTime(stop);
                    long now = System.currentTimeMillis();
                    if (stopMs <= 0 || stopMs >= now - 6L * 3600000L) {
                        JSONObject row = new JSONObject();
                        row.put("channel", channel == null ? "" : channel);
                        row.put("title", title.trim());
                        row.put("desc", desc.trim());
                        row.put("start_ms", startMs);
                        row.put("stop_ms", stopMs);
                        out.put(row);
                    }
                }
                tag = "";
            }
            event = parser.next();
        }
        return out;
    }

    private long parseXmltvTime(String raw) {
        if (raw == null) return 0L;
        String value = raw.trim();
        try {
            SimpleDateFormat f = new SimpleDateFormat("yyyyMMddHHmmss Z", Locale.US);
            f.setLenient(true);
            Date d = f.parse(value);
            return d == null ? 0L : d.getTime();
        } catch (Exception ignored) {}
        try {
            String compact = value.length() >= 14 ? value.substring(0, 14) : value;
            SimpleDateFormat f = new SimpleDateFormat("yyyyMMddHHmmss", Locale.US);
            f.setTimeZone(TimeZone.getDefault());
            Date d = f.parse(compact);
            return d == null ? 0L : d.getTime();
        } catch (Exception ignored) {}
        return 0L;
    }

    private void showXmltvPrograms(JSONArray programs) {
        systemBack = this::showXmltvScreen;
        root = cloneScreen();
        addCloneHeader("XMLTV / PROGRAMACIÓN", this::showXmltvScreen);

        EditText search = input("Buscar canal o programa", false);
        root.addView(search);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);

        Runnable render = () -> {
            list.removeAllViews();
            String q = search.getText().toString().trim().toLowerCase(Locale.ROOT);
            long now = System.currentTimeMillis();
            int shown = 0;
            for (int i = 0; i < programs.length() && shown < 300; i++) {
                JSONObject row = programs.optJSONObject(i);
                if (row == null) continue;
                String channel = row.optString("channel", "");
                String title = row.optString("title", "Programa");
                String desc = row.optString("desc", "");
                String hay = (channel + " " + title + " " + desc).toLowerCase(Locale.ROOT);
                if (!q.isEmpty() && !hay.contains(q)) continue;
                long start = row.optLong("start_ms", 0L);
                long stop = row.optLong("stop_ms", 0L);
                String when = "";
                if (start > 0) {
                    when = new SimpleDateFormat("MMM d · h:mm a", Locale.getDefault()).format(new Date(start));
                    if (stop > start) when += " - " +
                            new SimpleDateFormat("h:mm a", Locale.getDefault()).format(new Date(stop));
                }
                String status = start <= now && stop > now ? "AHORA · " : "";
                TextView card = cardText(status + channel + "\n" + when + "\n" + title +
                        (desc.isEmpty() ? "" : "\n" + desc));
                list.addView(card);
                shown++;
            }
            if (shown == 0) list.addView(cardText("No se encontraron programas."));
        };
        render.run();
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render.run(); }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private JSONArray loadDnsList() {
        try {
            return new JSONArray(prefs == null ? "[]" : prefs.getString("multi_dns_json", "[]"));
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    private void saveDnsList(JSONArray arr) {
        if (prefs != null) prefs.edit().putString("multi_dns_json", arr.toString()).apply();
    }

    private void showMultiDnsScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("MULTI-DNS", this::showSettings);

        root.addView(cardText("Servidor actual:\n" + server));

        EditText input = input("https://servidor:puerto", false);
        root.addView(input);

        Button add = cloneGreenButton("AÑADIR DNS / SERVIDOR");
        add.setOnClickListener(v -> {
            String value = normalizeServer(input.getText().toString());
            if (value.isEmpty()) return;
            JSONArray arr = loadDnsList();
            boolean exists = false;
            for (int i = 0; i < arr.length(); i++) {
                if (value.equalsIgnoreCase(arr.optString(i))) { exists = true; break; }
            }
            if (!exists) arr.put(value);
            saveDnsList(arr);
            showMultiDnsScreen();
        });
        root.addView(add);

        JSONArray arr = loadDnsList();
        for (int i = 0; i < arr.length(); i++) {
            String value = arr.optString(i, "");
            if (value.isEmpty()) continue;
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);

            Button use = cloneGrayButton((value.equalsIgnoreCase(server) ? "✓  " : "") + value);
            use.setOnClickListener(v -> testAndSwitchDns(value));
            row.addView(use, new LinearLayout.LayoutParams(0, dp(58), 1f));

            int index = i;
            Button del = cloneRedButton("BORRAR");
            del.setOnClickListener(v -> {
                JSONArray old = loadDnsList();
                JSONArray next = new JSONArray();
                for (int j = 0; j < old.length(); j++) if (j != index) next.put(old.optString(j));
                saveDnsList(next);
                showMultiDnsScreen();
            });
            row.addView(del, new LinearLayout.LayoutParams(dp(120), dp(58)));
            root.addView(row);
        }
    }

    private void testAndSwitchDns(String candidate) {
        String oldServer = server;
        showLoading("Probando servidor…");
        io.execute(() -> {
            try {
                server = normalizeServer(candidate);
                JSONObject json = new JSONObject(request(null, null));
                JSONObject user = json.optJSONObject("user_info");
                if (user == null) throw new Exception("Sin user_info");
                String auth = String.valueOf(user.opt("auth"));
                String status = user.optString("status", "");
                if (!("1".equals(auth) || "Active".equalsIgnoreCase(status))) {
                    throw new Exception("Cuenta no activa en este servidor.");
                }
                accountInfo = user;
                if (prefs != null) prefs.edit().putString("server", server).apply();
                ui.post(() -> {
                    Toast.makeText(this, "Servidor cambiado.", Toast.LENGTH_SHORT).show();
                    showDashboard();
                });
            } catch (Exception e) {
                server = oldServer;
                ui.post(() -> showErrorScreen("Multi-DNS", e, this::showMultiDnsScreen));
            }
        });
    }

    private void showStalkerScreen() {
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

        Button connect = cloneGreenButton("CONECTAR PORTAL");
        connect.setOnClickListener(v -> {
            String purl = portal.getText().toString().trim();
            String m = mac.getText().toString().trim().toUpperCase(Locale.US);
            if (purl.isEmpty() || m.isEmpty()) {
                Toast.makeText(this, "Completa portal y MAC.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit()
                    .putString("stalker_portal", purl)
                    .putString("stalker_mac", m)
                    .apply();
            loadStalkerChannels(purl, m);
        });
        root.addView(connect);

        root.addView(cardText("Compatibilidad básica con portales Stalker/MAG autorizados: "
                + "handshake, perfil, canales Live y creación del enlace de reproducción."));
    }

    private String stalkerEndpoint(String portal) {
        String p = normalizeServer(portal);
        if (p.endsWith("/c")) p = p.substring(0, p.length() - 2);
        if (p.endsWith("/portal.php")) p = p.substring(0, p.length() - "/portal.php".length());
        return p + "/portal.php";
    }

    private String stalkerGet(String url, String mac, String token) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(25000);
        conn.setInstanceFollowRedirects(true);
        conn.setRequestProperty("User-Agent",
                "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG254 stbapp Safari/533.3");
        conn.setRequestProperty("X-User-Agent", "Model: MAG254; Link: Ethernet");
        conn.setRequestProperty("Cookie", "mac=" + Uri.encode(mac) +
                "; stb_lang=en; timezone=America%2FLos_Angeles;");
        if (token != null && !token.isEmpty()) conn.setRequestProperty("Authorization", "Bearer " + token);

        int code = conn.getResponseCode();
        String body = readAll(code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream());
        conn.disconnect();
        if (code < 200 || code >= 300) throw new Exception("Portal HTTP " + code);
        if (body.trim().isEmpty()) throw new Exception("Respuesta vacía del portal.");
        return body;
    }

    private void loadStalkerChannels(String portal, String mac) {
        showLoading("Conectando Stalker/MAG…");
        io.execute(() -> {
            try {
                String endpoint = stalkerEndpoint(portal);
                String handshakeUrl = endpoint + "?type=stb&action=handshake&token=&JsHttpRequest=1-xml";
                JSONObject handshake = new JSONObject(stalkerGet(handshakeUrl, mac, ""));
                JSONObject hjs = handshake.optJSONObject("js");
                String token = hjs == null ? "" : hjs.optString("token", "");
                if (token.isEmpty()) throw new Exception("El portal no devolvió token.");

                try {
                    stalkerGet(endpoint + "?type=stb&action=get_profile&JsHttpRequest=1-xml", mac, token);
                } catch (Exception ignored) {}

                String channelsBody = stalkerGet(endpoint +
                        "?type=itv&action=get_all_channels&JsHttpRequest=1-xml", mac, token);
                JSONObject channelsJson = new JSONObject(channelsBody);
                Object jsObj = channelsJson.opt("js");
                JSONArray channels = null;
                if (jsObj instanceof JSONObject) {
                    JSONObject js = (JSONObject) jsObj;
                    channels = js.optJSONArray("data");
                    if (channels == null) channels = js.optJSONArray("channels");
                } else if (jsObj instanceof JSONArray) {
                    channels = (JSONArray) jsObj;
                }
                if (channels == null) channels = new JSONArray();
                JSONArray finalChannels = channels;
                ui.post(() -> showStalkerChannels(portal, mac, token, finalChannels));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, this::showStalkerScreen));
            }
        });
    }

    private void showStalkerChannels(String portal, String mac, String token, JSONArray channels) {
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
            for (int i = 0; i < channels.length() && shown < 500; i++) {
                JSONObject row = channels.optJSONObject(i);
                if (row == null) continue;
                String name = row.optString("name", "Canal");
                if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;
                String cmd = row.optString("cmd", "");
                Button b = listButton(name);
                b.setOnClickListener(v -> createAndPlayStalkerLink(portal, mac, token, cmd, name,
                        () -> showStalkerChannels(portal, mac, token, channels)));
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

    private void createAndPlayStalkerLink(String portal, String mac, String token, String cmd,
                                          String name, Runnable back) {
        if (cmd == null || cmd.trim().isEmpty()) {
            Toast.makeText(this, "El portal no proporcionó comando de reproducción.", Toast.LENGTH_LONG).show();
            return;
        }
        if (cmd.startsWith("http://") || cmd.startsWith("https://")) {
            playStream(name, cmd, null, back);
            return;
        }

        showLoading("Creando enlace de reproducción…");
        io.execute(() -> {
            try {
                String endpoint = stalkerEndpoint(portal);
                String url = endpoint + "?type=itv&action=create_link&cmd=" + enc(cmd)
                        + "&series=0&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml";
                JSONObject response = new JSONObject(stalkerGet(url, mac, token));
                JSONObject js = response.optJSONObject("js");
                String play = js == null ? "" : js.optString("cmd", "");
                play = cleanStalkerPlayUrl(play);
                if (play.isEmpty()) throw new Exception("No se pudo crear el enlace.");
                String finalPlay = play;
                ui.post(() -> playStream(name, finalPlay, null, back));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Stalker / MAG", e, back));
            }
        });
    }

    private String cleanStalkerPlayUrl(String cmd) {
        if (cmd == null) return "";
        String value = cmd.trim();
        if (value.startsWith("ffmpeg ")) value = value.substring(7).trim();
        if (value.startsWith("auto ")) value = value.substring(5).trim();
        int http = value.indexOf("http://");
        int https = value.indexOf("https://");
        int idx = http >= 0 ? http : https;
        if (idx > 0) value = value.substring(idx);
        return value.trim();
    }

'''
s = s.replace(marker2, methods + marker2, 1)

p.write_text(s)
print('v2.4 M3U file XMLTV Multi-DNS and Stalker/MAG patch applied')
