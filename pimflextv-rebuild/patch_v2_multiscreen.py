from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import java.util.HashSet;\n', 'import java.util.HashSet;\nimport java.util.LinkedHashSet;\n')

field = '    private String lastGlobalQuery = "";\n'
extra = '''    private final List<ExoPlayer> multiPlayers = new ArrayList<>();
'''
if field not in s:
    raise SystemExit('global search field marker not found')
s = s.replace(field, field + extra, 1)

tile = '        addDashboardTile(menu, "🔎  BUSCAR", this::loadGlobalSearch, cols);\n'
if tile not in s:
    raise SystemExit('search tile marker not found')
s = s.replace(tile, '''        addDashboardTile(menu, "🔎  BUSCAR", this::loadGlobalSearch, cols);
        addDashboardTile(menu, "▦  MULTI-SCREEN", this::loadMultiScreenChannels, cols);
''', 1)

base = '''    private LinearLayout baseScreen() {
        releasePlayer();
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);
'''
if base not in s:
    raise SystemExit('baseScreen release marker not found')
s = s.replace(base, '''    private LinearLayout baseScreen() {
        releaseMultiPlayers();
        releasePlayer();
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);
''', 1)

marker = '    private void loadGlobalSearch() {\n'
methods = r'''    private void loadMultiScreenChannels() {
        showLoading("Cargando canales para Multi-Screen…");
        io.execute(() -> {
            try {
                JSONArray channels = new JSONArray(request("get_live_streams", null));
                ui.post(() -> showMultiScreenPicker(channels));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("No se pudo abrir Multi-Screen", e, this::showDashboard));
            }
        });
    }

    private void showMultiScreenPicker(JSONArray channels) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("▦ MULTI-SCREEN", 27);
        addSubtitle("Selecciona entre 2 y 4 canales");

        LinkedHashSet<String> selected = new LinkedHashSet<>();
        TextView counter = cardText("Seleccionados: 0 / 4");
        root.addView(counter);

        Button start = actionButton("ABRIR MULTI-SCREEN");
        start.setEnabled(false);
        root.addView(start);

        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list);

        int limit = Math.min(channels.length(), 180);
        for (int i = 0; i < limit; i++) {
            JSONObject item = channels.optJSONObject(i);
            if (item == null) continue;
            String id = String.valueOf(item.opt("stream_id"));
            String name = item.optString("name", "Canal");
            Button b = listButton("□  " + name);
            b.setOnClickListener(v -> {
                if (selected.contains(id)) {
                    selected.remove(id);
                    b.setText("□  " + name);
                } else {
                    if (selected.size() >= 4) {
                        Toast.makeText(this, "Máximo 4 canales.", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    selected.add(id);
                    b.setText("☑  " + name);
                }
                counter.setText("Seleccionados: " + selected.size() + " / 4");
                start.setEnabled(selected.size() >= 2);
            });
            list.addView(b);
        }

        start.setOnClickListener(v -> {
            JSONArray chosen = new JSONArray();
            for (int i = 0; i < channels.length(); i++) {
                JSONObject item = channels.optJSONObject(i);
                if (item == null) continue;
                String id = String.valueOf(item.opt("stream_id"));
                if (selected.contains(id)) chosen.put(item);
            }
            if (chosen.length() >= 2) showMultiScreen(chosen, channels);
        });
    }

    private void showMultiScreen(JSONArray chosen, JSONArray parentChannels) {
        releaseMultiPlayers();
        releasePlayer();
        systemBack = () -> {
            releaseMultiPlayers();
            showMultiScreenPicker(parentChannels);
        };

        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.BLACK);
        screen.setPadding(dp(5), dp(5), dp(5), dp(5));
        setContentView(screen);

        Button back = secondaryButton("← VOLVER");
        back.setOnClickListener(v -> systemBack.run());
        screen.addView(back, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(50)));

        TextView hint = label("Toca una ventana para escuchar ese canal");
        hint.setTextColor(Color.LTGRAY);
        hint.setGravity(Gravity.CENTER);
        hint.setPadding(0, dp(4), 0, dp(6));
        screen.addView(hint);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(2);
        grid.setRowCount(2);
        screen.addView(grid, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        int count = Math.min(4, chosen.length());
        for (int i = 0; i < count; i++) {
            JSONObject item = chosen.optJSONObject(i);
            if (item == null) continue;
            String id = String.valueOf(item.opt("stream_id"));
            String name = item.optString("name", "Canal");

            LinearLayout cell = new LinearLayout(this);
            cell.setOrientation(LinearLayout.VERTICAL);
            cell.setBackgroundColor(Color.rgb(8, 8, 8));
            cell.setPadding(dp(2), dp(2), dp(2), dp(2));

            GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
            gp.width = 0;
            gp.height = 0;
            gp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
            gp.rowSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
            gp.setMargins(dp(2), dp(2), dp(2), dp(2));
            cell.setLayoutParams(gp);

            TextView title = label(name);
            title.setTextSize(12);
            title.setMaxLines(1);
            title.setEllipsize(TextUtils.TruncateAt.END);
            title.setGravity(Gravity.CENTER);
            cell.addView(title, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(32)));

            PlayerView pv = new PlayerView(this);
            pv.setUseController(false);
            pv.setKeepScreenOn(true);
            cell.addView(pv, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

            DefaultHttpDataSource.Factory httpFactory = new DefaultHttpDataSource.Factory()
                    .setUserAgent("PIMFLEXTV/4.0.2 (Android)")
                    .setAllowCrossProtocolRedirects(true)
                    .setConnectTimeoutMs(15000)
                    .setReadTimeoutMs(30000);
            DefaultMediaSourceFactory sourceFactory = new DefaultMediaSourceFactory(this)
                    .setDataSourceFactory(httpFactory);
            ExoPlayer p = new ExoPlayer.Builder(this)
                    .setMediaSourceFactory(sourceFactory)
                    .build();
            p.setVolume(i == 0 ? 1f : 0f);
            pv.setPlayer(p);
            p.setMediaItem(MediaItem.fromUri(Uri.parse(liveUrl(id, "m3u8"))));
            p.prepare();
            p.play();
            multiPlayers.add(p);

            pv.setOnClickListener(v -> selectMultiAudio(p));
            grid.addView(cell);
        }
    }

    private void selectMultiAudio(ExoPlayer selected) {
        for (ExoPlayer p : multiPlayers) {
            try { p.setVolume(p == selected ? 1f : 0f); } catch (Exception ignored) {}
        }
    }

    private void releaseMultiPlayers() {
        for (ExoPlayer p : new ArrayList<>(multiPlayers)) {
            try { p.stop(); } catch (Exception ignored) {}
            try { p.release(); } catch (Exception ignored) {}
        }
        multiPlayers.clear();
    }

'''
if marker not in s:
    raise SystemExit('global search method marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2 multi-screen patch applied')
