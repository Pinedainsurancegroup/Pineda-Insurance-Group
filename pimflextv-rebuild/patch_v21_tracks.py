from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import androidx.media3.ui.PlayerView;\n', '''import androidx.media3.ui.PlayerView;\nimport androidx.media3.common.C;\nimport androidx.media3.common.Format;\nimport androidx.media3.common.TrackSelectionOverride;\nimport androidx.media3.common.Tracks;\n''')

toolbar_marker = '''        LinearLayout tools = new LinearLayout(this);
        tools.setOrientation(LinearLayout.HORIZONTAL);
        tools.setGravity(Gravity.CENTER);
'''
toolbar_repl = '''        LinearLayout trackTools = new LinearLayout(this);
        trackTools.setOrientation(LinearLayout.HORIZONTAL);
        trackTools.setGravity(Gravity.CENTER);

        Button audioButton = secondaryButton("🔊 AUDIO");
        LinearLayout.LayoutParams audioParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        audioParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        audioButton.setLayoutParams(audioParams);
        audioButton.setOnClickListener(v -> showAudioTrackDialog());
        trackTools.addView(audioButton);

        Button subtitleButton = secondaryButton("💬 SUBTÍTULOS");
        LinearLayout.LayoutParams subtitleParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        subtitleParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        subtitleButton.setLayoutParams(subtitleParams);
        subtitleButton.setOnClickListener(v -> showSubtitleTrackDialog());
        trackTools.addView(subtitleButton);

        screen.addView(trackTools);

        LinearLayout tools = new LinearLayout(this);
        tools.setOrientation(LinearLayout.HORIZONTAL);
        tools.setGravity(Gravity.CENTER);
'''
if toolbar_marker not in s:
    raise SystemExit('player toolbar marker not found')
s = s.replace(toolbar_marker, toolbar_repl, 1)

ready_marker = '''                    state.setText("");
                    applyPendingResume();
'''
ready_repl = '''                    state.setText("");
                    applyPendingResume();
                    applyRememberedTrackPreferences();
'''
if ready_marker not in s:
    raise SystemExit('player ready marker not found')
s = s.replace(ready_marker, ready_repl, 1)

vlc_marker = '''            vlcPlayer.play();
            state.setText("");
            ui.postDelayed(this::applyPendingResume, 700);
'''
vlc_repl = '''            vlcPlayer.play();
            state.setText("");
            ui.postDelayed(this::applyPendingResume, 700);
            ui.postDelayed(this::applyRememberedVlcTrackPreferences, 900);
'''
if vlc_marker not in s:
    raise SystemExit('VLC play marker not found')
s = s.replace(vlc_marker, vlc_repl, 1)

marker = '    private void releasePlayer() {\n'
methods = r'''    private void showAudioTrackDialog() {
        if (player != null) {
            showExoAudioTracks();
            return;
        }
        if (vlcPlayer != null) {
            showVlcAudioTracks();
            return;
        }
        Toast.makeText(this, "El reproductor todavía no cargó las pistas de audio.", Toast.LENGTH_SHORT).show();
    }

    private void showSubtitleTrackDialog() {
        if (player != null) {
            showExoSubtitleTracks();
            return;
        }
        if (vlcPlayer != null) {
            showVlcSubtitleTracks();
            return;
        }
        Toast.makeText(this, "El reproductor todavía no cargó los subtítulos.", Toast.LENGTH_SHORT).show();
    }

    private void showExoAudioTracks() {
        Tracks tracks = player.getCurrentTracks();
        List<Tracks.Group> groups = new ArrayList<>();
        List<Integer> indices = new ArrayList<>();
        List<String> labels = new ArrayList<>();
        labels.add("Automático");

        int selected = 0;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() != C.TRACK_TYPE_AUDIO) continue;
            for (int i = 0; i < group.length; i++) {
                if (!group.isTrackSupported(i, true)) continue;
                Format format = group.getTrackFormat(i);
                groups.add(group);
                indices.add(i);
                labels.add(trackLabel(format, "Audio", labels.size()));
                if (group.isTrackSelected(i)) selected = labels.size() - 1;
            }
        }

        if (labels.size() == 1) {
            Toast.makeText(this, "Este contenido solo reporta la pista de audio predeterminada.", Toast.LENGTH_LONG).show();
            return;
        }

        String[] options = labels.toArray(new String[0]);
        new AlertDialog.Builder(this)
                .setTitle("Idioma / pista de audio")
                .setSingleChoiceItems(options, selected, (dialog, which) -> {
                    androidx.media3.common.TrackSelectionParameters.Builder builder =
                            player.getTrackSelectionParameters().buildUpon();
                    builder.setTrackTypeDisabled(C.TRACK_TYPE_AUDIO, false);
                    builder.clearOverridesOfType(C.TRACK_TYPE_AUDIO);

                    if (which == 0) {
                        builder.setPreferredAudioLanguage(null);
                        if (prefs != null) prefs.edit()
                                .remove(scopedKey("preferred_audio_language"))
                                .apply();
                    } else {
                        Tracks.Group group = groups.get(which - 1);
                        int trackIndex = indices.get(which - 1);
                        Format format = group.getTrackFormat(trackIndex);
                        builder.addOverride(new TrackSelectionOverride(group.getMediaTrackGroup(), trackIndex));
                        if (prefs != null) {
                            if (format.language != null && !format.language.isEmpty()) {
                                prefs.edit().putString(scopedKey("preferred_audio_language"), format.language).apply();
                            } else {
                                prefs.edit().remove(scopedKey("preferred_audio_language")).apply();
                            }
                        }
                    }

                    player.setTrackSelectionParameters(builder.build());
                    dialog.dismiss();
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void showExoSubtitleTracks() {
        Tracks tracks = player.getCurrentTracks();
        List<Tracks.Group> groups = new ArrayList<>();
        List<Integer> indices = new ArrayList<>();
        List<String> labels = new ArrayList<>();
        labels.add("Desactivados");
        labels.add("Automático");

        int selected = player.getTrackSelectionParameters().disabledTrackTypes.contains(C.TRACK_TYPE_TEXT) ? 0 : 1;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() != C.TRACK_TYPE_TEXT) continue;
            for (int i = 0; i < group.length; i++) {
                if (!group.isTrackSupported(i, true)) continue;
                Format format = group.getTrackFormat(i);
                groups.add(group);
                indices.add(i);
                labels.add(trackLabel(format, "Subtítulo", labels.size() - 1));
                if (group.isTrackSelected(i)) selected = labels.size() - 1;
            }
        }

        if (labels.size() == 2) {
            Toast.makeText(this, "Este contenido no reporta pistas de subtítulos.", Toast.LENGTH_LONG).show();
            return;
        }

        String[] options = labels.toArray(new String[0]);
        new AlertDialog.Builder(this)
                .setTitle("Subtítulos")
                .setSingleChoiceItems(options, selected, (dialog, which) -> {
                    androidx.media3.common.TrackSelectionParameters.Builder builder =
                            player.getTrackSelectionParameters().buildUpon();
                    builder.clearOverridesOfType(C.TRACK_TYPE_TEXT);

                    if (which == 0) {
                        builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, true);
                        if (prefs != null) prefs.edit()
                                .putString(scopedKey("subtitle_mode"), "off")
                                .remove(scopedKey("preferred_subtitle_language"))
                                .apply();
                    } else if (which == 1) {
                        builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, false);
                        builder.setPreferredTextLanguage(null);
                        if (prefs != null) prefs.edit()
                                .putString(scopedKey("subtitle_mode"), "auto")
                                .remove(scopedKey("preferred_subtitle_language"))
                                .apply();
                    } else {
                        builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, false);
                        Tracks.Group group = groups.get(which - 2);
                        int trackIndex = indices.get(which - 2);
                        Format format = group.getTrackFormat(trackIndex);
                        builder.addOverride(new TrackSelectionOverride(group.getMediaTrackGroup(), trackIndex));
                        if (prefs != null) {
                            android.content.SharedPreferences.Editor editor = prefs.edit()
                                    .putString(scopedKey("subtitle_mode"), "manual");
                            if (format.language != null && !format.language.isEmpty()) {
                                editor.putString(scopedKey("preferred_subtitle_language"), format.language);
                            } else {
                                editor.remove(scopedKey("preferred_subtitle_language"));
                            }
                            editor.apply();
                        }
                    }

                    player.setTrackSelectionParameters(builder.build());
                    dialog.dismiss();
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private String trackLabel(Format format, String fallback, int number) {
        StringBuilder label = new StringBuilder();
        if (format.label != null && !format.label.trim().isEmpty()) {
            label.append(format.label.trim());
        }

        String language = languageName(format.language);
        if (!language.isEmpty()) {
            if (label.length() > 0) label.append(" · ");
            label.append(language);
        }

        if (format.channelCount > 0) {
            if (label.length() > 0) label.append(" · ");
            if (format.channelCount == 1) label.append("Mono");
            else if (format.channelCount == 2) label.append("Stereo");
            else label.append(format.channelCount).append(" canales");
        }

        if (label.length() == 0 && format.sampleMimeType != null && !format.sampleMimeType.isEmpty()) {
            label.append(format.sampleMimeType.replace("audio/", "").replace("text/", "").toUpperCase(Locale.ROOT));
        }
        if (label.length() == 0) label.append(fallback).append(" ").append(number);
        return label.toString();
    }

    private String languageName(String code) {
        if (code == null || code.trim().isEmpty() || "und".equalsIgnoreCase(code)) return "";
        try {
            Locale locale = Locale.forLanguageTag(code);
            String name = locale.getDisplayLanguage(Locale.getDefault());
            if (name == null || name.trim().isEmpty()) return code.toUpperCase(Locale.ROOT);
            return name.substring(0, 1).toUpperCase(Locale.getDefault()) + name.substring(1);
        } catch (Exception e) {
            return code.toUpperCase(Locale.ROOT);
        }
    }

    private void applyRememberedTrackPreferences() {
        if (player == null || prefs == null) return;
        try {
            androidx.media3.common.TrackSelectionParameters.Builder builder =
                    player.getTrackSelectionParameters().buildUpon();

            String audioLanguage = prefs.getString(scopedKey("preferred_audio_language"), "");
            if (!audioLanguage.isEmpty()) builder.setPreferredAudioLanguage(audioLanguage);

            String subtitleMode = prefs.getString(scopedKey("subtitle_mode"), "auto");
            if ("off".equals(subtitleMode)) {
                builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, true);
            } else {
                builder.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, false);
                String subtitleLanguage = prefs.getString(scopedKey("preferred_subtitle_language"), "");
                if (!subtitleLanguage.isEmpty()) builder.setPreferredTextLanguage(subtitleLanguage);
            }

            player.setTrackSelectionParameters(builder.build());
        } catch (Exception ignored) {}
    }

    private void showVlcAudioTracks() {
        try {
            org.videolan.libvlc.MediaPlayer.TrackDescription[] tracks = vlcPlayer.getAudioTracks();
            if (tracks == null || tracks.length == 0) {
                Toast.makeText(this, "VLC no reportó pistas de audio.", Toast.LENGTH_LONG).show();
                return;
            }

            String[] labels = new String[tracks.length];
            int selected = 0;
            int current = vlcPlayer.getAudioTrack();
            for (int i = 0; i < tracks.length; i++) {
                labels[i] = tracks[i].name == null || tracks[i].name.isEmpty()
                        ? "Audio " + (i + 1) : tracks[i].name;
                if (tracks[i].id == current) selected = i;
            }

            new AlertDialog.Builder(this)
                    .setTitle("Idioma / pista de audio")
                    .setSingleChoiceItems(labels, selected, (dialog, which) -> {
                        vlcPlayer.setAudioTrack(tracks[which].id);
                        if (prefs != null) prefs.edit()
                                .putString(scopedKey("vlc_audio_name"), labels[which])
                                .apply();
                        dialog.dismiss();
                    })
                    .setNegativeButton("Cancelar", null)
                    .show();
        } catch (Exception e) {
            Toast.makeText(this, "No se pudieron leer las pistas de audio.", Toast.LENGTH_LONG).show();
        }
    }

    private void showVlcSubtitleTracks() {
        try {
            org.videolan.libvlc.MediaPlayer.TrackDescription[] tracks = vlcPlayer.getSpuTracks();
            int extra = tracks == null ? 0 : tracks.length;
            String[] labels = new String[extra + 1];
            labels[0] = "Desactivados";
            int selected = 0;
            int current = vlcPlayer.getSpuTrack();

            for (int i = 0; i < extra; i++) {
                labels[i + 1] = tracks[i].name == null || tracks[i].name.isEmpty()
                        ? "Subtítulo " + (i + 1) : tracks[i].name;
                if (tracks[i].id == current) selected = i + 1;
            }

            new AlertDialog.Builder(this)
                    .setTitle("Subtítulos")
                    .setSingleChoiceItems(labels, selected, (dialog, which) -> {
                        if (which == 0) {
                            vlcPlayer.setSpuTrack(-1);
                            if (prefs != null) prefs.edit()
                                    .putString(scopedKey("vlc_subtitle_mode"), "off")
                                    .remove(scopedKey("vlc_subtitle_name"))
                                    .apply();
                        } else {
                            vlcPlayer.setSpuTrack(tracks[which - 1].id);
                            if (prefs != null) prefs.edit()
                                    .putString(scopedKey("vlc_subtitle_mode"), "manual")
                                    .putString(scopedKey("vlc_subtitle_name"), labels[which])
                                    .apply();
                        }
                        dialog.dismiss();
                    })
                    .setNegativeButton("Cancelar", null)
                    .show();
        } catch (Exception e) {
            Toast.makeText(this, "No se pudieron leer los subtítulos.", Toast.LENGTH_LONG).show();
        }
    }

    private void applyRememberedVlcTrackPreferences() {
        if (vlcPlayer == null || prefs == null) return;
        try {
            String audioName = prefs.getString(scopedKey("vlc_audio_name"), "");
            if (!audioName.isEmpty()) {
                org.videolan.libvlc.MediaPlayer.TrackDescription[] audio = vlcPlayer.getAudioTracks();
                if (audio != null) {
                    for (org.videolan.libvlc.MediaPlayer.TrackDescription track : audio) {
                        if (track.name != null && track.name.equalsIgnoreCase(audioName)) {
                            vlcPlayer.setAudioTrack(track.id);
                            break;
                        }
                    }
                }
            }

            String subtitleMode = prefs.getString(scopedKey("vlc_subtitle_mode"), "");
            if ("off".equals(subtitleMode)) {
                vlcPlayer.setSpuTrack(-1);
            } else {
                String subtitleName = prefs.getString(scopedKey("vlc_subtitle_name"), "");
                if (!subtitleName.isEmpty()) {
                    org.videolan.libvlc.MediaPlayer.TrackDescription[] subtitles = vlcPlayer.getSpuTracks();
                    if (subtitles != null) {
                        for (org.videolan.libvlc.MediaPlayer.TrackDescription track : subtitles) {
                            if (track.name != null && track.name.equalsIgnoreCase(subtitleName)) {
                                vlcPlayer.setSpuTrack(track.id);
                                break;
                            }
                        }
                    }
                }
            }
        } catch (Exception ignored) {}
    }

'''
if marker not in s:
    raise SystemExit('releasePlayer marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('Audio and subtitle track selector patch applied')
