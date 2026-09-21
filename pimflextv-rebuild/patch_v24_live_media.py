from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Imports for recordings/local files.
s = s.replace('import java.io.InputStreamReader;\n',
              'import java.io.InputStreamReader;\nimport java.io.BufferedInputStream;\nimport java.io.File;\nimport java.io.FileOutputStream;\n')
s = s.replace('import java.text.DateFormat;\n',
              'import java.text.DateFormat;\nimport java.text.SimpleDateFormat;\n')

# Fields.
field = '    private JSONArray cloneCategoryArray = new JSONArray();\n'
if field not in s:
    raise SystemExit('cloneCategoryArray field marker not found')
extra = '''    private ExoPlayer livePreviewPlayer;
    private final ExecutorService recorderIo = Executors.newSingleThreadExecutor();
    private volatile boolean recordingActive = false;
    private volatile HttpURLConnection recordingConnection;
    private File activeRecordingFile;
'''
if 'private ExoPlayer livePreviewPlayer;' not in s:
    s = s.replace(field, field + extra, 1)

# Clean up preview/recorder.
old_destroy = '''    protected void onDestroy() {
        releasePlayer();
        io.shutdownNow();
        super.onDestroy();
    }
'''
new_destroy = '''    protected void onDestroy() {
        stopRecording(false);
        releaseLivePreview();
        releasePlayer();
        recorderIo.shutdownNow();
        io.shutdownNow();
        super.onDestroy();
    }
'''
if old_destroy not in s:
    raise SystemExit('onDestroy marker not found')
s = s.replace(old_destroy, new_destroy, 1)

base_marker = '''    private LinearLayout baseScreen() {
        releaseMultiPlayers();
        releasePlayer();
'''
base_repl = '''    private LinearLayout baseScreen() {
        releaseLivePreview();
        releaseMultiPlayers();
        releasePlayer();
'''
if base_marker not in s:
    raise SystemExit('baseScreen marker not found')
s = s.replace(base_marker, base_repl, 1)

# Open original-style live studio instead of jumping straight to fullscreen.
old_live_click = '''            card.setOnClickListener(v -> runWithParentalGate(name, () ->
                    playLiveWithZapping(arr, liveIndex,
                            () -> showItems("live", categoryId, categoryName, arr))));
'''
new_live_click = '''            card.setOnClickListener(v -> runWithParentalGate(name, () ->
                    showLiveTvStudio(arr, liveIndex,
                            () -> showItems("live", categoryId, categoryName, arr))));
'''
if old_live_click not in s:
    raise SystemExit('live grid click marker not found')
s = s.replace(old_live_click, new_live_click, 1)

# Add settings tiles.
settings_marker = '        addCloneSettingsTile(grid, "▣", "Log in on TV", this::showCloneLoginOnTv);\n'
settings_add = '''        addCloneSettingsTile(grid, "▣", "Log in on TV", this::showCloneLoginOnTv);
        addCloneSettingsTile(grid, "♫", "RADIO", this::loadRadioStreams);
        addCloneSettingsTile(grid, "●", "GRABACIONES", this::showRecordingCenter);
        addCloneSettingsTile(grid, "⬇", "DESCARGAS", this::showDownloadsLibrary);
'''
if settings_marker not in s:
    raise SystemExit('settings tile marker not found')
s = s.replace(settings_marker, settings_add, 1)

# Insert live/radio/recording methods before M3U screen.
marker = '    private void showM3uScreen() {\n'
if marker not in s:
    raise SystemExit('showM3uScreen marker not found')
methods = r'''    private void showLiveTvStudio(JSONArray channels, int index, Runnable back) {
        releaseLivePreview();
        releasePlayer();
        releaseMultiPlayers();

        if (channels == null || channels.length() == 0) {
            showErrorScreen("TV en directo", new Exception("No hay canales disponibles."), back);
            return;
        }
        int normalized = Math.max(0, Math.min(index, channels.length() - 1));
        JSONObject current = channels.optJSONObject(normalized);
        if (current == null) {
            showErrorScreen("TV en directo", new Exception("Canal inválido."), back);
            return;
        }

        String currentName = current.optString("name", "Canal");
        String currentId = String.valueOf(current.opt("stream_id"));
        systemBack = back;

        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundResource(R.drawable.clone_screen_bg);
        screen.setPadding(dp(10), dp(8), dp(10), dp(8));
        setContentView(screen);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        Button backBtn = cloneGrayButton("←");
        backBtn.setOnClickListener(v -> back.run());
        header.addView(backBtn, new LinearLayout.LayoutParams(dp(68), dp(52)));

        TextView title = label("TV EN DIRECTO  |  " + currentName);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextSize(19);
        title.setGravity(Gravity.CENTER_VERTICAL);
        header.addView(title, new LinearLayout.LayoutParams(0, dp(52), 1f));

        Button full = cloneGrayButton("PANTALLA COMPLETA");
        full.setOnClickListener(v -> playLiveWithZapping(channels, normalized,
                () -> showLiveTvStudio(channels, normalized, back)));
        header.addView(full, new LinearLayout.LayoutParams(dp(210), dp(48)));

        screen.addView(header);

        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.HORIZONTAL);
        main.setGravity(Gravity.TOP);
        screen.addView(main, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        ScrollView channelScroll = new ScrollView(this);
        LinearLayout channelList = new LinearLayout(this);
        channelList.setOrientation(LinearLayout.VERTICAL);
        channelList.setBackgroundColor(Color.BLACK);
        channelScroll.addView(channelList);
        main.addView(channelScroll, new LinearLayout.LayoutParams(
                dp(isTvLayout() ? 330 : 270), ViewGroup.LayoutParams.MATCH_PARENT));

        TextView channelsTitle = label("CANALES");
        channelsTitle.setTypeface(Typeface.DEFAULT_BOLD);
        channelsTitle.setGravity(Gravity.CENTER);
        channelsTitle.setPadding(0, dp(8), 0, dp(8));
        channelList.addView(channelsTitle);

        int start = Math.max(0, normalized - 35);
        int end = Math.min(channels.length(), start + 80);
        for (int i = start; i < end; i++) {
            JSONObject row = channels.optJSONObject(i);
            if (row == null) continue;
            String name = row.optString("name", "Canal");
            Button b = listButton((i == normalized ? "▶  " : "") + name);
            b.setBackgroundColor(i == normalized ? Color.rgb(47, 146, 230) : Color.BLACK);
            int selectedIndex = i;
            b.setOnClickListener(v -> showLiveTvStudio(channels, selectedIndex, back));
            channelList.addView(b);
        }

        LinearLayout center = new LinearLayout(this);
        center.setOrientation(LinearLayout.VERTICAL);
        center.setPadding(dp(8), 0, dp(8), 0);
        main.addView(center, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));

        PlayerView preview = new PlayerView(this);
        preview.setUseController(true);
        preview.setKeepScreenOn(true);
        center.addView(preview, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        TextView previewState = label("Cargando canal…");
        previewState.setGravity(Gravity.CENTER);
        previewState.setTextColor(Color.LTGRAY);
        center.addView(previewState, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(34)));

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER);

        Button favorite = cloneGrayButton(isFavorite("live", currentId) ? "♥ FAVORITO" : "♡ FAVORITO");
        favorite.setOnClickListener(v -> {
            toggleFavorite("live", currentId);
            favorite.setText(isFavorite("live", currentId) ? "♥ FAVORITO" : "♡ FAVORITO");
        });
        actions.addView(favorite, weightedButtonParams());

        Button record = recordingActive ? cloneRedButton("■ DETENER REC") : cloneGreenButton("● GRABAR");
        record.setOnClickListener(v -> {
            if (recordingActive) {
                stopRecording(true);
                record.setText("● GRABAR");
                record.setBackgroundResource(R.drawable.clone_green_button);
            } else {
                startLiveRecording(currentName, liveUrl(currentId, "ts"));
                record.setText("■ DETENER REC");
                record.setBackgroundResource(R.drawable.clone_red_button);
            }
        });
        actions.addView(record, weightedButtonParams());

        center.addView(actions);

        LinearLayout epg = new LinearLayout(this);
        epg.setOrientation(LinearLayout.VERTICAL);
        epg.setBackgroundResource(R.drawable.clone_panel_bg);
        epg.setPadding(dp(12), dp(10), dp(12), dp(10));
        main.addView(epg, new LinearLayout.LayoutParams(
                dp(isTvLayout() ? 390 : 320), ViewGroup.LayoutParams.MATCH_PARENT));

        TextView epgTitle = label("EPG / AHORA");
        epgTitle.setTypeface(Typeface.DEFAULT_BOLD);
        epgTitle.setTextSize(18);
        epg.addView(epgTitle);
        epg.addView(cardText("Cargando programación…"));

        startLivePreview(currentId, preview, previewState);
        loadStudioEpg(currentId, epg);
    }

    private void startLivePreview(String streamId, PlayerView preview, TextView state) {
        releaseLivePreview();
        try {
            DefaultHttpDataSource.Factory httpFactory = new DefaultHttpDataSource.Factory()
                    .setUserAgent("PIMFLEXTV/4.0.2 (Android)")
                    .setAllowCrossProtocolRedirects(true)
                    .setConnectTimeoutMs(15000)
                    .setReadTimeoutMs(30000);
            DefaultMediaSourceFactory sourceFactory = new DefaultMediaSourceFactory(this)
                    .setDataSourceFactory(httpFactory);
            livePreviewPlayer = new ExoPlayer.Builder(this)
                    .setMediaSourceFactory(sourceFactory)
                    .build();
            preview.setPlayer(livePreviewPlayer);

            String hls = liveUrl(streamId, "m3u8");
            String ts = liveUrl(streamId, "ts");
            final boolean[] fallbackUsed = {false};
            livePreviewPlayer.addListener(new Player.Listener() {
                @Override
                public void onPlaybackStateChanged(int playbackState) {
                    if (playbackState == Player.STATE_READY) state.setText("");
                }

                @Override
                public void onPlayerError(PlaybackException error) {
                    if (!fallbackUsed[0] && livePreviewPlayer != null) {
                        fallbackUsed[0] = true;
                        state.setText("Probando MPEGTS…");
                        livePreviewPlayer.setMediaItem(MediaItem.fromUri(Uri.parse(ts)));
                        livePreviewPlayer.prepare();
                        livePreviewPlayer.play();
                    } else {
                        state.setText("Vista previa no disponible · usa PANTALLA COMPLETA");
                    }
                }
            });
            livePreviewPlayer.setMediaItem(MediaItem.fromUri(Uri.parse(hls)));
            livePreviewPlayer.prepare();
            livePreviewPlayer.play();
        } catch (Exception e) {
            state.setText("Vista previa no disponible · usa PANTALLA COMPLETA");
        }
    }

    private void releaseLivePreview() {
        if (livePreviewPlayer != null) {
            try { livePreviewPlayer.stop(); } catch (Exception ignored) {}
            try { livePreviewPlayer.release(); } catch (Exception ignored) {}
            livePreviewPlayer = null;
        }
    }

    private void loadStudioEpg(String streamId, LinearLayout target) {
        io.execute(() -> {
            try {
                JSONObject data = new JSONObject(request("get_short_epg",
                        "stream_id=" + enc(streamId) + "&limit=8"));
                JSONArray rows = data.optJSONArray("epg_listings");
                ui.post(() -> renderStudioEpg(target, rows));
            } catch (Exception e) {
                ui.post(() -> renderStudioEpg(target, null));
            }
        });
    }

    private void renderStudioEpg(LinearLayout target, JSONArray rows) {
        target.removeAllViews();
        TextView title = label("EPG / PROGRAMACIÓN");
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextSize(18);
        target.addView(title);

        if (rows == null || rows.length() == 0) {
            target.addView(cardText("Sin información EPG para este canal."));
            return;
        }

        int limit = Math.min(8, rows.length());
        for (int i = 0; i < limit; i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row == null) continue;
            String program = decodeMaybeBase64(row.optString("title", "Programa"));
            long start = epgEpoch(row, "start_timestamp", "start");
            long stop = epgEpoch(row, "stop_timestamp", "end");
            String time = "";
            if (start > 0) {
                time = new SimpleDateFormat("h:mm a", Locale.getDefault()).format(new Date(start * 1000L));
                if (stop > start) {
                    time += " - " + new SimpleDateFormat("h:mm a", Locale.getDefault())
                            .format(new Date(stop * 1000L));
                }
            }
            TextView item = cardText((time.isEmpty() ? "" : time + "\n") + program);
            item.setTextSize(14);
            target.addView(item);
        }
    }

    private void loadRadioStreams() {
        showLoading("Cargando Radio…");
        io.execute(() -> {
            try {
                JSONArray all = new JSONArray(request("get_live_streams", null));
                JSONArray radio = new JSONArray();
                for (int i = 0; i < all.length(); i++) {
                    JSONObject row = all.optJSONObject(i);
                    if (row == null) continue;
                    String type = row.optString("stream_type", "").toLowerCase(Locale.ROOT);
                    String name = row.optString("name", "").toLowerCase(Locale.ROOT);
                    if (type.contains("radio") || name.contains(" radio") || name.contains("fm ") ||
                            name.startsWith("fm") || name.contains("music") || name.contains("música")) {
                        radio.put(row);
                    }
                }
                ui.post(() -> showRadioStreams(radio));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Radio", e, this::showSettings));
            }
        });
    }

    private void showRadioStreams(JSONArray radio) {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("RADIO", this::showSettings);

        if (radio.length() == 0) {
            root.addView(cardText("El servidor no reportó streams identificados como Radio."));
            return;
        }

        EditText search = input("Buscar estación", false);
        root.addView(search);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);

        Runnable render = () -> {
            list.removeAllViews();
            String q = search.getText().toString().trim().toLowerCase(Locale.ROOT);
            for (int i = 0; i < radio.length(); i++) {
                JSONObject row = radio.optJSONObject(i);
                if (row == null) continue;
                String name = row.optString("name", "Radio");
                if (!q.isEmpty() && !name.toLowerCase(Locale.ROOT).contains(q)) continue;
                String id = String.valueOf(row.opt("stream_id"));
                Button b = listButton("♫  " + name);
                b.setOnClickListener(v -> playStream(name, liveUrl(id, "ts"), liveUrl(id, "m3u8"),
                        () -> showRadioStreams(radio)));
                list.addView(b);
            }
        };
        render.run();

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render.run(); }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void showRecordingCenter() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("GRABACIONES", this::showSettings);

        if (recordingActive) {
            root.addView(cardText("Grabando ahora:\n" +
                    (activeRecordingFile == null ? "Stream en directo" : activeRecordingFile.getName())));
            Button stop = cloneRedButton("■ DETENER GRABACIÓN");
            stop.setOnClickListener(v -> {
                stopRecording(true);
                showRecordingCenter();
            });
            root.addView(stop);
        } else {
            root.addView(cardText("Puedes iniciar una grabación desde TV EN DIRECTO. "
                    + "La grabación se guarda en el almacenamiento privado de PIMFLEX TV."));
        }

        Button library = cloneGrayButton("ABRIR BIBLIOTECA DE GRABACIONES");
        library.setOnClickListener(v -> showRecordingsLibrary());
        root.addView(library);

        Button select = cloneGreenButton("SELECCIONAR CANAL PARA GRABAR");
        select.setOnClickListener(v -> loadChannelsForRecording());
        root.addView(select);
    }

    private void loadChannelsForRecording() {
        showLoading("Cargando canales…");
        io.execute(() -> {
            try {
                JSONArray channels = new JSONArray(request("get_live_streams", null));
                ui.post(() -> showChannelsForRecording(channels));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Grabaciones", e, this::showRecordingCenter));
            }
        });
    }

    private void showChannelsForRecording(JSONArray channels) {
        systemBack = this::showRecordingCenter;
        root = cloneScreen();
        addCloneHeader("SELECCIONA CANAL", this::showRecordingCenter);

        int limit = Math.min(channels.length(), 300);
        for (int i = 0; i < limit; i++) {
            JSONObject row = channels.optJSONObject(i);
            if (row == null) continue;
            String name = row.optString("name", "Canal");
            String id = String.valueOf(row.opt("stream_id"));
            Button b = listButton(name);
            b.setOnClickListener(v -> {
                startLiveRecording(name, liveUrl(id, "ts"));
                showRecordingCenter();
            });
            root.addView(b);
        }
    }

    private void startLiveRecording(String title, String url) {
        if (recordingActive) {
            Toast.makeText(this, "Ya hay una grabación activa.", Toast.LENGTH_LONG).show();
            return;
        }

        File movies = getExternalFilesDir(Environment.DIRECTORY_MOVIES);
        if (movies == null) {
            Toast.makeText(this, "No se pudo acceder al almacenamiento.", Toast.LENGTH_LONG).show();
            return;
        }

        File dir = new File(movies, "Recordings");
        if (!dir.exists() && !dir.mkdirs()) {
            Toast.makeText(this, "No se pudo crear la carpeta de grabaciones.", Toast.LENGTH_LONG).show();
            return;
        }

        String safe = (title == null ? "Canal" : title).replaceAll("[^A-Za-z0-9._ -]", "_").trim();
        if (safe.isEmpty()) safe = "Canal";
        String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        activeRecordingFile = new File(dir, safe + "_" + stamp + ".ts");
        recordingActive = true;
        Toast.makeText(this, "Grabación iniciada.", Toast.LENGTH_SHORT).show();

        recorderIo.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                recordingConnection = conn;
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(0);
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/4.0.2 (Android)");
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);

                try (BufferedInputStream in = new BufferedInputStream(conn.getInputStream());
                     FileOutputStream out = new FileOutputStream(activeRecordingFile)) {
                    byte[] buffer = new byte[64 * 1024];
                    while (recordingActive) {
                        int read = in.read(buffer);
                        if (read < 0) break;
                        out.write(buffer, 0, read);
                    }
                    out.flush();
                }
            } catch (Exception e) {
                if (recordingActive) {
                    ui.post(() -> Toast.makeText(this,
                            "La grabación se detuvo: " + cleanError(e), Toast.LENGTH_LONG).show());
                }
            } finally {
                recordingActive = false;
                recordingConnection = null;
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void stopRecording(boolean notify) {
        recordingActive = false;
        HttpURLConnection conn = recordingConnection;
        recordingConnection = null;
        if (conn != null) {
            try { conn.disconnect(); } catch (Exception ignored) {}
        }
        if (notify) Toast.makeText(this, "Grabación detenida.", Toast.LENGTH_SHORT).show();
    }

    private File recordingsDir() {
        File movies = getExternalFilesDir(Environment.DIRECTORY_MOVIES);
        return movies == null ? null : new File(movies, "Recordings");
    }

    private void showRecordingsLibrary() {
        systemBack = this::showRecordingCenter;
        root = cloneScreen();
        addCloneHeader("BIBLIOTECA DE GRABACIONES", this::showRecordingCenter);

        File dir = recordingsDir();
        File[] files = dir == null ? null : dir.listFiles();
        if (files == null || files.length == 0) {
            root.addView(cardText("Todavía no hay grabaciones guardadas."));
            return;
        }

        java.util.Arrays.sort(files, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
        for (File file : files) {
            if (!file.isFile()) continue;
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);

            Button play = cloneGrayButton(file.getName() + "  ·  " +
                    String.format(Locale.US, "%.1f MB", file.length() / 1048576.0));
            play.setOnClickListener(v -> playLocalMedia(file, this::showRecordingsLibrary));
            row.addView(play, new LinearLayout.LayoutParams(0, dp(58), 1f));

            Button del = cloneRedButton("BORRAR");
            del.setOnClickListener(v -> {
                if (file.delete()) showRecordingsLibrary();
                else Toast.makeText(this, "No se pudo borrar el archivo.", Toast.LENGTH_SHORT).show();
            });
            row.addView(del, new LinearLayout.LayoutParams(dp(120), dp(58)));
            root.addView(row);
        }
    }

    private void showDownloadsLibrary() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("DESCARGAS", this::showSettings);

        File dir = getExternalFilesDir(Environment.DIRECTORY_MOVIES);
        File[] files = dir == null ? null : dir.listFiles();
        int shown = 0;
        if (files != null) {
            java.util.Arrays.sort(files, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
            for (File file : files) {
                if (!file.isFile()) continue;
                shown++;
                LinearLayout row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);

                Button play = cloneGrayButton(file.getName() + "  ·  " +
                        String.format(Locale.US, "%.1f MB", file.length() / 1048576.0));
                play.setOnClickListener(v -> playLocalMedia(file, this::showDownloadsLibrary));
                row.addView(play, new LinearLayout.LayoutParams(0, dp(58), 1f));

                Button del = cloneRedButton("BORRAR");
                del.setOnClickListener(v -> {
                    if (file.delete()) showDownloadsLibrary();
                    else Toast.makeText(this, "No se pudo borrar.", Toast.LENGTH_SHORT).show();
                });
                row.addView(del, new LinearLayout.LayoutParams(dp(120), dp(58)));
                root.addView(row);
            }
        }
        if (shown == 0) root.addView(cardText("No hay películas descargadas."));
    }

    private void playLocalMedia(File file, Runnable back) {
        releaseLivePreview();
        releasePlayer();
        systemBack = back;

        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.BLACK);
        setContentView(screen);

        Button backBtn = cloneGrayButton("← VOLVER");
        backBtn.setOnClickListener(v -> {
            releasePlayer();
            back.run();
        });
        screen.addView(backBtn, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        PlayerView view = new PlayerView(this);
        view.setUseController(true);
        view.setKeepScreenOn(true);
        screen.addView(view, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        try {
            player = new ExoPlayer.Builder(this).build();
            view.setPlayer(player);
            player.setMediaItem(MediaItem.fromUri(Uri.fromFile(file)));
            player.prepare();
            player.play();
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo reproducir el archivo.", Toast.LENGTH_LONG).show();
        }
    }

'''
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2.4 live studio, radio, recording and libraries patch applied')
