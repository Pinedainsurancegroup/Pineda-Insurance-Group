from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import androidx.media3.ui.PlayerView;\n', '''import androidx.media3.ui.PlayerView;\n\nimport org.videolan.libvlc.LibVLC;\nimport org.videolan.libvlc.Media;\nimport org.videolan.libvlc.util.VLCVideoLayout;\n''')
s = s.replace('    private ExoPlayer player;\n', '''    private ExoPlayer player;\n    private LibVLC libVLC;\n    private org.videolan.libvlc.MediaPlayer vlcPlayer;\n''')

new_play = r'''    private void playStream(String title, String primaryUrl, String fallbackUrl, Runnable back) {
        releasePlayer();
        systemBack = () -> {
            releasePlayer();
            back.run();
        };

        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.BLACK);
        screen.setPadding(dp(8), dp(8), dp(8), dp(8));
        setContentView(screen);
        activePlaybackUrl = primaryUrl == null ? "" : primaryUrl;

        boolean immersive = prefs != null && prefs.getBoolean("immersive_player", true);
        if (immersive) {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }

        Button backBtn = secondaryButton("← VOLVER");
        backBtn.setOnClickListener(v -> systemBack.run());
        screen.addView(backBtn, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        TextView name = label(title);
        name.setTextSize(18);
        name.setTextColor(Color.WHITE);
        name.setGravity(Gravity.CENTER_HORIZONTAL);
        name.setPadding(0, dp(6), 0, dp(6));
        screen.addView(name);

        LinearLayout tools = new LinearLayout(this);
        tools.setOrientation(LinearLayout.HORIZONTAL);
        tools.setGravity(Gravity.CENTER);

        Button pipButton = secondaryButton("▣ PiP");
        LinearLayout.LayoutParams toolParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        toolParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        pipButton.setLayoutParams(toolParams);
        pipButton.setOnClickListener(v -> enterPipMode());
        tools.addView(pipButton);

        Button externalButton = secondaryButton("↗ EXTERNO");
        LinearLayout.LayoutParams extParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        extParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        externalButton.setLayoutParams(extParams);
        externalButton.setOnClickListener(v -> openExternalPlayer());
        tools.addView(externalButton);

        Button sleepButton = secondaryButton(sleepTimerLabel());
        LinearLayout.LayoutParams sleepParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        sleepParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        sleepButton.setLayoutParams(sleepParams);
        sleepButton.setOnClickListener(v -> showSleepTimerDialog());
        tools.addView(sleepButton);

        MediaRouteButton routeButton = new MediaRouteButton(this);
        CastButtonFactory.setUpMediaRouteButton(this, routeButton);
        LinearLayout.LayoutParams routeParams = new LinearLayout.LayoutParams(dp(48), dp(48));
        routeParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        routeButton.setLayoutParams(routeParams);
        tools.addView(routeButton);

        Button castButton = secondaryButton("CAST ▶");
        LinearLayout.LayoutParams castParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        castParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        castButton.setLayoutParams(castParams);
        castButton.setOnClickListener(v -> castActiveStream(title));
        tools.addView(castButton);

        screen.addView(tools);

        TextView state = label("Conectando al stream…");
        state.setTextColor(Color.LTGRAY);
        state.setGravity(Gravity.CENTER_HORIZONTAL);
        screen.addView(state);

        PlayerView playerView = new PlayerView(this);
        playerView.setUseController(true);
        playerView.setKeepScreenOn(true);
        LinearLayout.LayoutParams vp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        screen.addView(playerView, vp);

        VLCVideoLayout vlcView = new VLCVideoLayout(this);
        vlcView.setVisibility(android.view.View.GONE);
        screen.addView(vlcView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        String playerMode = prefs == null ? "auto" : prefs.getString("player_mode", "auto");
        int networkCache = prefs == null ? 2500 : prefs.getInt("network_cache_ms", 2500);

        if ("vlc".equals(playerMode)) {
            startVlcPlayback(vlcView, playerView, primaryUrl, networkCache, state);
            return;
        }

        DefaultHttpDataSource.Factory httpFactory = new DefaultHttpDataSource.Factory()
                .setUserAgent("PIMFLEXTV/4.0.2 (Android)")
                .setAllowCrossProtocolRedirects(true)
                .setConnectTimeoutMs(15000)
                .setReadTimeoutMs(30000);

        DefaultMediaSourceFactory mediaSourceFactory = new DefaultMediaSourceFactory(this)
                .setDataSourceFactory(httpFactory);

        player = new ExoPlayer.Builder(this)
                .setMediaSourceFactory(mediaSourceFactory)
                .build();
        playerView.setPlayer(player);

        final int[] attempt = {0};
        final String[] urls = fallbackUrl != null && !fallbackUrl.isEmpty()
                ? new String[]{fallbackUrl, primaryUrl}
                : new String[]{primaryUrl};

        Player.Listener listener = new Player.Listener() {
            @Override
            public void onPlaybackStateChanged(int playbackState) {
                if (playbackState == Player.STATE_BUFFERING) {
                    state.setText(attempt[0] == 0 ? "Conectando…" : "Probando formato alternativo…");
                } else if (playbackState == Player.STATE_READY) {
                    state.setText("");
                    applyPendingResume();
                } else if (playbackState == Player.STATE_ENDED) {
                    state.setText("Reproducción finalizada");
                }
            }

            @Override
            public void onPlayerError(PlaybackException error) {
                if (attempt[0] + 1 < urls.length) {
                    attempt[0]++;
                    state.setText("Cambiando formato de stream…");
                    player.setMediaItem(MediaItem.fromUri(Uri.parse(urls[attempt[0]])));
                    player.prepare();
                    player.play();
                    return;
                }

                if ("exo".equals(playerMode)) {
                    state.setText("ExoPlayer no pudo reproducir este stream");
                    Toast.makeText(MainActivity.this,
                            "Error: " + error.getErrorCodeName(),
                            Toast.LENGTH_LONG).show();
                    return;
                }

                state.setText("Activando motor VLC compatible con IPTV…");
                String url = urls[Math.min(attempt[0], urls.length - 1)];
                startVlcPlayback(vlcView, playerView, url, networkCache, state);
            }
        };
        player.addListener(listener);
        player.setMediaItem(MediaItem.fromUri(Uri.parse(urls[0])));
        player.prepare();
        player.play();
    }

    private void startVlcPlayback(VLCVideoLayout vlcView, PlayerView playerView,
                                  String url, int networkCache, TextView state) {
        try {
            if (player != null) {
                player.stop();
                playerView.setPlayer(null);
                player.release();
                player = null;
            }
            playerView.setVisibility(android.view.View.GONE);
            vlcView.setVisibility(android.view.View.VISIBLE);

            java.util.ArrayList<String> options = new java.util.ArrayList<>();
            options.add("--network-caching=" + networkCache);
            options.add("--http-reconnect");
            options.add("--no-drop-late-frames");
            options.add("--no-skip-frames");
            libVLC = new LibVLC(MainActivity.this, options);
            vlcPlayer = new org.videolan.libvlc.MediaPlayer(libVLC);
            vlcPlayer.attachViews(vlcView, null, false, false);

            Media media = new Media(libVLC, Uri.parse(url));
            media.setHWDecoderEnabled(true, false);
            media.addOption(":network-caching=" + networkCache);
            media.addOption(":http-user-agent=PIMFLEXTV/4.0.2 (Android)");
            vlcPlayer.setMedia(media);
            media.release();
            vlcPlayer.play();
            state.setText("");
            ui.postDelayed(this::applyPendingResume, 700);
        } catch (Exception vlcError) {
            state.setText("No fue posible reproducir este stream");
            Toast.makeText(MainActivity.this,
                    "VLC: " + vlcError.getClass().getSimpleName(),
                    Toast.LENGTH_LONG).show();
        }
    }

'''

s, n = re.subn(r'    private void playStream\(String title, String primaryUrl, String fallbackUrl, Runnable back\) \{.*?\n    \}\n\n    private void releasePlayer\(\)', new_play + '    private void releasePlayer()', s, flags=re.S)
if n != 1:
    raise SystemExit(f'playStream replacement count={n}')

old_release = '''    private void releasePlayer() {
        if (player != null) {
            player.stop();
            player.release();
            player = null;
        }
    }
'''
new_release = '''    private void releasePlayer() {
        if (player != null || vlcPlayer != null) saveProgressNow();
        if (player != null) {
            player.stop();
            player.release();
            player = null;
        }
        if (vlcPlayer != null) {
            try { vlcPlayer.stop(); } catch (Exception ignored) {}
            try { vlcPlayer.detachViews(); } catch (Exception ignored) {}
            try { vlcPlayer.release(); } catch (Exception ignored) {}
            vlcPlayer = null;
        }
        if (libVLC != null) {
            try { libVLC.release(); } catch (Exception ignored) {}
            libVLC = null;
        }
        activePlaybackUrl = "";
        if (sleepTimerRunnable != null) {
            ui.removeCallbacks(sleepTimerRunnable);
            sleepTimerRunnable = null;
        }
        sleepTimerMinutes = 0;
    }
'''
if old_release not in s:
    raise SystemExit('releasePlayer block not found')
s = s.replace(old_release, new_release)
p.write_text(s)
