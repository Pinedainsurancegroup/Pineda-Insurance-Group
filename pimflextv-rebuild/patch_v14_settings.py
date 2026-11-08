from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import java.text.DateFormat;\n', 'import java.text.DateFormat;\nimport java.text.SimpleDateFormat;\n')

needle = '        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);\n'
repl = '''        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);
        addDashboardTile(menu, "⏪  CATCH-UP", this::loadCatchupChannels, cols);
        addDashboardTile(menu, "⚙  AJUSTES", this::showSettings, cols);
'''
if needle not in s:
    raise SystemExit('dashboard marker not found')
s = s.replace(needle, repl, 1)

needle = '''    private LinearLayout baseScreen() {
        releasePlayer();
'''
repl = '''    private LinearLayout baseScreen() {
        releasePlayer();
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);
'''
if needle not in s:
    raise SystemExit('baseScreen marker not found')
s = s.replace(needle, repl, 1)

marker = '    private void showParentalSettings() {\n'
methods = r'''    private void showSettings() {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("⚙ AJUSTES", 27);

        String mode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        int cache = prefs == null ? 2500 : prefs.getInt("network_cache_ms", 2500);
        boolean immersive = prefs != null && prefs.getBoolean("immersive_player", true);

        root.addView(cardText("Reproductor: " + playerModeLabel(mode)
                + "\nCaché de red: " + cache + " ms"
                + "\nModo inmersivo: " + (immersive ? "Sí" : "No")));

        Button auto = actionButton(("auto".equals(mode) ? "✓  " : "") + "AUTOMÁTICO · EXO + VLC");
        auto.setOnClickListener(v -> setPlayerMode("auto"));
        root.addView(auto);

        Button exo = secondaryButton(("exo".equals(mode) ? "✓  " : "") + "FORZAR EXOPLAYER");
        exo.setOnClickListener(v -> setPlayerMode("exo"));
        root.addView(exo);

        Button vlc = secondaryButton(("vlc".equals(mode) ? "✓  " : "") + "FORZAR VLC");
        vlc.setOnClickListener(v -> setPlayerMode("vlc"));
        root.addView(vlc);

        Button low = secondaryButton((cache == 1500 ? "✓  " : "") + "CACHÉ RÁPIDO · 1500 ms");
        low.setOnClickListener(v -> setNetworkCache(1500));
        root.addView(low);

        Button normal = secondaryButton((cache == 2500 ? "✓  " : "") + "CACHÉ NORMAL · 2500 ms");
        normal.setOnClickListener(v -> setNetworkCache(2500));
        root.addView(normal);

        Button stable = secondaryButton((cache == 5000 ? "✓  " : "") + "CACHÉ ESTABLE · 5000 ms");
        stable.setOnClickListener(v -> setNetworkCache(5000));
        root.addView(stable);

        CheckBox immersiveBox = new CheckBox(this);
        immersiveBox.setText("Pantalla completa inmersiva al reproducir");
        immersiveBox.setTextColor(Color.WHITE);
        immersiveBox.setChecked(immersive);
        immersiveBox.setPadding(dp(4), dp(12), dp(4), dp(12));
        immersiveBox.setOnCheckedChangeListener((buttonView, checked) -> {
            if (prefs != null) prefs.edit().putBoolean("immersive_player", checked).apply();
        });
        root.addView(immersiveBox);
    }

    private String playerModeLabel(String mode) {
        if ("exo".equals(mode)) return "ExoPlayer";
        if ("vlc".equals(mode)) return "VLC";
        return "Automático";
    }

    private void setPlayerMode(String mode) {
        if (prefs != null) prefs.edit().putString("player_mode", mode).apply();
        showSettings();
    }

    private void setNetworkCache(int value) {
        if (prefs != null) prefs.edit().putInt("network_cache_ms", value).apply();
        showSettings();
    }

    private void loadCatchupChannels() {
        showLoading("Buscando canales con Catch-Up…");
        io.execute(() -> {
            try {
                JSONArray source = new JSONArray(request("get_live_streams", null));
                JSONArray archive = new JSONArray();
                for (int i = 0; i < source.length(); i++) {
                    JSONObject row = source.optJSONObject(i);
                    if (row == null) continue;
                    String enabled = String.valueOf(row.opt("tv_archive"));
                    if ("1".equals(enabled) || row.optBoolean("tv_archive", false)) archive.put(row);
                }
                ui.post(() -> showCatchupChannels(archive));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo cargar Catch-Up", e, this::showDashboard));
            }
        });
    }

    private void showCatchupChannels(JSONArray channels) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("⏪ CATCH-UP", 27);
        addSubtitle("Canales con archivo disponible: " + channels.length());

        if (channels.length() == 0) {
            root.addView(cardText("El servidor no marcó canales con TV Archive / Catch-Up."));
            return;
        }

        int limit = Math.min(channels.length(), 500);
        for (int i = 0; i < limit; i++) {
            JSONObject row = channels.optJSONObject(i);
            if (row == null) continue;
            String id = String.valueOf(row.opt("stream_id"));
            String name = row.optString("name", "Canal");
            Button b = listButton(name);
            b.setOnClickListener(v -> runWithParentalGate(name, () -> loadCatchupPrograms(id, name, channels)));
            root.addView(b);
        }
    }

    private void loadCatchupPrograms(String streamId, String channelName, JSONArray parent) {
        showLoading("Cargando archivo de " + channelName + "…");
        io.execute(() -> {
            try {
                JSONObject obj = new JSONObject(request("get_simple_data_table", "stream_id=" + enc(streamId)));
                ui.post(() -> showCatchupPrograms(streamId, channelName, obj, parent));
            } catch (Exception first) {
                try {
                    JSONObject obj = new JSONObject(request("get_short_epg", "stream_id=" + enc(streamId) + "&limit=100"));
                    ui.post(() -> showCatchupPrograms(streamId, channelName, obj, parent));
                } catch (Exception second) {
                    ui.post(() -> showErrorScreen("No se pudo cargar el archivo", second,
                            () -> showCatchupChannels(parent)));
                }
            }
        });
    }

    private void showCatchupPrograms(String streamId, String channelName, JSONObject obj, JSONArray parent) {
        Runnable back = () -> showCatchupChannels(parent);
        systemBack = back;
        root = baseScreen();
        addBack(back);
        addTitle(channelName, 25);
        addSubtitle("Programas anteriores disponibles");

        JSONArray listings = obj.optJSONArray("epg_listings");
        if (listings == null) listings = obj.optJSONArray("listings");
        if (listings == null || listings.length() == 0) {
            root.addView(cardText("Este canal no devolvió programas archivados."));
            return;
        }

        long nowSec = System.currentTimeMillis() / 1000L;
        int shown = 0;
        for (int i = listings.length() - 1; i >= 0 && shown < 100; i--) {
            JSONObject row = listings.optJSONObject(i);
            if (row == null) continue;
            long start = epgEpoch(row, "start_timestamp", "start");
            long stop = epgEpoch(row, "stop_timestamp", "end");
            if (start <= 0 || stop <= start || start >= nowSec) continue;

            String archiveFlag = String.valueOf(row.opt("has_archive"));
            if ("0".equals(archiveFlag) && obj.has("epg_listings")) continue;

            String title = decodeMaybeBase64(row.optString("title", "Programa"));
            String desc = decodeMaybeBase64(row.optString("description", ""));
            int durationMin = (int) Math.max(1L, (stop - start + 59L) / 60L);

            Button b = listButton(title + "\n" + catchupTimeLabel(start, stop));
            long startFinal = start;
            b.setOnClickListener(v -> playCatchup(streamId, title, startFinal, durationMin,
                    () -> showCatchupPrograms(streamId, channelName, obj, parent)));
            root.addView(b);

            if (!desc.isEmpty()) {
                TextView d = label(desc);
                d.setTextSize(12);
                d.setTextColor(Color.rgb(170, 176, 196));
                d.setMaxLines(2);
                d.setEllipsize(TextUtils.TruncateAt.END);
                d.setPadding(dp(10), 0, dp(10), dp(4));
                root.addView(d);
            }
            shown++;
        }

        if (shown == 0) {
            root.addView(cardText("No encontré emisiones pasadas reproducibles en la guía de este canal."));
        }
    }

    private long epgEpoch(JSONObject row, String epochKey, String dateKey) {
        long direct = row.optLong(epochKey, 0L);
        if (direct > 0) return direct;
        String value = row.optString(dateKey, "");
        if (value.isEmpty()) return 0L;
        String[] patterns = {"yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd'T'HH:mm:ss"};
        for (String pattern : patterns) {
            try {
                SimpleDateFormat f = new SimpleDateFormat(pattern, Locale.US);
                Date date = f.parse(value);
                if (date != null) return date.getTime() / 1000L;
            } catch (Exception ignored) {}
        }
        return 0L;
    }

    private String catchupTimeLabel(long start, long stop) {
        DateFormat date = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT, Locale.getDefault());
        DateFormat time = DateFormat.getTimeInstance(DateFormat.SHORT, Locale.getDefault());
        return date.format(new Date(start * 1000L)) + " → " + time.format(new Date(stop * 1000L));
    }

    private void playCatchup(String streamId, String title, long startSec, int durationMin, Runnable back) {
        SimpleDateFormat pathFormat = new SimpleDateFormat("yyyy-MM-dd:HH-mm", Locale.US);
        String start = pathFormat.format(new Date(startSec * 1000L));

        String pathUrl = server + "/timeshift/" + encPath(username) + "/" + encPath(password)
                + "/" + durationMin + "/" + Uri.encode(start) + "/" + streamId + ".ts";

        String queryUrl = server + "/streaming/timeshift.php?username=" + enc(username)
                + "&password=" + enc(password)
                + "&stream=" + enc(streamId)
                + "&start=" + enc(start)
                + "&duration=" + durationMin;

        playStream(title, queryUrl, pathUrl, back);
    }

'''
if marker not in s:
    raise SystemExit('settings insertion marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v1.4 settings/catchup patch applied')
