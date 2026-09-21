from pathlib import Path
import re

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

# Extra request codes.
field = '''    private static final int REQ_M3U_FILE = 4101;
    private Uri pendingM3uUri;
'''
if field not in s:
    raise SystemExit('REQ_M3U_FILE field marker not found')
repl = '''    private static final int REQ_M3U_FILE = 4101;
    private static final int REQ_LOCAL_MEDIA = 4102;
    private static final int REQ_OVPN_FILE = 4103;
    private static final int REQ_BACKUP_EXPORT = 4104;
    private static final int REQ_BACKUP_IMPORT = 4105;
    private Uri pendingM3uUri;
'''
s = s.replace(field, repl, 1)

# Expand onActivityResult.
pattern = r'''    @Override
    protected void onActivityResult\(int requestCode, int resultCode, Intent data\) \{
        super\.onActivityResult\(requestCode, resultCode, data\);
        if \(requestCode == REQ_M3U_FILE.*?
        \}
    \}

'''
m = re.search(pattern, s, flags=re.S)
if not m:
    raise SystemExit('onActivityResult block not found')
new_result = r'''    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();

        try {
            if ((data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION) != 0) {
                getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }
        } catch (Exception ignored) {}

        if (requestCode == REQ_M3U_FILE) {
            pendingM3uUri = uri;
            loadM3uFromUri(uri);
        } else if (requestCode == REQ_LOCAL_MEDIA) {
            playLocalUri(uri, this::showLocalMediaScreen);
        } else if (requestCode == REQ_OVPN_FILE) {
            if (prefs != null) prefs.edit().putString("ovpn_uri", uri.toString()).apply();
            openVpnProfile(uri);
        } else if (requestCode == REQ_BACKUP_EXPORT) {
            writeBackupToUri(uri);
        } else if (requestCode == REQ_BACKUP_IMPORT) {
            restoreBackupFromUri(uri);
        }
    }

'''
s = s[:m.start()] + new_result + s[m.end():]

# Extra settings tiles.
settings_marker = '        addCloneSettingsTile(grid, "MAG", "STALKER / MAG", this::showStalkerScreen);\n'
settings_add = '''        addCloneSettingsTile(grid, "MAG", "STALKER / MAG", this::showStalkerScreen);
        addCloneSettingsTile(grid, "▶", "ONE STREAM", this::showOneStreamScreen);
        addCloneSettingsTile(grid, "▣", "MEDIA LOCAL", this::showLocalMediaScreen);
        addCloneSettingsTile(grid, "VPN", "VPN / OVPN", this::showVpnScreen);
        addCloneSettingsTile(grid, "↕", "BACKUP / RESTORE", this::showBackupRestoreScreen);
        addCloneSettingsTile(grid, "!", "ANUNCIOS", this::showAnnouncementsScreen);
        addCloneSettingsTile(grid, "$", "CLIENT AREA", this::showClientAreaScreen);
'''
if settings_marker not in s:
    raise SystemExit('v2.5 settings marker not found')
s = s.replace(settings_marker, settings_add, 1)

# Replace update checker with user-controlled manifest.
update_pattern = r'''    private void showCloneUpdateCheck\(\) \{.*?
    \}

    private void showCloneDeviceMode'''
m = re.search(update_pattern, s, flags=re.S)
if not m:
    raise SystemExit('showCloneUpdateCheck method not found')
update_method = r'''    private void showCloneUpdateCheck() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("Ajustes  |  Comprueba la actualización", this::showSettings);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackgroundResource(R.drawable.clone_panel_bg);
        panel.setPadding(dp(40), dp(28), dp(40), dp(28));
        root.addView(panel);

        TextView heading = label("Versión instalada: v2.5.0");
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextSize(20);
        panel.addView(heading);

        EditText manifest = input("URL de update.json controlado por ti", false);
        if (prefs != null) manifest.setText(prefs.getString("update_manifest_url", ""));
        panel.addView(manifest);

        Button check = cloneGreenButton("COMPROBAR ACTUALIZACIÓN");
        check.setOnClickListener(v -> {
            String url = manifest.getText().toString().trim();
            if (url.isEmpty()) {
                Toast.makeText(this, "Configura primero tu URL de actualización.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit().putString("update_manifest_url", url).apply();
            checkOwnedUpdate(url);
        });
        panel.addView(check);

        panel.addView(cardText("Formato esperado: {\"versionCode\":18,\"versionName\":\"2.6.0\","
                + "\"apkUrl\":\"https://tu-dominio/app.apk\"}. "
                + "La app no depende de un servidor de activación externo."));
    }

    private void checkOwnedUpdate(String manifestUrl) {
        showLoading("Comprobando actualización…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(manifestUrl).openConnection();
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(20000);
                conn.setInstanceFollowRedirects(true);
                conn.setRequestProperty("User-Agent", "PIMFLEXTV/2.5 Android");
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
                JSONObject json = new JSONObject(readAll(conn.getInputStream()));
                long remoteCode = json.optLong("versionCode", 0L);
                String remoteName = json.optString("versionName", "");
                String apkUrl = json.optString("apkUrl", "");

                long localCode;
                if (Build.VERSION.SDK_INT >= 28) {
                    localCode = getPackageManager().getPackageInfo(getPackageName(), 0).getLongVersionCode();
                } else {
                    localCode = getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
                }

                long finalLocalCode = localCode;
                ui.post(() -> showOwnedUpdateResult(finalLocalCode, remoteCode, remoteName, apkUrl));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Actualización", e, this::showCloneUpdateCheck));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void showOwnedUpdateResult(long localCode, long remoteCode, String remoteName, String apkUrl) {
        systemBack = this::showCloneUpdateCheck;
        root = cloneScreen();
        addCloneHeader("ACTUALIZACIÓN", this::showCloneUpdateCheck);

        if (remoteCode > localCode && !apkUrl.isEmpty()) {
            root.addView(cardText("Nueva versión disponible: " +
                    (remoteName.isEmpty() ? String.valueOf(remoteCode) : remoteName)));
            Button download = cloneGreenButton("ABRIR DESCARGA");
            download.setOnClickListener(v -> openBrowserUrl(apkUrl));
            root.addView(download);
        } else {
            root.addView(cardText("PIMFLEX TV está actualizado."));
        }
    }

    private void showCloneDeviceMode'''
s = s[:m.start()] + update_method + s[m.end():]

# Insert utility/control methods before showM3uScreen.
marker = '    private void showM3uScreen() {\n'
if marker not in s:
    raise SystemExit('showM3uScreen marker missing for v2.5')
methods = r'''    private void showOneStreamScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("ONE STREAM", this::showSettings);

        EditText name = input("Nombre del stream", false);
        EditText url = input("URL HTTP / HTTPS", false);
        root.addView(name);
        root.addView(url);

        Button play = cloneGreenButton("REPRODUCIR");
        play.setOnClickListener(v -> {
            String streamUrl = url.getText().toString().trim();
            String title = name.getText().toString().trim();
            if (streamUrl.isEmpty()) {
                Toast.makeText(this, "Introduce una URL.", Toast.LENGTH_SHORT).show();
                return;
            }
            playStream(title.isEmpty() ? "One Stream" : title, streamUrl, null, this::showOneStreamScreen);
        });
        root.addView(play);
    }

    private void showLocalMediaScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("MEDIA LOCAL", this::showSettings);

        root.addView(cardText("Reproduce archivos de video o audio seleccionados desde el almacenamiento del dispositivo."));
        Button pick = cloneGreenButton("SELECCIONAR ARCHIVO");
        pick.setOnClickListener(v -> {
            try {
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("video/*");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, REQ_LOCAL_MEDIA);
            } catch (Exception e) {
                Toast.makeText(this, "No se pudo abrir el selector.", Toast.LENGTH_LONG).show();
            }
        });
        root.addView(pick);
    }

    private void playLocalUri(Uri uri, Runnable back) {
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
            player.setMediaItem(MediaItem.fromUri(uri));
            player.prepare();
            player.play();
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo reproducir el archivo.", Toast.LENGTH_LONG).show();
        }
    }

    private void showVpnScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("VPN / OVPN", this::showSettings);

        root.addView(cardText("Importa un perfil .ovpn y envíalo a una aplicación VPN compatible instalada "
                + "en el dispositivo. PIMFLEX TV no contiene una licencia VPN de terceros."));

        String saved = prefs == null ? "" : prefs.getString("ovpn_uri", "");
        if (!saved.isEmpty()) root.addView(cardText("Perfil guardado:\n" + saved));

        Button importProfile = cloneGreenButton("IMPORTAR PERFIL .OVPN");
        importProfile.setOnClickListener(v -> {
            try {
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                startActivityForResult(intent, REQ_OVPN_FILE);
            } catch (Exception e) {
                Toast.makeText(this, "No se pudo abrir el selector.", Toast.LENGTH_LONG).show();
            }
        });
        root.addView(importProfile);

        if (!saved.isEmpty()) {
            Button open = cloneGrayButton("ABRIR PERFIL VPN");
            open.setOnClickListener(v -> {
                try { openVpnProfile(Uri.parse(saved)); }
                catch (Exception e) { Toast.makeText(this, "Perfil VPN no disponible.", Toast.LENGTH_LONG).show(); }
            });
            root.addView(open);
        }
    }

    private void openVpnProfile(Uri uri) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/x-openvpn-profile");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(intent, "Abrir perfil VPN"));
        } catch (Exception e) {
            Toast.makeText(this,
                    "Instala una aplicación compatible con perfiles OpenVPN para usar este archivo.",
                    Toast.LENGTH_LONG).show();
        }
    }

    private void showBackupRestoreScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("BACKUP / RESTORE", this::showSettings);

        root.addView(cardText("El respaldo incluye ajustes, favoritos, historial y fuentes configuradas. "
                + "No exporta contraseñas cifradas ni claves secretas."));

        Button backup = cloneGreenButton("CREAR RESPALDO");
        backup.setOnClickListener(v -> {
            try {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.putExtra(Intent.EXTRA_TITLE, "PIMFLEX_TV_backup.json");
                startActivityForResult(intent, REQ_BACKUP_EXPORT);
            } catch (Exception e) {
                Toast.makeText(this, "No se pudo abrir el selector.", Toast.LENGTH_LONG).show();
            }
        });
        root.addView(backup);

        Button restore = cloneGrayButton("RESTAURAR RESPALDO");
        restore.setOnClickListener(v -> {
            try {
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivityForResult(intent, REQ_BACKUP_IMPORT);
            } catch (Exception e) {
                Toast.makeText(this, "No se pudo abrir el selector.", Toast.LENGTH_LONG).show();
            }
        });
        root.addView(restore);
    }

    private JSONObject createBackupJson() throws Exception {
        JSONObject rootJson = new JSONObject();
        rootJson.put("format", "PIMFLEX_BACKUP_1");
        rootJson.put("created_at", System.currentTimeMillis());
        JSONObject values = new JSONObject();

        if (prefs != null) {
            for (java.util.Map.Entry<String, ?> entry : prefs.getAll().entrySet()) {
                String key = entry.getKey();
                String low = key.toLowerCase(Locale.ROOT);
                if (low.contains("password") || low.contains("secret") || low.contains("cipher") ||
                        low.contains("_iv") || low.contains("keystore")) {
                    continue;
                }
                Object value = entry.getValue();
                if (value instanceof java.util.Set) {
                    JSONArray arr = new JSONArray();
                    for (Object item : (java.util.Set<?>) value) arr.put(String.valueOf(item));
                    JSONObject wrapped = new JSONObject();
                    wrapped.put("_type", "string_set");
                    wrapped.put("value", arr);
                    values.put(key, wrapped);
                } else if (value instanceof String || value instanceof Boolean ||
                        value instanceof Integer || value instanceof Long || value instanceof Float) {
                    values.put(key, value);
                }
            }
        }
        rootJson.put("prefs", values);
        return rootJson;
    }

    private void writeBackupToUri(Uri uri) {
        io.execute(() -> {
            try (java.io.OutputStream out = getContentResolver().openOutputStream(uri)) {
                if (out == null) throw new Exception("No se pudo abrir el archivo.");
                byte[] bytes = createBackupJson().toString(2).getBytes(StandardCharsets.UTF_8);
                out.write(bytes);
                out.flush();
                ui.post(() -> Toast.makeText(this, "Respaldo creado.", Toast.LENGTH_LONG).show());
            } catch (Exception e) {
                ui.post(() -> Toast.makeText(this, "Error de respaldo: " + cleanError(e), Toast.LENGTH_LONG).show());
            }
        });
    }

    private void restoreBackupFromUri(Uri uri) {
        showLoading("Restaurando respaldo…");
        io.execute(() -> {
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                JSONObject rootJson = new JSONObject(readAll(in));
                if (!"PIMFLEX_BACKUP_1".equals(rootJson.optString("format", ""))) {
                    throw new Exception("Formato de respaldo no reconocido.");
                }
                JSONObject values = rootJson.optJSONObject("prefs");
                if (values == null || prefs == null) throw new Exception("Respaldo vacío.");

                android.content.SharedPreferences.Editor editor = prefs.edit();
                Iterator<String> keys = values.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    Object value = values.opt(key);
                    if (value instanceof JSONObject &&
                            "string_set".equals(((JSONObject) value).optString("_type", ""))) {
                        JSONArray arr = ((JSONObject) value).optJSONArray("value");
                        java.util.HashSet<String> set = new java.util.HashSet<>();
                        if (arr != null) for (int i = 0; i < arr.length(); i++) set.add(arr.optString(i));
                        editor.putStringSet(key, set);
                    } else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
                    else if (value instanceof Integer) editor.putInt(key, (Integer) value);
                    else if (value instanceof Long) editor.putLong(key, (Long) value);
                    else if (value instanceof Double) {
                        double d = (Double) value;
                        if (d == Math.rint(d)) editor.putLong(key, (long) d);
                        else editor.putFloat(key, (float) d);
                    } else if (value != null && value != JSONObject.NULL) editor.putString(key, String.valueOf(value));
                }
                editor.apply();
                ui.post(() -> {
                    Toast.makeText(this, "Respaldo restaurado.", Toast.LENGTH_LONG).show();
                    showSettings();
                });
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Restaurar respaldo", e, this::showBackupRestoreScreen));
            }
        });
    }

    private void showAnnouncementsScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("ANUNCIOS", this::showSettings);

        EditText url = input("URL JSON de anuncios controlada por ti", false);
        if (prefs != null) url.setText(prefs.getString("announcements_url", ""));
        root.addView(url);

        Button load = cloneGreenButton("CARGAR ANUNCIOS");
        load.setOnClickListener(v -> {
            String value = url.getText().toString().trim();
            if (value.isEmpty()) {
                Toast.makeText(this, "Configura una URL.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit().putString("announcements_url", value).apply();
            loadAnnouncements(value);
        });
        root.addView(load);

        root.addView(cardText("El feed puede ser un array JSON o un objeto con la propiedad announcements. "
                + "Campos sugeridos: title, message y date."));
    }

    private void loadAnnouncements(String url) {
        showLoading("Cargando anuncios…");
        io.execute(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(20000);
                conn.setInstanceFollowRedirects(true);
                int code = conn.getResponseCode();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
                String body = readAll(conn.getInputStream()).trim();
                JSONArray arr;
                if (body.startsWith("[")) arr = new JSONArray(body);
                else {
                    JSONObject obj = new JSONObject(body);
                    arr = obj.optJSONArray("announcements");
                    if (arr == null) arr = new JSONArray();
                }
                JSONArray finalArr = arr;
                ui.post(() -> showAnnouncementsList(finalArr));
            } catch (Exception e) {
                ui.post(() -> showErrorScreen("Anuncios", e, this::showAnnouncementsScreen));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private void showAnnouncementsList(JSONArray arr) {
        systemBack = this::showAnnouncementsScreen;
        root = cloneScreen();
        addCloneHeader("ANUNCIOS", this::showAnnouncementsScreen);
        if (arr.length() == 0) {
            root.addView(cardText("No hay anuncios."));
            return;
        }
        for (int i = 0; i < arr.length(); i++) {
            JSONObject row = arr.optJSONObject(i);
            if (row == null) continue;
            String title = row.optString("title", "Anuncio");
            String message = row.optString("message", row.optString("body", ""));
            String date = row.optString("date", "");
            root.addView(cardText(title + (date.isEmpty() ? "" : "\n" + date) +
                    (message.isEmpty() ? "" : "\n\n" + message)));
        }
    }

    private void showClientAreaScreen() {
        systemBack = this::showSettings;
        root = cloneScreen();
        addCloneHeader("CLIENT AREA / BILLING", this::showSettings);

        EditText url = input("URL de tu portal de clientes / WHMCS", false);
        if (prefs != null) url.setText(prefs.getString("client_area_url", ""));
        root.addView(url);

        Button open = cloneGreenButton("ABRIR CLIENT AREA");
        open.setOnClickListener(v -> {
            String value = url.getText().toString().trim();
            if (value.isEmpty()) {
                Toast.makeText(this, "Configura la URL de tu portal.", Toast.LENGTH_SHORT).show();
                return;
            }
            if (prefs != null) prefs.edit().putString("client_area_url", value).apply();
            openBrowserUrl(value);
        });
        root.addView(open);

        root.addView(cardText("Este acceso queda bajo tu propio portal. No se incluyen credenciales WHMCS "
                + "ni licencias de terceros dentro del APK."));
    }

    private void openBrowserUrl(String value) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(value));
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, "No se pudo abrir el enlace.", Toast.LENGTH_LONG).show();
        }
    }

'''
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v2.5 user-controlled utilities patch applied')
