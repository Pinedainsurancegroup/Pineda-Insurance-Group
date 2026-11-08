from pathlib import Path

p = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = p.read_text()

marker = '    private String profileId(String serverValue, String userValue) {\n'
scope_method = r'''    private String accountScope() {
        String raw = (server == null ? "" : server) + "|" + (username == null ? "" : username);
        return Integer.toHexString(raw.hashCode());
    }

    private String scopedKey(String base) {
        return base + "_" + accountScope();
    }

'''
if marker not in s:
    raise SystemExit('profileId marker not found')
s = s.replace(marker, scope_method + marker, 1)

repls = {
    'prefs.getStringSet("favorites", Collections.emptySet())': 'prefs.getStringSet(scopedKey("favorites"), Collections.emptySet())',
    'prefs.edit().putStringSet("favorites", favs).apply()': 'prefs.edit().putStringSet(scopedKey("favorites"), favs).apply()',
    'prefs.getString("watch_history", "[]")': 'prefs.getString(scopedKey("watch_history"), "[]")',
    'prefs.edit().putString("watch_history", out.toString()).apply()': 'prefs.edit().putString(scopedKey("watch_history"), out.toString()).apply()',
    'prefs.edit().putString("watch_history", rows.toString()).apply()': 'prefs.edit().putString(scopedKey("watch_history"), rows.toString()).apply()',
    'prefs.getString("parental_pin_hash", "")': 'prefs.getString(scopedKey("parental_pin_hash"), "")',
    '.putString("parental_pin_hash", pinHash(pin))': '.putString(scopedKey("parental_pin_hash"), pinHash(pin))',
    '.remove("parental_pin_hash")': '.remove(scopedKey("parental_pin_hash"))',
    'prefs.getBoolean("parental_enabled", false)': 'prefs.getBoolean(scopedKey("parental_enabled"), false)',
    '.putBoolean("parental_enabled", checked)': '.putBoolean(scopedKey("parental_enabled"), checked)',
    '.putBoolean("parental_enabled", true)': '.putBoolean(scopedKey("parental_enabled"), true)',
    '.putBoolean("parental_enabled", false)': '.putBoolean(scopedKey("parental_enabled"), false)',
}
for old, new in repls.items():
    s = s.replace(old, new)

p.write_text(s)
print('v2 account-scoped data patch applied')
