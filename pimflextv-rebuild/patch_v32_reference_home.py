"""Apply only presentation changes after the stable 3.1 patch chain.

Fail closed on an unexpected baseline. Do not alter playback or production builds.
"""
from pathlib import Path
import re

path = Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s = path.read_text()
if 'new ReferenceHomeView(' in s:
    raise SystemExit('Reference patch already applied; use a fresh source checkout.')

def replace_method(text, name, new):
    pattern = r'    private [^\n]+\b' + re.escape(name) + r'\([^\n]*\) \{.*?(?=\n    (?:private|public|protected) )'
    updated, count = re.subn(pattern, new.rstrip()+'\n', text, count=1, flags=re.S)
    if count != 1: raise SystemExit('Missing stable method: '+name)
    return updated

s = replace_method(s, 'showDashboard', '''    private void showDashboard() {
        systemBack = this::showLogin;
        root = cloneScreen();
        boolean use24 = prefs != null && prefs.getBoolean("clone_clock_24", false);
        String expiry = accountInfo == null ? "" : formatEpoch(accountInfo.optString("exp_date", ""));
        String[] updates = {referenceCategoryUpdate("live"), referenceCategoryUpdate("vod"), referenceCategoryUpdate("series")};
        root.addView(new ReferenceHomeView(this, use24, username, expiry, updates, destination -> {
            switch (destination) {
                case "live": loadCategories("live"); break;
                case "vod": loadCategories("vod"); break;
                case "series": loadCategories("series"); break;
                case "search": loadGlobalSearch(); break;
                case "recordings": showRecordingCenter(); break;
                case "downloads": showDownloadsLibrary(); break;
                case "radio": loadRadioStreams(); break;
                case "favorites": loadFavorites(); break;
                case "epg": loadEpgGrid(); break;
                case "multiscreen": loadMultiScreenChannels(); break;
                case "catchup": loadCatchupChannels(); break;
                case "settings": showSettings(); break;
                case "accounts": showSavedAccounts(); break;
                case "account": showAccount(); break;
                case "local": showLocalMediaScreen(); break;
                case "m3u": showM3uScreen(); break;
                case "announcements": showAnnouncementsScreen(); break;
                case "vpn": showVpnScreen(); break;
                case "backup": showBackupRestoreScreen(); break;
                case "client": showClientAreaScreen(); break;
                case "status": showSystemStatusScreen(); break;
            }
        }));
        maybeRunAutomaticRefresh();
    }

    private String referenceCategoryUpdate(String type) {
        long loaded = prefs == null ? 0 : prefs.getLong(scopedKey("reference_categories_" + type), 0);
        if (loaded <= 0) return "Categorías sin consultar";
        boolean use24 = prefs != null && prefs.getBoolean("clone_clock_24", false);
        String pattern = use24 ? "dd/MM HH:mm" : "dd/MM h:mm a";
        return "Categorías: " + new java.text.SimpleDateFormat(pattern, Locale.getDefault()).format(new Date(loaded));
    }
''')

marker = '                ui.post(() -> showCategories(type, arr));'
if s.count(marker) != 1: raise SystemExit('Unexpected category load marker')
s = s.replace(marker, '''                ui.post(() -> {
                    if (prefs != null) prefs.edit().putLong(scopedKey("reference_categories_" + type), System.currentTimeMillis()).apply();
                    showCategories(type, arr);
                });''', 1)

# Header clock is live and follows the user's saved 12/24-hour preference.
start = '        String timeText = DateFormat.getTimeInstance(DateFormat.SHORT, Locale.getDefault()).format(new Date());'
end = '        clock.addView(date);'
a=s.index(start); b=s.index(end,a)+len(end)
s=s[:a]+'''        boolean use24 = prefs != null && prefs.getBoolean("clone_clock_24", false);
        android.widget.TextClock time = new android.widget.TextClock(this);
        time.setFormat12Hour(use24 ? "HH:mm" : "h:mm a");
        time.setFormat24Hour(use24 ? "HH:mm" : "h:mm a");
        time.setTextColor(Color.WHITE);
        time.setTextSize(18);
        time.setPadding(0, 0, dp(12), 0);
        clock.addView(time);
        android.widget.TextClock date = new android.widget.TextClock(this);
        date.setFormat12Hour("EEE, d MMM");
        date.setFormat24Hour("EEE, d MMM");
        date.setTextSize(12);
        date.setTextColor(Color.LTGRAY);
        clock.addView(date);'''+s[b:]
s=s.replace('header.addView(clock, new LinearLayout.LayoutParams(dp(360), dp(70)));',
            'header.addView(clock, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(70)));')
s=s.replace('TextView footer = label("Última actualización: ahora     ↻");','TextView footer = label("Abrir catálogo");')
# Accurately label integrations that have different behavior from the reference.
s=s.replace('"Switch Device Mode"', '"MODO DE DISPOSITIVO"').replace('"Subtitles"', '"SUBTÍTULOS"')
s=s.replace('"Log in on TV"', '"CUENTAS EN ESTE TV"').replace('"VPN / OVPN"', '"VPN EXTERNA / OVPN"')
s=s.replace('"CLIENT AREA"', '"PORTAL DE CLIENTES"').replace('"BACKUP / RESTORE"', '"RESPALDO / RESTAURAR"')
path.write_text(s)

gradle = Path('app/build.gradle')
g = gradle.read_text()
g=g.replace("versionName '3.1.0'", "versionName '3.2.0'").replace('versionCode 23', 'versionCode 24')
marker='        debug {\n'
if g.count(marker)!=1: raise SystemExit('Unexpected debug configuration')
g=g.replace(marker, marker+"            applicationIdSuffix '.reference'\n            versionNameSuffix '-reference.1'\n",1)
gradle.write_text(g)

# The test app installs alongside the stable app. Release manifest is untouched.
debug=Path('app/src/debug/AndroidManifest.xml'); debug.parent.mkdir(parents=True,exist_ok=True)
debug.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">
    <application android:label="PIMFLEX TV Prueba" tools:replace="android:label" />
</manifest>
''')
print('Reference 4.0.2 presentation applied; playback methods unchanged.')
