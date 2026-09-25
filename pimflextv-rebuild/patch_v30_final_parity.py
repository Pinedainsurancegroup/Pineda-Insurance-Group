from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Dynamic version helper and final parity/settings tiles.
settings_marker = '        addCloneSettingsTile(grid, "CC", "OPENSUBTITLES", this::showOpenSubtitlesSettings);\n'
if settings_marker not in s:
    raise SystemExit('v3 settings marker not found')
settings_add = '''        addCloneSettingsTile(grid, "CC", "OPENSUBTITLES", this::showOpenSubtitlesSettings);
        addCloneSettingsTile(grid, "CAST", "CHROMECAST", this::showCastControlScreen);
        addCloneSettingsTile(grid, "✓", "ESTADO DEL SISTEMA", this::showSystemStatusScreen);
'''
s = s.replace(settings_marker, settings_add, 1)

# Replace hardcoded visible version labels with runtime package version where practical.
s = s.replace('TextView version = label("v2.3.0");',
              'TextView version = label("v" + appVersionName());')
s = s.replace('TextView heading = label("Versión instalada: v2.5.0");',
              'TextView heading = label("Versión instalada: v" + appVersionName());')

# Lazy Cast button in player: no Cast framework initialization until the user taps it.
tool_marker = '''        Button sleepButton = secondaryButton(sleepTimerLabel());
        LinearLayout.LayoutParams sleepParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        sleepParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        sleepButton.setLayoutParams(sleepParams);
        sleepButton.setOnClickListener(v -> showSleepTimerDialog());
        tools.addView(sleepButton);

        screen.addView(tools);
'''
if tool_marker not in s:
    raise SystemExit('v3 player tools marker not found')
tool_repl = '''        Button sleepButton = secondaryButton(sleepTimerLabel());
        LinearLayout.LayoutParams sleepParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        sleepParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        sleepButton.setLayoutParams(sleepParams);
        sleepButton.setOnClickListener(v -> showSleepTimerDialog());
        tools.addView(sleepButton);

        Button castButtonSafe = secondaryButton("CAST");
        LinearLayout.LayoutParams castSafeParams = new LinearLayout.LayoutParams(0, dp(48), 1f);
        castSafeParams.setMargins(dp(2), dp(2), dp(2), dp(2));
        castButtonSafe.setLayoutParams(castSafeParams);
        castButtonSafe.setOnClickListener(v -> showCastChooser(title));
        tools.addView(castButtonSafe);

        screen.addView(tools);
'''
s = s.replace(tool_marker, tool_repl, 1)

# Insert final utility methods before OpenSubtitles settings.
marker = '    private void showOpenSubtitlesSettings() {\n'
if marker not in s:
    raise SystemExit('OpenSubtitles method marker not found for v3')

methods = r'''    private String appVersionName() {
        try {
            android.content.pm.PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return info.versionName == null ? "" : info.versionName;
        } catch (Exception e) {
            return "";
        }
    }

    private long appVersionCode() {
        try {
            android.content.pm.PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            if (Build.VERSION.SDK_INT >= 28) return info.getLongVersionCode();
            return info.versionCode;
        } catch (Exception e) {
            return 0L;
        }
    }

    private void showCastChooser(String title) {
        if (activePlaybackUrl == null || activePlaybackUrl.trim().isEmpty()) {
            Toast.makeText(this, "No hay un stream activo para enviar.", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            android.app.Dialog dialog = new android.app.Dialog(this);
            LinearLayout panel = new LinearLayout(this);
            panel.setOrientation(LinearLayout.VERTICAL);
            panel.setBackgroundResource(R.drawable.clone_panel_bg);
            panel.setPadding(dp(28), dp(24), dp(28), dp(24));

            TextView heading = label("CHROMECAST");
            heading.setTypeface(Typeface.DEFAULT_BOLD);
            heading.setTextSize(22);
            heading.setGravity(Gravity.CENTER);
            heading.setPadding(0, 0, 0, dp(12));
            panel.addView(heading);

            panel.addView(cardText("Selecciona un dispositivo Cast y después pulsa ENVIAR STREAM. "
                    + "Chromecast solo se inicializa cuando abres esta pantalla."));

            MediaRouteButton route = new MediaRouteButton(this);
            route.setContentDescription("Seleccionar Chromecast");
            CastButtonFactory.setUpMediaRouteButton(this, route);
            LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(64));
            rp.setMargins(0, dp(8), 0, dp(8));
            panel.addView(route, rp);

            Button send = cloneGreenButton("ENVIAR STREAM");
            send.setOnClickListener(v -> {
                castActiveStream(title);
                dialog.dismiss();
            });
            panel.addView(send, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(58)));

            Button close = cloneRedButton("CERRAR");
            close.setOnClickListener(v -> dialog.dismiss());
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(58));
            cp.setMargins(0, dp(8), 0, 0);
            panel.addView(close, cp);

            dialog.setContentView(panel);
            android.view.Window window = dialog.getWindow();
            if (window != null) {
                window.setBackgroundDrawableResource(android.R.color.transparent);
                window.setLayout(Math.min(dp(560),
                        Math.round(getResources().getDisplayMetrics().widthPixels * 0.65f)),
                        ViewGroup.LayoutParams.WRAP_CONTENT);
            }
            dialog.show();
            if (window != null) {
                window.setLayout(Math.min(dp(560),
                        Math.round(getResources().getDisplayMetrics().widthPixels * 0.65f)),
                        ViewGroup.LayoutParams.WRAP_CONTENT);
            }
        } catch (Throwable e) {
            Toast.makeText(this,
                    "Chromecast no está disponible en este dispositivo: " + cleanError(
                            e instanceof Exception ? (Exception) e : new Exception(e)),
                    Toast.LENGTH_LONG).show();
        }
    }

    private void showCastControlScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("CHROMECAST", this::showSettings);

        root.addView(cardText("La integración Cast está aislada del reproductor principal. "
                + "Esto evita que un error de Google Cast cierre Live TV, Cine o Series."));

        try {
            MediaRouteButton route = new MediaRouteButton(this);
            route.setContentDescription("Seleccionar Chromecast");
            CastButtonFactory.setUpMediaRouteButton(this, route);
            root.addView(route, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(72)));

            CastContext context = CastContext.getSharedInstance(this);
            CastSession session = context.getSessionManager().getCurrentCastSession();
            String status = session != null && session.isConnected()
                    ? "Chromecast conectado" : "Sin dispositivo Cast conectado";
            root.addView(cardText(status));
        } catch (Throwable e) {
            root.addView(cardText("Google Cast no está disponible en este dispositivo. "
                    + "El resto de PIMFLEX TV continúa funcionando normalmente."));
        }

        Button back = cloneRedButton("ATRÁS");
        back.setOnClickListener(v -> showSettings());
        root.addView(back);
    }

    private void showSystemStatusScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("ESTADO DEL SISTEMA", this::showSettings);

        StringBuilder sb = new StringBuilder();
        sb.append("PIMFLEX TV v").append(appVersionName())
                .append(" · build ").append(appVersionCode()).append("\n\n");
        sb.append("✓ Xtream Codes / player_api\n");
        sb.append("✓ Live TV + zapping + EPG\n");
        sb.append("✓ Movies / Series / Catch-Up\n");
        sb.append("✓ ExoPlayer + VLC fallback\n");
        sb.append("✓ Audio / subtítulos / panel de pistas\n");
        sb.append("✓ OpenSubtitles configurable\n");
        sb.append("✓ M3U URL + archivo local\n");
        sb.append("✓ XMLTV externo\n");
        sb.append("✓ Multi-DNS\n");
        sb.append("✓ Stalker / MAG\n");
        sb.append("✓ Multi-Screen\n");
        sb.append("✓ Descargas + grabaciones DVR\n");
        sb.append("✓ Radio + media local + One Stream\n");
        sb.append("✓ PiP + reproductor externo + Sleep Timer\n");
        sb.append("✓ Backup / Restore\n");
        sb.append("✓ Actualizaciones y anuncios bajo tu control\n");
        sb.append("✓ Client Area configurable\n");
        sb.append("✓ VPN mediante perfil OVPN y app compatible\n");
        sb.append("✓ Chromecast aislado / opcional\n");

        root.addView(cardText(sb.toString()));

        Button test = cloneGreenButton("PROBAR SERVIDOR ACTUAL");
        test.setOnClickListener(v -> runSystemServerTest());
        root.addView(test);

        Button account = cloneGrayButton("SUBSCRIPTION INFO");
        account.setOnClickListener(v -> showAccount());
        root.addView(account);
    }

    private void runSystemServerTest() {
        showLoading("Comprobando servidor y APIs…");
        io.execute(() -> {
            StringBuilder result = new StringBuilder();
            try {
                JSONObject auth = new JSONObject(request(null, null));
                JSONObject user = auth.optJSONObject("user_info");
                result.append(user != null ? "✓ Login Xtream\n" : "✗ Login Xtream\n");
            } catch (Exception e) {
                result.append("✗ Login Xtream: ").append(cleanError(e)).append("\n");
            }

            try {
                JSONArray live = new JSONArray(request("get_live_streams", null));
                result.append("✓ Live TV: ").append(live.length()).append(" streams\n");
            } catch (Exception e) {
                result.append("✗ Live TV: ").append(cleanError(e)).append("\n");
            }

            try {
                JSONArray vod = new JSONArray(request("get_vod_streams", null));
                result.append("✓ Cine: ").append(vod.length()).append(" títulos\n");
            } catch (Exception e) {
                result.append("✗ Cine: ").append(cleanError(e)).append("\n");
            }

            try {
                JSONArray series = new JSONArray(request("get_series", null));
                result.append("✓ Series: ").append(series.length()).append(" títulos\n");
            } catch (Exception e) {
                result.append("✗ Series: ").append(cleanError(e)).append("\n");
            }

            String finalResult = result.toString();
            ui.post(() -> showSystemTestResult(finalResult));
        });
    }

    private void showSystemTestResult(String result) {
        systemBack = this::showSystemStatusScreen;
        root = cloneScreen();
        addCloneHeader("DIAGNÓSTICO", this::showSystemStatusScreen);
        root.addView(cardText(result));
        Button back = cloneRedButton("ATRÁS");
        back.setOnClickListener(v -> showSystemStatusScreen());
        root.addView(back);
    }

'''
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v3.0 final parity, lazy Cast and diagnostics patch applied')
