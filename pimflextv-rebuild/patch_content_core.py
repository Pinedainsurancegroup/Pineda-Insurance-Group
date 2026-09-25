from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import java.util.Locale;\n', 'import java.util.Locale;\n')

field_marker = '    private final LruCache<String, Bitmap> artCache = new LruCache<>(48);\n'
fields = '''    private String currentWatchType = "";
    private String currentWatchId = "";
    private String currentWatchTitle = "";
    private String currentWatchExt = "";
    private String currentWatchArt = "";
    private long pendingResumeMs = 0L;
    private int resumeAttempts = 0;
    private Runnable progressRunnable;
'''
if field_marker not in s:
    raise SystemExit('artCache field marker not found')
s = s.replace(field_marker, field_marker + fields, 1)

dash = '        addDashboardTile(menu, "★  FAVORITOS", this::loadFavorites, cols);\n'
if dash not in s:
    raise SystemExit('dashboard marker not found')
s = s.replace(dash, '''        addDashboardTile(menu, "★  FAVORITOS", this::loadFavorites, cols);
        addDashboardTile(menu, "⏯  CONTINUAR", () -> showWatchHistory(true), cols);
        addDashboardTile(menu, "🕘  RECIENTES", () -> showWatchHistory(false), cols);
''', 1)

vod_poster = '''                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                card.setOnClickListener(v -> playStream(name, url, null,
                        () -> showItems(type, categoryId, categoryName, arr)));
'''
if vod_poster not in s:
    raise SystemExit('VOD poster marker not found')
s = s.replace(vod_poster, '''                String ext = safeExt(item.optString("container_extension", "mp4"));
                String artFinal = art;
                card.setOnClickListener(v -> loadVodDetails(id, name, ext, artFinal,
                        () -> showItems(type, categoryId, categoryName, arr)));
''', 1)

series_ep = '''                b.setOnClickListener(v -> playStream(title, url, null,
                        () -> showSeriesEpisodes(seriesName, info, categoryId, categoryName, parentList)));
'''
if series_ep not in s:
    raise SystemExit('series episode marker not found')
s = s.replace(series_ep, '''                b.setOnClickListener(v ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showSeriesEpisodes(seriesName, info, categoryId, categoryName, parentList)));
''', 1)

fav_ep = '''                b.setOnClickListener(v -> playStream(title, url, null,
                        () -> showFavoriteSeriesEpisodes(seriesName, info, favorites)));
'''
if fav_ep not in s:
    raise SystemExit('favorite episode marker not found')
s = s.replace(fav_ep, '''                b.setOnClickListener(v ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showFavoriteSeriesEpisodes(seriesName, info, favorites)));
''', 1)

fav_vod = '''                String ext = safeExt(item.optString("container_extension", "mp4"));
                String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                b.setOnClickListener(v -> playStream(name, url, null, () -> showFavorites(arr)));
'''
if fav_vod not in s:
    raise SystemExit('favorite VOD marker not found')
s = s.replace(fav_vod, '''                String ext = safeExt(item.optString("container_extension", "mp4"));
                String art = item.optString("stream_icon", item.optString("cover_big", item.optString("cover", "")));
                b.setOnClickListener(v -> loadVodDetails(id, name, ext, art, () -> showFavorites(arr)));
''', 1)

s = s.replace('        addSubtitle("Episodios");\n', '        addSubtitle("Episodios");\n        addSeriesInfoHeader(info);\n')

marker = '    private void loadEpgChannels() {\n'
methods = r'''    private void loadVodDetails(String id, String fallbackTitle, String ext, String fallbackArt, Runnable back) {
        showLoading("Cargando información…");
        io.execute(() -> {
            try {
                JSONObject obj = new JSONObject(request("get_vod_info", "vod_id=" + enc(id)));
                ui.post(() -> showVodDetails(id, fallbackTitle, ext, fallbackArt, obj, back));
            } catch (Exception e) {
                ui.post(() -> showVodDetails(id, fallbackTitle, ext, fallbackArt, new JSONObject(), back));
            }
        });
    }

    private void showVodDetails(String id, String fallbackTitle, String ext, String fallbackArt,
                                JSONObject payload, Runnable back) {
        systemBack = back;
        root = baseScreen();
        addBack(back);

        JSONObject movieData = payload.optJSONObject("movie_data");
        JSONObject info = payload.optJSONObject("info");
        String title = movieData == null ? fallbackTitle : movieData.optString("name", fallbackTitle);
        addTitle(title, 26);

        String art = fallbackArt == null ? "" : fallbackArt;
        if (movieData != null) art = movieData.optString("stream_icon", movieData.optString("cover_big", art));
        if (info != null) art = info.optString("movie_image", info.optString("cover_big", art));

        ImageView poster = new ImageView(this);
        poster.setImageResource(R.drawable.poster_placeholder);
        poster.setScaleType(ImageView.ScaleType.CENTER_CROP);
        LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(isTvLayout() ? 390 : 300));
        pp.setMargins(0, 0, 0, dp(10));
        poster.setLayoutParams(pp);
        root.addView(poster);
        loadArtwork(art, poster);

        String plot = info == null ? "" : info.optString("plot", "");
        String genre = info == null ? "" : info.optString("genre", "");
        String release = info == null ? "" : info.optString("releasedate", info.optString("releaseDate", ""));
        String rating = info == null ? "" : info.optString("rating", "");
        String duration = info == null ? "" : info.optString("duration", "");
        String cast = info == null ? "" : info.optString("cast", "");
        String director = info == null ? "" : info.optString("director", "");

        StringBuilder meta = new StringBuilder();
        if (!genre.isEmpty()) meta.append("Género: ").append(genre).append("\n");
        if (!release.isEmpty()) meta.append("Estreno: ").append(release).append("\n");
        if (!rating.isEmpty()) meta.append("Rating: ").append(rating).append("\n");
        if (!duration.isEmpty()) meta.append("Duración: ").append(duration).append("\n");
        if (!director.isEmpty()) meta.append("Director: ").append(director).append("\n");
        if (!cast.isEmpty()) meta.append("Reparto: ").append(cast).append("\n");
        if (!plot.isEmpty()) meta.append("\n").append(plot);
        if (meta.length() > 0) root.addView(cardText(meta.toString().trim()));

        long saved = getSavedPosition("vod", id);
        String url = server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
        String finalTitle = title;
        String finalArt = art;

        Button play = actionButton(saved > 60000 ? "▶  CONTINUAR · " + humanTime(saved) : "▶  REPRODUCIR");
        play.setOnClickListener(v -> startTrackedPlayback("vod", id, finalTitle, ext, finalArt, url,
                () -> showVodDetails(id, fallbackTitle, ext, fallbackArt, payload, back)));
        root.addView(play);

        if (saved > 0) {
            Button restart = secondaryButton("↺  VER DESDE EL INICIO");
            restart.setOnClickListener(v -> {
                clearSavedPosition("vod", id);
                startTrackedPlayback("vod", id, finalTitle, ext, finalArt, url,
                        () -> showVodDetails(id, fallbackTitle, ext, fallbackArt, payload, back));
            });
            root.addView(restart);
        }

        Button favorite = secondaryButton(isFavorite("vod", id) ? "★  QUITAR DE FAVORITOS" : "☆  AGREGAR A FAVORITOS");
        favorite.setOnClickListener(v -> {
            toggleFavorite("vod", id);
            favorite.setText(isFavorite("vod", id) ? "★  QUITAR DE FAVORITOS" : "☆  AGREGAR A FAVORITOS");
        });
        root.addView(favorite);
    }

    private void addSeriesInfoHeader(JSONObject payload) {
        JSONObject info = payload == null ? null : payload.optJSONObject("info");
        if (info == null) return;
        String cover = info.optString("cover", info.optString("cover_big", ""));
        String plot = info.optString("plot", "");
        String genre = info.optString("genre", "");
        String rating = info.optString("rating", "");
        String release = info.optString("releaseDate", info.optString("releasedate", ""));

        if (!cover.isEmpty()) {
            ImageView poster = new ImageView(this);
            poster.setImageResource(R.drawable.poster_placeholder);
            poster.setScaleType(ImageView.ScaleType.CENTER_CROP);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(isTvLayout() ? 340 : 250));
            p.setMargins(0, 0, 0, dp(8));
            poster.setLayoutParams(p);
            root.addView(poster);
            loadArtwork(cover, poster);
        }

        StringBuilder text = new StringBuilder();
        if (!genre.isEmpty()) text.append("Género: ").append(genre).append("\n");
        if (!release.isEmpty()) text.append("Estreno: ").append(release).append("\n");
        if (!rating.isEmpty()) text.append("Rating: ").append(rating).append("\n");
        if (!plot.isEmpty()) text.append("\n").append(plot);
        if (text.length() > 0) root.addView(cardText(text.toString().trim()));
    }

    private void startTrackedPlayback(String type, String id, String title, String ext, String art,
                                      String url, Runnable back) {
        currentWatchType = type == null ? "" : type;
        currentWatchId = id == null ? "" : id;
        currentWatchTitle = title == null ? "" : title;
        currentWatchExt = ext == null ? "" : ext;
        currentWatchArt = art == null ? "" : art;
        pendingResumeMs = getSavedPosition(currentWatchType, currentWatchId);
        resumeAttempts = 0;

        upsertWatchRecord(currentWatchType, currentWatchId, currentWatchTitle, currentWatchExt,
                currentWatchArt, pendingResumeMs, getSavedDuration(currentWatchType, currentWatchId));

        playStream(title, url, null, () -> {
            stopProgressTracking();
            currentWatchType = "";
            currentWatchId = "";
            back.run();
        });
        scheduleProgressTracking();
        ui.postDelayed(this::applyPendingResume, 450);
    }

    private void scheduleProgressTracking() {
        stopProgressTracking();
        progressRunnable = new Runnable() {
            @Override public void run() {
                saveProgressNow();
                if (!currentWatchId.isEmpty()) ui.postDelayed(this, 5000);
            }
        };
        ui.postDelayed(progressRunnable, 5000);
    }

    private void stopProgressTracking() {
        if (progressRunnable != null) {
            ui.removeCallbacks(progressRunnable);
            progressRunnable = null;
        }
    }

    private void saveProgressNow() {
        if (currentWatchId.isEmpty()) return;
        long pos = 0L;
        long dur = 0L;
        try {
            if (player != null) {
                pos = Math.max(0L, player.getCurrentPosition());
                dur = Math.max(0L, player.getDuration());
            } else if (vlcPlayer != null) {
                pos = Math.max(0L, vlcPlayer.getTime());
                dur = Math.max(0L, vlcPlayer.getLength());
            }
        } catch (Exception ignored) {}
        upsertWatchRecord(currentWatchType, currentWatchId, currentWatchTitle, currentWatchExt,
                currentWatchArt, pos, dur);
    }

    private void applyPendingResume() {
        if (pendingResumeMs <= 60000 || currentWatchId.isEmpty()) return;
        try {
            if (player != null && player.getPlaybackState() == Player.STATE_READY) {
                long position = pendingResumeMs;
                pendingResumeMs = 0L;
                player.seekTo(position);
                return;
            }
            if (vlcPlayer != null && vlcPlayer.isPlaying()) {
                long position = pendingResumeMs;
                pendingResumeMs = 0L;
                vlcPlayer.setTime(position);
                return;
            }
        } catch (Exception ignored) {}
        resumeAttempts++;
        if (resumeAttempts < 30 && pendingResumeMs > 0) ui.postDelayed(this::applyPendingResume, 500);
    }

    private JSONArray watchHistory() {
        if (prefs == null) return new JSONArray();
        try {
            return new JSONArray(prefs.getString("watch_history", "[]"));
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    private String watchKey(String type, String id) {
        return (type == null ? "" : type) + ":" + (id == null ? "" : id);
    }

    private void upsertWatchRecord(String type, String id, String title, String ext, String art,
                                   long position, long duration) {
        if (prefs == null || id == null || id.isEmpty()) return;
        JSONArray old = watchHistory();
        JSONArray out = new JSONArray();
        String key = watchKey(type, id);
        try {
            JSONObject fresh = new JSONObject();
            fresh.put("key", key);
            fresh.put("type", type);
            fresh.put("id", id);
            fresh.put("title", title == null ? "" : title);
            fresh.put("ext", ext == null ? "" : ext);
            fresh.put("art", art == null ? "" : art);
            fresh.put("position", Math.max(0L, position));
            fresh.put("duration", Math.max(0L, duration));
            fresh.put("updated", System.currentTimeMillis());
            out.put(fresh);

            int kept = 1;
            for (int i = 0; i < old.length() && kept < 40; i++) {
                JSONObject row = old.optJSONObject(i);
                if (row == null || key.equals(row.optString("key", ""))) continue;
                out.put(row);
                kept++;
            }
            prefs.edit().putString("watch_history", out.toString()).apply();
        } catch (Exception ignored) {}
    }

    private long getSavedPosition(String type, String id) {
        JSONArray rows = watchHistory();
        String key = watchKey(type, id);
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row != null && key.equals(row.optString("key", ""))) return row.optLong("position", 0L);
        }
        return 0L;
    }

    private long getSavedDuration(String type, String id) {
        JSONArray rows = watchHistory();
        String key = watchKey(type, id);
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row != null && key.equals(row.optString("key", ""))) return row.optLong("duration", 0L);
        }
        return 0L;
    }

    private void clearSavedPosition(String type, String id) {
        JSONArray rows = watchHistory();
        String key = watchKey(type, id);
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row != null && key.equals(row.optString("key", ""))) {
                try { row.put("position", 0L); } catch (Exception ignored) {}
                break;
            }
        }
        if (prefs != null) prefs.edit().putString("watch_history", rows.toString()).apply();
    }

    private void removeWatchRecord(String key) {
        JSONArray rows = watchHistory();
        JSONArray out = new JSONArray();
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row == null || key.equals(row.optString("key", ""))) continue;
            out.put(row);
        }
        if (prefs != null) prefs.edit().putString("watch_history", out.toString()).apply();
    }

    private void showWatchHistory(boolean onlyContinue) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle(onlyContinue ? "⏯ CONTINUAR VIENDO" : "🕘 RECIENTES", 27);

        JSONArray rows = watchHistory();
        int shown = 0;
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row == null) continue;
            String type = row.optString("type", "");
            if (!"vod".equals(type) && !"series_episode".equals(type)) continue;
            long pos = row.optLong("position", 0L);
            long dur = row.optLong("duration", 0L);
            boolean resumable = pos > 60000 && (dur <= 0 || pos < dur * 0.95);
            if (onlyContinue && !resumable) continue;

            String id = row.optString("id", "");
            String title = row.optString("title", "Contenido");
            String ext = safeExt(row.optString("ext", "mp4"));
            String art = row.optString("art", "");
            String key = row.optString("key", watchKey(type, id));

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.HORIZONTAL);
            card.setGravity(Gravity.CENTER_VERTICAL);
            card.setBackgroundColor(panel);
            card.setPadding(dp(8), dp(8), dp(8), dp(8));
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            cp.setMargins(0, dp(4), 0, dp(4));
            card.setLayoutParams(cp);

            ImageView image = new ImageView(this);
            image.setImageResource(R.drawable.poster_placeholder);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            card.addView(image, new LinearLayout.LayoutParams(dp(74), dp(100)));
            loadArtwork(art, image);

            LinearLayout textCol = new LinearLayout(this);
            textCol.setOrientation(LinearLayout.VERTICAL);
            textCol.setPadding(dp(10), 0, dp(6), 0);
            TextView t = label(title);
            t.setTypeface(Typeface.DEFAULT_BOLD);
            t.setTextSize(16);
            t.setMaxLines(2);
            textCol.addView(t);
            if (pos > 0) {
                String progress = dur > 0 ? humanTime(pos) + " / " + humanTime(dur) : humanTime(pos);
                TextView pr = label(progress);
                pr.setTextSize(13);
                pr.setTextColor(primary);
                pr.setPadding(0, dp(5), 0, 0);
                textCol.addView(pr);
            }
            card.addView(textCol, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            Button play = secondaryButton("▶");
            LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(dp(58), dp(54));
            bp.setMargins(dp(3), 0, dp(3), 0);
            play.setLayoutParams(bp);
            play.setOnClickListener(v -> {
                String url = "vod".equals(type)
                        ? server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext
                        : server + "/series/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                startTrackedPlayback(type, id, title, ext, art, url, () -> showWatchHistory(onlyContinue));
            });
            card.addView(play);

            Button remove = secondaryButton("×");
            LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(dp(58), dp(54));
            rp.setMargins(dp(3), 0, 0, 0);
            remove.setLayoutParams(rp);
            remove.setOnClickListener(v -> {
                removeWatchRecord(key);
                showWatchHistory(onlyContinue);
            });
            card.addView(remove);

            root.addView(card);
            shown++;
        }

        if (shown == 0) {
            root.addView(cardText(onlyContinue
                    ? "Todavía no hay contenido parcialmente visto para continuar."
                    : "Todavía no hay películas o episodios reproducidos."));
        }
    }

    private String humanTime(long ms) {
        long total = Math.max(0L, ms / 1000L);
        long h = total / 3600L;
        long m = (total % 3600L) / 60L;
        long sec = total % 60L;
        if (h > 0) return String.format(Locale.US, "%d:%02d:%02d", h, m, sec);
        return String.format(Locale.US, "%d:%02d", m, sec);
    }

'''
if marker not in s:
    raise SystemExit('EPG marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('Content details/history patch applied')
