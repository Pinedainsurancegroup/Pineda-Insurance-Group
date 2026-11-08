from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import android.app.Activity;\n', 'import android.app.Activity;\nimport android.app.DownloadManager;\n')
s = s.replace('import android.os.Build;\n', 'import android.os.Build;\nimport android.os.Environment;\n')

tile = '        addDashboardTile(menu, "▦  MULTI-SCREEN", this::loadMultiScreenChannels, cols);\n'
if tile not in s:
    raise SystemExit('multiscreen tile marker not found')
s = s.replace(tile, '''        addDashboardTile(menu, "▦  MULTI-SCREEN", this::loadMultiScreenChannels, cols);
        addDashboardTile(menu, "🚀  SPEED TEST", this::runSpeedTest, cols);
''', 1)

marker = '    private void loadMultiScreenChannels() {\n'
methods = r'''    private void runSpeedTest() {
        showLoading("Midiendo velocidad de descarga…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                long startNs = System.nanoTime();
                conn = (HttpURLConnection) new URL("https://speed.cloudflare.com/__down?bytes=5000000").openConnection();
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(20000);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/2.0 Android");
                conn.setUseCaches(false);
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);

                InputStream in = conn.getInputStream();
                byte[] buffer = new byte[32 * 1024];
                long bytes = 0L;
                int read;
                while ((read = in.read(buffer)) != -1) bytes += read;
                in.close();
                long elapsedNs = Math.max(1L, System.nanoTime() - startNs);
                double seconds = elapsedNs / 1_000_000_000.0;
                double mbps = (bytes * 8.0) / seconds / 1_000_000.0;
                double megabytes = bytes / 1_000_000.0;
                String result = String.format(Locale.US,
                        "Velocidad aproximada: %.1f Mbps\nDescargados: %.1f MB\nTiempo: %.2f s",
                        mbps, megabytes, seconds);
                ui.post(() -> showSpeedTestResult(result));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Speed Test", e, this::showDashboard));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void showSpeedTestResult(String result) {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("🚀 SPEED TEST", 28);
        root.addView(cardText(result));
        Button again = actionButton("REPETIR PRUEBA");
        again.setOnClickListener(v -> runSpeedTest());
        root.addView(again);
    }

    private void downloadVod(String title, String url, String ext) {
        try {
            String clean = title == null ? "PIMFLEX_TV" : title.replaceAll("[^A-Za-z0-9._ -]", "_").trim();
            if (clean.isEmpty()) clean = "PIMFLEX_TV";
            String safeExtension = safeExt(ext);
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            request.setTitle(title);
            request.setDescription("Descarga PIMFLEX TV");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setAllowedOverMetered(true);
            request.setAllowedOverRoaming(false);
            request.setDestinationInExternalFilesDir(this, Environment.DIRECTORY_MOVIES,
                    clean + "." + safeExtension);
            DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
            if (manager == null) throw new Exception("DownloadManager no disponible");
            manager.enqueue(request);
            Toast.makeText(this, "Descarga iniciada.", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo iniciar la descarga: " + cleanError(e), Toast.LENGTH_LONG).show();
        }
    }

'''
if marker not in s:
    raise SystemExit('multiscreen method marker not found')
s = s.replace(marker, methods + marker, 1)

fav_marker = '''        root.addView(favorite);
    }

    private void addSeriesInfoHeader'''
download_repl = '''        root.addView(favorite);

        Button download = secondaryButton("⬇  DESCARGAR PELÍCULA");
        download.setOnClickListener(v -> downloadVod(finalTitle, url, ext));
        root.addView(download);
    }

    private void addSeriesInfoHeader'''
if fav_marker not in s:
    raise SystemExit('VOD favorite marker not found')
s = s.replace(fav_marker, download_repl, 1)

p.write_text(s)
print('v2 speed test and VOD download patch applied')
