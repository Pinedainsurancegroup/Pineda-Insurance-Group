from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Add the original-style tracks side panel button.
marker = '''        subtitleButton.setOnClickListener(v -> showSubtitleTrackDialog());
        trackTools.addView(subtitleButton);

        screen.addView(trackTools);
'''
repl = '''        subtitleButton.setOnClickListener(v -> showSubtitleTrackDialog());
        trackTools.addView(subtitleButton);

        Button tracksButton = secondaryButton("⚙ PISTAS");
        LinearLayout.LayoutParams tracksParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        tracksParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        tracksButton.setLayoutParams(tracksParams);
        tracksButton.setOnClickListener(v -> showTracksSidePanel());
        trackTools.addView(tracksButton);

        screen.addView(trackTools);
'''
if marker not in s:
    raise SystemExit('track toolbar marker not found')
s = s.replace(marker, repl, 1)

# Run real refresh checks when returning home.
dashboard_end = '''        expiry.setPadding(0, dp(16), 0, dp(2));
        root.addView(expiry);
    }

    private LinearLayout cloneScreen() {
'''
if dashboard_end not in s:
    raise SystemExit('dashboard end marker not found')
s = s.replace(dashboard_end, '''        expiry.setPadding(0, dp(16), 0, dp(2));
        root.addView(expiry);
        maybeRunAutomaticRefresh();
    }

    private LinearLayout cloneScreen() {
''', 1)

# Insert track panel and automation before audio dialog.
marker2 = '    private void showAudioTrackDialog() {\n'
if marker2 not in s:
    raise SystemExit('showAudioTrackDialog marker not found')
methods = r'''    private void showTracksSidePanel() {
        if (player == null && vlcPlayer == null) {
            Toast.makeText(this, "El reproductor todavía no cargó las pistas.", Toast.LENGTH_SHORT).show();
            return;
        }

        android.app.Dialog dialog = new android.app.Dialog(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundColor(Color.rgb(7, 7, 10));
        panel.setPadding(dp(22), dp(18), dp(22), dp(22));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        Button back = cloneGrayButton("←");
        back.setOnClickListener(v -> dialog.dismiss());
        header.addView(back, new LinearLayout.LayoutParams(dp(62), dp(50)));

        TextView title = label("Settings");
        title.setTextSize(24);
        title.setPadding(dp(12), 0, 0, 0);
        header.addView(title, new LinearLayout.LayoutParams(0, dp(50), 1f));
        panel.addView(header);

        View divider = new View(this);
        divider.setBackgroundColor(Color.DKGRAY);
        panel.addView(divider, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(1)));

        ScrollView scroll = new ScrollView(this);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(0, dp(12), 0, dp(12));
        scroll.addView(content);
        panel.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        if (player != null) populateExoTracksPanel(content, dialog);
        else populateVlcTracksPanel(content, dialog);

        dialog.setContentView(panel);
        android.view.Window window = dialog.getWindow();
        if (window != null) {
            window.setBackgroundDrawableResource(android.R.color.transparent);
            window.setGravity(Gravity.RIGHT);
            int width = Math.round(getResources().getDisplayMetrics().widthPixels * 0.47f);
            window.setLayout(Math.max(dp(380), width), ViewGroup.LayoutParams.MATCH_PARENT);
            window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            android.view.WindowManager.LayoutParams lp = window.getAttributes();
            lp.dimAmount = 0.45f;
            window.setAttributes(lp);
        }
        dialog.show();
        if (window != null) {
            int width = Math.round(getResources().getDisplayMetrics().widthPixels * 0.47f);
            window.setLayout(Math.max(dp(380), width), ViewGroup.LayoutParams.MATCH_PARENT);
            window.setGravity(Gravity.RIGHT);
        }
    }

    private void addTrackSectionTitle(LinearLayout parent, String icon, String title) {
        TextView heading = label(icon + "  " + title);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextSize(19);
        heading.setPadding(dp(4), dp(18), dp(4), dp(8));
        parent.addView(heading);
    }

    private void populateExoTracksPanel(LinearLayout content, android.app.Dialog dialog) {
        Tracks tracks = player.getCurrentTracks();

        addTrackSectionTitle(content, "▣", "PISTAS DE VIDEO");
        int videoCount = 0;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() != C.TRACK_TYPE_VIDEO) continue;
            for (int i = 0; i < group.length; i++) {
                if (!group.isTrackSupported(i, true)) continue;
                videoCount++;
                Format f = group.getTrackFormat(i);
                String codec = f.sampleMimeType == null ? "VIDEO" :
                        f.sampleMimeType.replace("video/", "").toUpperCase(Locale.ROOT);
                String details = codec;
                if (f.bitrate > 0) details += ", " + Math.round(f.bitrate / 1000f) + " kb/s";
                if (f.width > 0 && f.height > 0) details += ", " + f.width + " x " + f.height;
                Button b = cloneGrayButton((group.isTrackSelected(i) ? "◉  " : "○  ") + details);
                int index = i;
                b.setOnClickListener(v -> {
                    androidx.media3.common.TrackSelectionParameters.Builder builder =
                            player.getTrackSelectionParameters().buildUpon();
                    builder.setTrackTypeDisabled(C.TRACK_TYPE_VIDEO, false);
                    builder.clearOverridesOfType(C.TRACK_TYPE_VIDEO);
                    builder.addOverride(new TrackSelectionOverride(group.getMediaTrackGroup(), index));
                    player.setTrackSelectionParameters(builder.build());
                    dialog.dismiss();
                    ui.postDelayed(this::showTracksSidePanel, 250);
                });
                content.addView(b);
            }
        }
        if (videoCount == 0) content.addView(cardText("Video automático / sin pistas alternativas."));

        addTrackSectionTitle(content, "♫", "PISTAS DE AUDIO");
        Button autoAudio = cloneGrayButton("○  Automático");
        autoAudio.setOnClickListener(v -> {
            androidx.media3.common.TrackSelectionParameters.Builder builder =
                    player.getTrackSelectionParameters().buildUpon();
            builder.setTrackTypeDisabled(C.TRACK_TYPE_AUDIO, false);
            builder.clearOverridesOfType(C.TRACK_TYPE_AUDIO);
            builder.setPreferredAudioLanguage(null);
            player.setTrackSelectionParameters(builder.build());
            dialog.dismiss();
            ui.postDelayed(this::showTracksSidePanel, 250);
        });
        content.addView(autoAudio);

        int audioCount = 0;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() != C.TRACK_TYPE_AUDIO) continue;
            for (int i = 0; i < group.length; i++) {
                if (!group.isTrackSupported(i, true)) continue;
                audioCount++;
                Format f = group.getTrackFormat(i);
                String details = trackLabel(f, "Audio", audioCount);
                if (f.bitrate > 0) details += " · " + Math.round(f.bitrate / 1000f) + " kb/s";
                if (f.sampleRate > 0) details += " · " + f.sampleRate + " Hz";
                Button b = cloneGrayButton((group.isTrackSelected(i) ? "◉  " : "○  ") + details);
                int index = i;
                b.setOnClickListener(v -> {
                    androidx.media3.common.TrackSelectionParameters.Builder builder =
                            player.getTrackSelectionParameters().buildUpon();
                    builder.setTrackTypeDisabled(C.TRACK_TYPE_AUDIO, false);
                    builder.clearOverridesOfType(C.TRACK_TYPE_AUDIO);
                    builder.addOverride(new TrackSelectionOverride(group.getMediaTrackGroup(), index));
                    player.setTrackSelectionParameters(builder.build());
                    if (prefs != null) {
                        if (f.language != null && !f.language.isEmpty()) {
                            prefs.edit().putString(scopedKey("preferred_audio_language"), f.language).apply();
                        } else {
                            prefs.edit().remove(scopedKey("preferred_audio_language")).apply();
                        }
                    }
                    dialog.dismiss();
                    ui.postDelayed(this::showTracksSidePanel, 250);
                });
                content.addView(b);
            }
        }
        if (audioCount == 0) content.addView(cardText("Solo audio predeterminado."));

        addTrackSectionTitle(content, "CC", "PISTAS DE SUBTÍTULOS");
        Button disable = cloneGrayButton(
                player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)
                        ? "◉  Disable" : "○  Disable");
        disable.setOnClickListener(v -> {
            androidx.media3.common.TrackSelectionParameters.Builder builder =
                    player.getTrackSelectionParameters().buildUpon();
            builder.clearOverridesOfType(C.TRACK_TYPE_TEXT);
            builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, true);
            player.setTrackSelectionParameters(builder.build());
            if (prefs != null) prefs.edit().putString(scopedKey("subtitle_mode"), "off").apply();
            dialog.dismiss();
            ui.postDelayed(this::showTracksSidePanel, 250);
        });
        content.addView(disable);

        int subtitleCount = 0;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() != C.TRACK_TYPE_TEXT) continue;
            for (int i = 0; i < group.length; i++) {
                if (!group.isTrackSupported(i, true)) continue;
                subtitleCount++;
                Format f = group.getTrackFormat(i);
                Button b = cloneGrayButton((group.isTrackSelected(i) ? "◉  " : "○  ") +
                        trackLabel(f, "Subtítulo", subtitleCount));
                int index = i;
                b.setOnClickListener(v -> {
                    androidx.media3.common.TrackSelectionParameters.Builder builder =
                            player.getTrackSelectionParameters().buildUpon();
                    builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, false);
                    builder.clearOverridesOfType(C.TRACK_TYPE_TEXT);
                    builder.addOverride(new TrackSelectionOverride(group.getMediaTrackGroup(), index));
                    player.setTrackSelectionParameters(builder.build());
                    if (prefs != null) {
                        android.content.SharedPreferences.Editor ed = prefs.edit()
                                .putString(scopedKey("subtitle_mode"), "manual");
                        if (f.language != null && !f.language.isEmpty()) {
                            ed.putString(scopedKey("preferred_subtitle_language"), f.language);
                        }
                        ed.apply();
                    }
                    dialog.dismiss();
                    ui.postDelayed(this::showTracksSidePanel, 250);
                });
                content.addView(b);
            }
        }
        if (subtitleCount == 0 && pendingExternalSubtitlePath.isEmpty()) {
            content.addView(cardText("Este contenido no reporta subtítulos internos."));
        }
        if (!pendingExternalSubtitlePath.isEmpty()) {
            content.addView(cardText("CC externo: " + new File(pendingExternalSubtitlePath).getName()));
        }
    }

    private void populateVlcTracksPanel(LinearLayout content, android.app.Dialog dialog) {
        addTrackSectionTitle(content, "▣", "PISTAS DE VIDEO");
        content.addView(cardText("VLC administra automáticamente la pista de video y el decoder."));

        addTrackSectionTitle(content, "♫", "PISTAS DE AUDIO");
        try {
            org.videolan.libvlc.MediaPlayer.TrackDescription[] audio = vlcPlayer.getAudioTracks();
            int current = vlcPlayer.getAudioTrack();
            if (audio != null && audio.length > 0) {
                for (org.videolan.libvlc.MediaPlayer.TrackDescription track : audio) {
                    String name = track.name == null || track.name.isEmpty() ? "Audio" : track.name;
                    Button b = cloneGrayButton((track.id == current ? "◉  " : "○  ") + name);
                    b.setOnClickListener(v -> {
                        vlcPlayer.setAudioTrack(track.id);
                        dialog.dismiss();
                        ui.postDelayed(this::showTracksSidePanel, 250);
                    });
                    content.addView(b);
                }
            } else content.addView(cardText("Sin pistas de audio alternativas."));
        } catch (Exception e) {
            content.addView(cardText("VLC no reportó las pistas de audio."));
        }

        addTrackSectionTitle(content, "CC", "PISTAS DE SUBTÍTULOS");
        Button disable = cloneGrayButton(vlcPlayer.getSpuTrack() < 0 ? "◉  Disable" : "○  Disable");
        disable.setOnClickListener(v -> {
            vlcPlayer.setSpuTrack(-1);
            dialog.dismiss();
            ui.postDelayed(this::showTracksSidePanel, 250);
        });
        content.addView(disable);

        try {
            org.videolan.libvlc.MediaPlayer.TrackDescription[] subs = vlcPlayer.getSpuTracks();
            int current = vlcPlayer.getSpuTrack();
            if (subs != null) {
                for (org.videolan.libvlc.MediaPlayer.TrackDescription track : subs) {
                    String name = track.name == null || track.name.isEmpty() ? "Subtítulo" : track.name;
                    Button b = cloneGrayButton((track.id == current ? "◉  " : "○  ") + name);
                    b.setOnClickListener(v -> {
                        vlcPlayer.setSpuTrack(track.id);
                        dialog.dismiss();
                        ui.postDelayed(this::showTracksSidePanel, 250);
                    });
                    content.addView(b);
                }
            }
        } catch (Exception e) {
            content.addView(cardText("VLC no reportó subtítulos."));
        }
    }

    private void maybeRunAutomaticRefresh() {
        if (prefs == null || server == null || server.isEmpty() ||
                username == null || username.isEmpty() || password == null || password.isEmpty()) return;

        final long now = System.currentTimeMillis();
        final long day = 24L * 60L * 60L * 1000L;

        boolean contentEnabled = prefs.getBoolean("clone_auto_content", true);
        boolean epgEnabled = prefs.getBoolean("clone_auto_epg", true);
        boolean clearCache = prefs.getBoolean("clone_clear_cache", true);

        long lastContent = prefs.getLong("auto_refresh_content_at", 0L);
        long lastEpg = prefs.getLong("auto_refresh_epg_at", 0L);
        long lastCache = prefs.getLong("auto_clear_cache_at", 0L);

        if (clearCache && now - lastCache >= 7L * day) {
            artCache.evictAll();
            prefs.edit().putLong("auto_clear_cache_at", now).apply();
        }

        if (contentEnabled && now - lastContent >= 2L * day) {
            io.execute(() -> {
                try {
                    request("get_live_categories", null);
                    request("get_vod_categories", null);
                    request("get_series_categories", null);
                    prefs.edit().putLong("auto_refresh_content_at", System.currentTimeMillis()).apply();
                } catch (Exception ignored) {}
            });
        }

        if (epgEnabled && now - lastEpg >= day) {
            io.execute(() -> {
                try {
                    JSONArray channels = new JSONArray(request("get_live_streams", null));
                    int limit = Math.min(8, channels.length());
                    for (int i = 0; i < limit; i++) {
                        JSONObject row = channels.optJSONObject(i);
                        if (row == null) continue;
                        String id = String.valueOf(row.opt("stream_id"));
                        try { request("get_short_epg", "stream_id=" + enc(id) + "&limit=2"); }
                        catch (Exception ignored) {}
                    }
                    prefs.edit().putLong("auto_refresh_epg_at", System.currentTimeMillis()).apply();
                } catch (Exception ignored) {}
            });
        }
    }

'''
s = s.replace(marker2, methods + marker2, 1)

p.write_text(s)
print('v2.8 original-style tracks panel and automatic refresh patch applied')
