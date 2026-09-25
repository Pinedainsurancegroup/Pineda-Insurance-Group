from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

needle = '''                    if (rememberSession) SecureStore.savePassword(this, prefs, password);
                    else SecureStore.clearPassword(prefs);
                }
                ui.post(this::showDashboard);
'''
repl = '''                    if (rememberSession) SecureStore.savePassword(this, prefs, password);
                    else SecureStore.clearPassword(prefs);
                }
                if (rememberSession) saveCurrentAccountProfile();
                ui.post(this::showDashboard);
'''
if needle not in s:
    raise SystemExit('login success marker not found')
s = s.replace(needle, repl, 1)

needle = '        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);\n'
repl = '''        addDashboardTile(menu, "👤  MI CUENTA", this::showAccount, cols);
        addDashboardTile(menu, "👥  CUENTAS", this::showSavedAccounts, cols);
'''
if needle not in s:
    raise SystemExit('dashboard account marker not found')
s = s.replace(needle, repl, 1)

marker = '    private void showSettings() {\n'
methods = r'''    private String profileId(String serverValue, String userValue) {
        String raw = (serverValue == null ? "" : serverValue) + "|" + (userValue == null ? "" : userValue);
        return Integer.toHexString(raw.hashCode());
    }

    private JSONArray savedAccounts() {
        if (prefs == null) return new JSONArray();
        try {
            return new JSONArray(prefs.getString("saved_accounts", "[]"));
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    private void saveCurrentAccountProfile() {
        if (prefs == null || server.isEmpty() || username.isEmpty() || password.isEmpty()) return;
        JSONArray old = savedAccounts();
        JSONArray out = new JSONArray();
        String id = profileId(server, username);
        try {
            JSONObject current = new JSONObject();
            current.put("id", id);
            current.put("server", server);
            current.put("username", username);
            current.put("updated", System.currentTimeMillis());
            out.put(current);
            for (int i = 0; i < old.length() && out.length() < 12; i++) {
                JSONObject row = old.optJSONObject(i);
                if (row == null || id.equals(row.optString("id", ""))) continue;
                out.put(row);
            }
            prefs.edit().putString("saved_accounts", out.toString()).apply();
            SecureStore.saveSecret(this, prefs, "account_" + id, password);
        } catch (Exception ignored) {}
    }

    private void showSavedAccounts() {
        systemBack = this::showDashboard;
        root = baseScreen();
        addBack(this::showDashboard);
        addTitle("👥 CUENTAS", 27);
        addSubtitle("Cuentas guardadas en este dispositivo");

        Button save = actionButton("GUARDAR CUENTA ACTUAL");
        save.setOnClickListener(v -> {
            saveCurrentAccountProfile();
            Toast.makeText(this, "Cuenta guardada.", Toast.LENGTH_SHORT).show();
            showSavedAccounts();
        });
        root.addView(save);

        JSONArray rows = savedAccounts();
        if (rows.length() == 0) {
            root.addView(cardText("Todavía no hay cuentas guardadas."));
            return;
        }

        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row == null) continue;
            String id = row.optString("id", "");
            String srv = row.optString("server", "");
            String usr = row.optString("username", "");

            LinearLayout line = new LinearLayout(this);
            line.setOrientation(LinearLayout.HORIZONTAL);
            line.setGravity(Gravity.CENTER_VERTICAL);

            Button open = listButton(usr + "\n" + srv);
            LinearLayout.LayoutParams op = new LinearLayout.LayoutParams(0, dp(72), 1f);
            op.setMargins(0, dp(4), dp(5), dp(4));
            open.setLayoutParams(op);
            open.setOnClickListener(v -> switchSavedAccount(id, srv, usr));
            line.addView(open);

            Button remove = secondaryButton("×");
            LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(dp(60), dp(72));
            rp.setMargins(0, dp(4), 0, dp(4));
            remove.setLayoutParams(rp);
            remove.setOnClickListener(v -> {
                removeSavedAccount(id);
                showSavedAccounts();
            });
            line.addView(remove);
            root.addView(line);
        }
    }

    private void switchSavedAccount(String id, String srv, String usr) {
        String secret = SecureStore.loadSecret(this, prefs, "account_" + id);
        if (secret.isEmpty()) {
            Toast.makeText(this, "No se pudo recuperar esta cuenta.", Toast.LENGTH_LONG).show();
            return;
        }
        showLogin();
        serverInput.setText(srv);
        userInput.setText(usr);
        passInput.setText(secret);
        if (rememberCheck != null) rememberCheck.setChecked(true);
        authenticate();
    }

    private void removeSavedAccount(String id) {
        JSONArray old = savedAccounts();
        JSONArray out = new JSONArray();
        for (int i = 0; i < old.length(); i++) {
            JSONObject row = old.optJSONObject(i);
            if (row == null || id.equals(row.optString("id", ""))) continue;
            out.put(row);
        }
        if (prefs != null) prefs.edit().putString("saved_accounts", out.toString()).apply();
        SecureStore.clearSecret(prefs, "account_" + id);
    }

'''
if marker not in s:
    raise SystemExit('settings marker not found')
s = s.replace(marker, methods + marker, 1)

p.write_text(s)
print('v1.4 saved accounts patch applied')
