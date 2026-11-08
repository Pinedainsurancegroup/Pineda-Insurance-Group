from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Media3 external subtitle MIME support.
s = s.replace('import androidx.media3.common.MediaItem;\n',
              'import androidx.media3.common.MediaItem;\nimport androidx.media3.common.MimeTypes;\n')

# Pending external subtitle state.
field = '    private File activeRecordingFile;\n'
if field not in s:
    raise SystemExit('activeRecordingFile marker not found')
if 'pendingExternalSubtitlePath' not in s:
    s = s.replace(field, field + '''    private String pendingExternalSubtitlePath = "";
    private String pendingExternalSubtitleLanguage = "";
''', 1)

# Add OpenSubtitles settings tile.
settings_marker = '        addCloneSettingsTile(grid, "$", "CLIENT AREA", this::showClientAreaScreen);\n'
settings_add = '''        addCloneSettingsTile(grid, "$", "CLIENT AREA", this::showClientAreaScreen);
        addCloneSettingsTile(grid, "CC", "OPENSUBTITLES", this::showOpenSubtitlesSettings);
'''
if settings_marker not in s:
    raise SystemExit('OpenSubtitles settings marker not found')
s = s.replace(settings_marker, settings_add, 1)

# Use professional EPG grid from dashboard.
epg_tile = '        addCloneSmallTile(lowerGrid, "▣", "EPG", this::loadEpgChannels);\n'
if epg_tile not in s:
    raise SystemExit('clone EPG tile marker not found')
s = s.replace(epg_tile, '        addCloneSmallTile(lowerGrid, "▣", "EPG", this::loadEpgGrid);\n', 1)

# Add online subtitles button on movie detail screen.
vod_marker = '''        details.addView(actions);

        if (saved > 0) {
'''
vod_repl = '''        details.addView(actions);

        Button onlineSubs = cloneGrayButton("CC  OpenSubtitles");
        onlineSubs.setOnClickListener(v -> showOpenSubtitleSearch(id, finalTitle, payload,
                () -> showVodDetails(id, fallbackTitle, ext, fallbackArt, payload, back)));
        details.addView(onlineSubs, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(54)));

        if (saved > 0) {
'''
if vod_marker not in s:
    raise SystemExit('VOD actions marker not found for OpenSubtitles')
s = s.replace(vod_marker, vod_repl, 1)

# Load saved external subtitle before tracked playback.
tracked_marker = '''        pendingResumeMs = getSavedPosition(currentWatchType, currentWatchId);
        resumeAttempts = 0;
'''
tracked_repl = '''        pendingResumeMs = getSavedPosition(currentWatchType, currentWatchId);
        pendingExternalSubtitlePath = prefs == null ? "" :
                prefs.getString(scopedKey("subtitle_file_" + currentWatchType + "_" + currentWatchId), "");
        pendingExternalSubtitleLanguage = prefs == null ? "" :
                prefs.getString(scopedKey("subtitle_language_" + currentWatchType + "_" + currentWatchId), "");
        resumeAttempts = 0;
'''
if tracked_marker not in s:
    raise SystemExit('tracked playback marker not found')
s = s.replace(tracked_marker, tracked_repl, 1)

tracked_back = '''            stopProgressTracking();
            currentWatchType = "";
            currentWatchId = "";
            back.run();
'''
tracked_back_repl = '''            stopProgressTracking();
            currentWatchType = "";
            currentWatchId = "";
            pendingExternalSubtitlePath = "";
            pendingExternalSubtitleLanguage = "";
            back.run();
'''
if tracked_back not in s:
    raise SystemExit('tracked playback back marker not found')
s = s.replace(tracked_back, tracked_back_repl, 1)

# Build player MediaItems with external subtitle when configured.
player_mode = '''        String playerMode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        int networkCache = prefs == null ? 2500 : prefs.getInt("network_cache_ms", 2500);
'''
player_mode_repl = '''        String configuredPlayerMode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        final String playerMode = (!pendingExternalSubtitlePath.isEmpty() && "vlc".equals(configuredPlayerMode))
                ? "exo" : configuredPlayerMode;
        int networkCache = prefs == null ? 2500 : prefs.getInt("network_cache_ms", 2500);
'''
if player_mode not in s:
    raise SystemExit('player mode marker not found')
s = s.replace(player_mode, player_mode_repl, 1)

s = s.replace('player.setMediaItem(MediaItem.fromUri(Uri.parse(urls[attempt[0]])));',
              'player.setMediaItem(buildPlaybackMediaItem(urls[attempt[0]]));')
s = s.replace('player.setMediaItem(MediaItem.fromUri(Uri.parse(urls[0])));',
              'player.setMediaItem(buildPlaybackMediaItem(urls[0]));')

# Helper before VLC playback.
vlc_marker = '    private void startVlcPlayback(VLCVideoLayout vlcView, PlayerView playerView,\n'
if vlc_marker not in s:
    raise SystemExit('VLC playback marker not found')
media_helper = r'''    private MediaItem buildPlaybackMediaItem(String url) {
        MediaItem.Builder builder = new MediaItem.Builder().setUri(Uri.parse(url));
        if (pendingExternalSubtitlePath != null && !pendingExternalSubtitlePath.isEmpty()) {
            try {
                File file = new File(pendingExternalSubtitlePath);
                if (file.isFile()) {
                    String lower = file.getName().toLowerCase(Locale.ROOT);
                    String mime = lower.endsWith(".vtt") ? MimeTypes.TEXT_VTT : MimeTypes.APPLICATION_SUBRIP;
                    MediaItem.SubtitleConfiguration subtitle =
                            new MediaItem.SubtitleConfiguration.Builder(Uri.fromFile(file))
                                    .setMimeType(mime)
                                    .setLanguage(pendingExternalSubtitleLanguage.isEmpty()
                                            ? "es" : pendingExternalSubtitleLanguage)
                                    .setSelectionFlags(C.SELECTION_FLAG_DEFAULT)
                                    .build();
                    builder.setSubtitleConfigurations(Collections.singletonList(subtitle));
                }
            } catch (Exception ignored) {}
        }
        return builder.build();
    }

'''
s = s.replace(vlc_marker, media_helper + vlc_marker, 1)

# Insert OpenSubtitles and EPG-grid methods before M3U screen.
marker = '    private void showM3uScreen() {\n'
if marker not in s:
    raise SystemExit('showM3uScreen marker not found for v2.6')
methods = r'''    private void showOpenSubtitlesSettings() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("OPENSUBTITLES", this::showSettings);

        EditText apiKey = input("OpenSubtitles API Key", false);
        EditText languages = input("Idiomas · es,en", false);
        if (prefs != null) {
            apiKey.setText(prefs.getString("opensubtitles_api_key", ""));
            languages.setText(prefs.getString("opensubtitles_languages", "es,en"));
        }
        root.addView(apiKey);
        root.addView(languages);

        Button save = cloneGreenButton("GUARDAR");
        save.setOnClickListener(v -> {
            if (prefs != null) prefs.edit()
                    .putString("opensubtitles_api_key", apiKey.getText().toString().trim())
                    .putString("opensubtitles_languages", languages.getText().toString().trim())
                    .apply();
            Toast.makeText(this, "OpenSubtitles configurado.", Toast.LENGTH_SHORT).show();
        });
        root.addView(save);

        root.addView(cardText("La API Key no viene incorporada en PIMFLEX TV. "
                + "Puedes conectar tu propia cuenta de OpenSubtitles y mantener el control de la integración."));
    }

    private void showOpenSubtitleSearch(String vodId, String title, JSONObject payload, Runnable back) {
        String apiKey = prefs == null ? "" : prefs.getString("opensubtitles_api_key", "").trim();
        if (apiKey.isEmpty()) {
            Toast.makeText(this, "Configura primero tu API Key de OpenSubtitles.", Toast.LENGTH_LONG).show();
            showOpenSubtitlesSettings();
            return;
        }

        JSONObject info = payload == null ? null : payload.optJSONObject("info");
        String tmdbId = info == null ? "" : info.optString("tmdb_id", info.optString("tmdb", ""));
        String languages = prefs == null ? "es,en" : prefs.getString("opensubtitles_languages", "es,en");

        showLoading("Buscando subtítulos…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                String query;
                if (!tmdbId.isEmpty() && !"0".equals(tmdbId)) {
                    query = "tmdb_id=" + enc(tmdbId);
                } else {
                    query = "query=" + enc(title);
                }
                if (!languages.trim().isEmpty()) query += "&languages=" + enc(languages.replace(" ", ""));

                URL url = new URL("https://api.opensubtitles.com/api/v1/subtitles?" + query);
                conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(25000);
                conn.setRequestProperty("Api-Key", apiKey);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV v2.6");
                conn.setRequestProperty("Accept", "application/json");
                int code = conn.getResponseCode();
                String body = readAll(code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream());
                if (code < 200 || code >= 300) throw new Exception("OpenSubtitles HTTP " + code);
                JSONObject json = new JSONObject(body);
                JSONArray data = json.optJSONArray("data");
                if (data == null) data = new JSONArray();
                JSONArray finalData = data;
                ui.post(() -> showOpenSubtitleResults(vodId, title, finalData, back));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("OpenSubtitles", e, back));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void showOpenSubtitleResults(String vodId, String title, JSONArray data, Runnable back) {
        systemBack = back;
        root = cloneScreen();
        addCloneHeader("SUBTÍTULOS · " + title, back);

        String saved = prefs == null ? "" :
                prefs.getString(scopedKey("subtitle_file_vod_" + vodId), "");
        if (!saved.isEmpty()) {
            root.addView(cardText("Subtítulo externo activo:\n" + new File(saved).getName()));
            Button clear = cloneRedButton("QUITAR SUBTÍTULO EXTERNO");
            clear.setOnClickListener(v -> {
                if (prefs != null) prefs.edit()
                        .remove(scopedKey("subtitle_file_vod_" + vodId))
                        .remove(scopedKey("subtitle_language_vod_" + vodId))
                        .apply();
                showOpenSubtitleResults(vodId, title, data, back);
            });
            root.addView(clear);
        }

        if (data.length() == 0) {
            root.addView(cardText("No se encontraron subtítulos."));
            return;
        }

        int limit = Math.min(80, data.length());
        for (int i = 0; i < limit; i++) {
            JSONObject row = data.optJSONObject(i);
            if (row == null) continue;
            JSONObject attr = row.optJSONObject("attributes");
            if (attr == null) continue;

            String lang = attr.optString("language", "");
            String release = attr.optString("release", attr.optString("feature_details", ""));
            JSONArray files = attr.optJSONArray("files");
            if (files == null || files.length() == 0) continue;
            JSONObject first = files.optJSONObject(0);
            if (first == null) continue;
            long fileId = first.optLong("file_id", 0L);
            String fileName = first.optString("file_name", "");
            if (fileId <= 0) continue;

            String labelText = (lang.isEmpty() ? "Subtítulo" : lang.toUpperCase(Locale.ROOT))
                    + (fileName.isEmpty() ? "" : " · " + fileName)
                    + (release.isEmpty() ? "" : "\n" + release);
            Button b = listButton(labelText);
            b.setOnClickListener(v -> downloadOpenSubtitle(vodId, title, lang, fileId, data, back));
            root.addView(b);
        }
    }

    private void downloadOpenSubtitle(String vodId, String title, String language, long fileId,
                                      JSONArray results, Runnable back) {
        String apiKey = prefs == null ? "" : prefs.getString("opensubtitles_api_key", "").trim();
        showLoading("Descargando subtítulo…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL("https://api.opensubtitles.com/api/v1/download").openConnection();
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(25000);
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setRequestProperty("Api-Key", apiKey);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV v2.6");
                conn.setRequestProperty("Accept", "application/json");
                conn.setRequestProperty("Content-Type", "application/json");

                JSONObject bodyJson = new JSONObject();
                bodyJson.put("file_id", fileId);
                byte[] body = bodyJson.toString().getBytes(StandardCharsets.UTF_8);
                try (java.io.OutputStream out = conn.getOutputStream()) {
                    out.write(body);
                }

                int code = conn.getResponseCode();
                String response = readAll(code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream());
                if (code < 200 || code >= 300) throw new Exception("OpenSubtitles HTTP " + code);
                String link = new JSONObject(response).optString("link", "");
                if (link.isEmpty()) throw new Exception("OpenSubtitles no devolvió enlace.");

                File base = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                if (base == null) throw new Exception("Sin almacenamiento disponible.");
                File dir = new File(base, "Subtitles");
                if (!dir.exists() && !dir.mkdirs()) throw new Exception("No se pudo crear carpeta Subtitles.");

                String safe = title.replaceAll("[^A-Za-z0-9._ -]", "_").trim();
                if (safe.isEmpty()) safe = "subtitle";
                File file = new File(dir, safe + "_" +
                        (language == null || language.isEmpty() ? "sub" : language) + ".srt");

                HttpURLConnection fileConn = (HttpURLConnection) new URL(link).openConnection();
                fileConn.setConnectTimeout(15000);
                fileConn.setReadTimeout(30000);
                fileConn.setInstanceFollowRedirects(true);
                try (InputStream in = fileConn.getInputStream();
                     FileOutputStream out = new FileOutputStream(file)) {
                    byte[] buf = new byte[16 * 1024];
                    int n;
                    while ((n = in.read(buf)) >= 0) out.write(buf, 0, n);
                } finally {
                    fileConn.disconnect();
                }

                if (prefs != null) prefs.edit()
                        .putString(scopedKey("subtitle_file_vod_" + vodId), file.getAbsolutePath())
                        .putString(scopedKey("subtitle_language_vod_" + vodId),
                                language == null ? "" : language)
                        .apply();

                ui.post(() -> {
                    Toast.makeText(this, "Subtítulo guardado y activado.", Toast.LENGTH_LONG).show();
                    showOpenSubtitleResults(vodId, title, results, back);
                });
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("OpenSubtitles", e, back));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void loadEpgGrid() {
        showLoading("Preparando guía EPG…");
        io.execute(() -> {
            try {
                JSONArray channels = new JSONArray(request("get_live_streams", null));
                int limit = Math.min(32, channels.length());
                JSONArray[] listings = new JSONArray[limit];
                CountDownLatch latch = new CountDownLatch(limit);
                ExecutorService pool = Executors.newFixedThreadPool(6);

                for (int i = 0; i < limit; i++) {
                    final int index = i;
                    final JSONObject channel = channels.optJSONObject(i);
                    pool.execute(() -> {
                        try {
                            if (channel == null) return;
                            String id = String.valueOf(channel.opt("stream_id"));
                            JSONObject epg = new JSONObject(request("get_short_epg",
                                    "stream_id=" + enc(id) + "&limit=8"));
                            listings[index] = epg.optJSONArray("epg_listings");
                        } catch (Exception ignored) {
                        } finally {
                            latch.countDown();
                        }
                    });
                }

                latch.await(20, TimeUnit.SECONDS);
                pool.shutdownNow();
                ui.post(() -> showEpgGrid(channels, listings, limit));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("EPG", e, this::showDashboard));
            }
        });
    }

    private void showEpgGrid(JSONArray channels, JSONArray[] listings, int limit) {
        systemBack = this::showDashboard;
        root = cloneScreen();
        addCloneHeader("EPG · GUÍA COMPLETA", this::showDashboard);

        TextView legend = label("● AHORA   ·   Selecciona un programa para abrir el canal. "
                + "Los programas pasados con Catch-Up intentan reproducir el archivo.");
        legend.setTextColor(Color.rgb(185, 190, 205));
        legend.setPadding(dp(8), 0, dp(8), dp(8));
        root.addView(legend);

        long nowSec = System.currentTimeMillis() / 1000L;
        for (int i = 0; i < limit; i++) {
            JSONObject channel = channels.optJSONObject(i);
            if (channel == null) continue;
            String channelName = channel.optString("name", "Canal");
            String streamId = String.valueOf(channel.opt("stream_id"));
            boolean archive = "1".equals(String.valueOf(channel.opt("tv_archive"))) ||
                    channel.optBoolean("tv_archive", false);

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(0, dp(3), 0, dp(3));

            Button channelButton = cloneGrayButton(channelName);
            int channelIndex = i;
            channelButton.setOnClickListener(v -> showLiveTvStudio(channels, channelIndex,
                    () -> showEpgGrid(channels, listings, limit)));
            row.addView(channelButton, new LinearLayout.LayoutParams(dp(245), dp(78)));

            android.widget.HorizontalScrollView scroller = new android.widget.HorizontalScrollView(this);
            scroller.setHorizontalScrollBarEnabled(false);
            LinearLayout programs = new LinearLayout(this);
            programs.setOrientation(LinearLayout.HORIZONTAL);
            scroller.addView(programs);

            JSONArray epg = listings == null || i >= listings.length ? null : listings[i];
            if (epg == null || epg.length() == 0) {
                programs.addView(cardText("Sin EPG"), new LinearLayout.LayoutParams(dp(220), dp(78)));
            } else {
                int count = Math.min(8, epg.length());
                for (int j = 0; j < count; j++) {
                    JSONObject program = epg.optJSONObject(j);
                    if (program == null) continue;
                    String title = decodeMaybeBase64(program.optString("title", "Programa"));
                    long start = epgEpoch(program, "start_timestamp", "start");
                    long stop = epgEpoch(program, "stop_timestamp", "end");
                    boolean isNow = start > 0 && stop > start && nowSec >= start && nowSec < stop;
                    String time = start > 0 ? new SimpleDateFormat("h:mm a", Locale.getDefault())
                            .format(new Date(start * 1000L)) : "";
                    Button pbtn = cloneGrayButton((isNow ? "● AHORA\n" : "") +
                            (time.isEmpty() ? "" : time + "\n") + title);
                    pbtn.setTextSize(13);
                    LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(dp(245), dp(78));
                    pp.setMargins(dp(3), 0, dp(3), 0);
                    programs.addView(pbtn, pp);

                    long startFinal = start;
                    long stopFinal = stop;
                    if (archive && stopFinal > startFinal && stopFinal < nowSec) {
                        int durationMin = (int) Math.max(1L, (stopFinal - startFinal + 59L) / 60L);
                        pbtn.setOnClickListener(v -> playCatchup(streamId, title, startFinal, durationMin,
                                () -> showEpgGrid(channels, listings, limit)));
                    } else {
                        pbtn.setOnClickListener(v -> showLiveTvStudio(channels, channelIndex,
                                () -> showEpgGrid(channels, listings, limit)));
                    }
                }
            }

            row.addView(scroller, new LinearLayout.LayoutParams(0, dp(84), 1f));
            root.addView(row);
        }
    }

'''
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2.6 EPG grid and OpenSubtitles patch applied')
