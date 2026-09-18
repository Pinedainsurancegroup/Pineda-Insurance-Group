from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

s = s.replace('import android.app.Activity;\n', 'import android.app.Activity;\nimport android.app.AlertDialog;\n')
s = s.replace('import java.util.Locale;\n', 'import java.util.Locale;\nimport java.security.MessageDigest;\n')

field = '    private Runnable progressRunnable;\n'
if field not in s:
    raise SystemExit('progress field not found')
s = s.replace(field, field + '    private long parentalUnlockedUntil = 0L;\n', 1)

# Gate category access
old = '            b.setOnClickListener(v -> loadItems(type, id, name));\n'
if old not in s:
    raise SystemExit('category click not found')
s = s.replace(old, '            b.setOnClickListener(v -> runWithParentalGate(name, () -> loadItems(type, id, name)));\n', 1)

# Gate Live items
old = '''                b.setOnClickListener(v -> playStream(name, ts, hls,
                        () -> showItems(type, categoryId, categoryName, arr)));
'''
if old not in s:
    raise SystemExit('live click not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        playStream(name, ts, hls,
                                () -> showItems(type, categoryId, categoryName, arr))));
''', 1)

# Gate visual cards after content patch
old = '''                card.setOnClickListener(v -> loadVodDetails(id, name, ext, artFinal,
                        () -> showItems(type, categoryId, categoryName, arr)));
'''
if old not in s:
    raise SystemExit('vod detail card not found')
s = s.replace(old, '''                card.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadVodDetails(id, name, ext, artFinal,
                                () -> showItems(type, categoryId, categoryName, arr))));
''', 1)

old = '                card.setOnClickListener(v -> loadSeriesEpisodes(id, name, categoryId, categoryName, arr));\n'
if old not in s:
    raise SystemExit('series card not found')
s = s.replace(old, '''                card.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadSeriesEpisodes(id, name, categoryId, categoryName, arr)));
''', 1)

# Gate tracked series episodes
old = '''                b.setOnClickListener(v ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showSeriesEpisodes(seriesName, info, categoryId, categoryName, parentList)));
'''
if old not in s:
    raise SystemExit('tracked series episode not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(title, () ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showSeriesEpisodes(seriesName, info, categoryId, categoryName, parentList))));
''', 1)

old = '''                b.setOnClickListener(v ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showFavoriteSeriesEpisodes(seriesName, info, favorites)));
'''
if old not in s:
    raise SystemExit('tracked favorite episode not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(title, () ->
                        startTrackedPlayback("series_episode", id, title, ext, "", url,
                                () -> showFavoriteSeriesEpisodes(seriesName, info, favorites))));
''', 1)

# Gate favorite rows
old = '''                b.setOnClickListener(v -> playStream(name, ts, hls, () -> showFavorites(arr)));
'''
if old not in s:
    raise SystemExit('favorite live not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        playStream(name, ts, hls, () -> showFavorites(arr))));
''', 1)

old = '''                b.setOnClickListener(v -> loadVodDetails(id, name, ext, art, () -> showFavorites(arr)));
'''
if old not in s:
    raise SystemExit('favorite vod detail not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadVodDetails(id, name, ext, art, () -> showFavorites(arr))));
''', 1)

old = '                b.setOnClickListener(v -> loadFavoriteSeriesEpisodes(id, name, arr));\n'
if old not in s:
    raise SystemExit('favorite series not found')
s = s.replace(old, '''                b.setOnClickListener(v -> runWithParentalGate(name, () ->
                        loadFavoriteSeriesEpisodes(id, name, arr)));
''', 1)

# Gate recent/continue play
old = '''            play.setOnClickListener(v -> {
                String url = "vod".equals(type)
                        ? server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext
                        : server + "/series/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                startTrackedPlayback(type, id, title, ext, art, url, () -> showWatchHistory(onlyContinue));
            });
'''
if old not in s:
    raise SystemExit('history play not found')
s = s.replace(old, '''            play.setOnClickListener(v -> runWithParentalGate(title, () -> {
                String url = "vod".equals(type)
                        ? server + "/movie/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext
                        : server + "/series/" + encPath(username) + "/" + encPath(password) + "/" + id + "." + ext;
                startTrackedPlayback(type, id, title, ext, art, url, () -> showWatchHistory(onlyContinue));
            }));
''', 1)

# Add settings entry in My Account
account = '        root.addView(cardText("Servidor: " + server));\n'
if account not in s:
    raise SystemExit('account marker not found')
s = s.replace(account, account + '''
        Button parental = secondaryButton("🔒  CONTROL PARENTAL");
        parental.setOnClickListener(v -> showParentalSettings());
        root.addView(parental);
''', 1)

marker = '    private String humanTime(long ms) {\n'
parental = r'''    private void showParentalSettings() {
        systemBack = this::showAccount;
        root = baseScreen();
        addBack(this::showAccount);
        addTitle("🔒 CONTROL PARENTAL", 27);

        boolean hasPin = prefs != null && !prefs.getString("parental_pin_hash", "").isEmpty();
        boolean enabled = hasPin && prefs.getBoolean("parental_enabled", false);
        root.addView(cardText(hasPin
                ? (enabled ? "Protección activa para categorías y títulos restringidos." : "PIN configurado. La protección está desactivada.")
                : "Configura un PIN de 4 dígitos para proteger categorías restringidas."));

        CheckBox toggle = new CheckBox(this);
        toggle.setText("Activar control parental");
        toggle.setTextColor(Color.WHITE);
        toggle.setChecked(enabled);
        toggle.setEnabled(hasPin);
        toggle.setPadding(dp(4), dp(10), dp(4), dp(10));
        toggle.setOnCheckedChangeListener((buttonView, checked) -> {
            if (prefs != null) prefs.edit().putBoolean("parental_enabled", checked).apply();
        });
        root.addView(toggle);

        Button pin = actionButton(hasPin ? "CAMBIAR PIN" : "CREAR PIN");
        pin.setOnClickListener(v -> promptSetParentalPin(this::showParentalSettings));
        root.addView(pin);

        if (hasPin) {
            Button remove = secondaryButton("ELIMINAR PIN Y DESACTIVAR");
            remove.setOnClickListener(v -> promptParentalPin(() -> {
                if (prefs != null) prefs.edit()
                        .remove("parental_pin_hash")
                        .putBoolean("parental_enabled", false)
                        .apply();
                parentalUnlockedUntil = 0L;
                showParentalSettings();
            }));
            root.addView(remove);
        }
    }

    private void promptSetParentalPin(Runnable done) {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        input.setHint("PIN de 4 dígitos");
        input.setSingleLine(true);
        input.setPadding(dp(20), dp(10), dp(20), dp(10));

        new AlertDialog.Builder(this)
                .setTitle("Configurar PIN")
                .setView(input)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Guardar", (dialog, which) -> {
                    String pin = input.getText().toString().trim();
                    if (!pin.matches("\\d{4}")) {
                        Toast.makeText(this, "El PIN debe tener exactamente 4 dígitos.", Toast.LENGTH_LONG).show();
                        return;
                    }
                    if (prefs != null) prefs.edit()
                            .putString("parental_pin_hash", pinHash(pin))
                            .putBoolean("parental_enabled", true)
                            .apply();
                    parentalUnlockedUntil = System.currentTimeMillis() + 5 * 60 * 1000L;
                    done.run();
                }).show();
    }

    private void promptParentalPin(Runnable success) {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        input.setHint("PIN");
        input.setSingleLine(true);
        input.setPadding(dp(20), dp(10), dp(20), dp(10));

        new AlertDialog.Builder(this)
                .setTitle("Control parental")
                .setMessage("Introduce el PIN de 4 dígitos.")
                .setView(input)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Desbloquear", (dialog, which) -> {
                    String stored = prefs == null ? "" : prefs.getString("parental_pin_hash", "");
                    if (!stored.isEmpty() && stored.equals(pinHash(input.getText().toString().trim()))) {
                        parentalUnlockedUntil = System.currentTimeMillis() + 5 * 60 * 1000L;
                        success.run();
                    } else {
                        Toast.makeText(this, "PIN incorrecto.", Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private void runWithParentalGate(String label, Runnable action) {
        if (!parentalProtectionEnabled() || !isRestrictedLabel(label)) {
            action.run();
            return;
        }
        if (System.currentTimeMillis() < parentalUnlockedUntil) {
            action.run();
            return;
        }
        promptParentalPin(action);
    }

    private boolean parentalProtectionEnabled() {
        return prefs != null
                && prefs.getBoolean("parental_enabled", false)
                && !prefs.getString("parental_pin_hash", "").isEmpty();
    }

    private boolean isRestrictedLabel(String value) {
        if (value == null) return false;
        String text = value.toLowerCase(Locale.ROOT);
        return text.contains("adult") || text.contains("xxx") || text.contains("18+")
                || text.contains("restricted") || text.contains("para adultos");
    }

    private String pinHash(String pin) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(("PIMFLEX-TV-PARENTAL|" + pin).getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (byte b : bytes) out.append(String.format(Locale.US, "%02x", b & 0xff));
            return out.toString();
        } catch (Exception e) {
            return "";
        }
    }

'''
if marker not in s:
    raise SystemExit('humanTime marker not found')
s = s.replace(marker, parental + marker, 1)

p.write_text(s)
print('Parental patch applied')
