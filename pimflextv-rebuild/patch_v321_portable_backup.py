"""Add a bounded portable backup flow after the validated v3.2 reference patch."""
from pathlib import Path
import re
p=Path('app/src/main/java/com/pimflextv/next/MainActivity.java')
s=p.read_text()
if 'new ReferenceHomeView(' not in s or 'PortableBackupScreen' in s:
    raise SystemExit('Expected fresh fully patched v3.2 source')

def method(name, body):
    global s
    pattern=r'    private [^\n]+\b'+re.escape(name)+r'\([^\n]*\)[^{\n]*\{.*?(?=\n    (?:private|public|protected) )'
    s,n=re.subn(pattern, lambda m:body.rstrip()+'\n',s,count=1,flags=re.S)
    if n!=1: raise SystemExit('Method marker missing: '+name)

method('showBackupRestoreScreen', '''    private void showBackupRestoreScreen() {
        systemBack = accountInfo == null ? this::showLogin : this::showSettings;
        root = cloneScreen();
        addCloneHeader("RESPALDO Y TRASLADO AL TV", systemBack);
        portableBackup().render(root);
    }

    private PortableBackupScreen portableBackup() {
        if (portableBackupScreen == null) {
            portableBackupScreen = new PortableBackupScreen(this, prefs, io, this::showImportedBackupLogin);
        }
        return portableBackupScreen;
    }

    private void showImportedBackupLogin() {
        showLogin();
        JSONArray rows = savedAccounts();
        if (rows.length() > 0) {
            JSONObject row = rows.optJSONObject(0);
            if (row != null) {
                serverInput.setText(row.optString("server", ""));
                userInput.setText(row.optString("username", ""));
                passInput.setText(SecureStore.loadSecret(this, prefs, "account_" + row.optString("id", "")));
                rememberCheck.setChecked(true);
            }
        }
        statusText.setText("Selecciona tu cuenta o completa sus datos y pulsa ENTRAR.");
    }
''')
method('createBackupJson', '')
method('writeBackupToUri', '''    private void writeBackupToUri(Uri uri) {
        portableBackup().exportTo(uri);
    }
''')
method('restoreBackupFromUri', '''    private void restoreBackupFromUri(Uri uri) {
        portableBackup().importFrom(uri);
    }
''')
method('showCloneLoginOnTv', '''    private void showCloneLoginOnTv() {
        showBackupRestoreScreen();
    }
''')
marker='    private SharedPreferences prefs;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\n    private PortableBackupScreen portableBackupScreen;')
marker='        root.addView(login);\n'
assert s.count(marker)==1
s=s.replace(marker,marker+'''
        Button restore = secondaryButton("IMPORTAR RESPALDO / TRASLADAR CUENTAS");
        restore.setOnClickListener(v -> showBackupRestoreScreen());
        root.addView(restore);
        if (savedAccounts().length() > 0) {
            Button accounts = secondaryButton("ELEGIR CUENTA GUARDADA");
            accounts.setOnClickListener(v -> showSavedAccounts());
            root.addView(accounts);
        }
''')
marker='''            Toast.makeText(this, "No se pudo recuperar esta cuenta.", Toast.LENGTH_LONG).show();
            return;'''
assert s.count(marker)==1
s=s.replace(marker,'''            showLogin();
            serverInput.setText(srv);
            userInput.setText(usr);
            rememberCheck.setChecked(true);
            statusText.setText("Escribe la contraseña de esta cuenta y pulsa ENTRAR.");
            passInput.requestFocus();
            return;''')
s=s.replace('addCloneSettingsTile(grid, "▣", "CUENTAS EN ESTE TV", this::showCloneLoginOnTv);',
            'addCloneSettingsTile(grid, "▣", "TRASLADAR CUENTAS AL TV", this::showCloneLoginOnTv);')
p.write_text(s)

secure=Path('app/src/main/java/com/pimflextv/next/SecureStore.java')
t=secure.read_text()
marker='    private static String safeSlot(String slot) {'
assert t.count(marker)==1
t=t.replace(marker,'''    // Used by portable restore to stage secrets in the same preferences transaction.
    static void stagePortableSecret(SharedPreferences.Editor editor, String slot, String value) throws Exception {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) throw new Exception("Android 6 o superior requerido.");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] clear = value.getBytes(StandardCharsets.UTF_8);
        try {
            byte[] encrypted = cipher.doFinal(clear);
            editor.putString(secretCipherKey(slot), Base64.encodeToString(encrypted, Base64.NO_WRAP));
            editor.putString(secretIvKey(slot), Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP));
        } finally { java.util.Arrays.fill(clear, (byte) 0); }
    }

'''+marker)
secure.write_text(t)
gradle=Path('app/build.gradle')
g=gradle.read_text().replace('versionCode 24','versionCode 25').replace("versionName '3.2.0'","versionName '3.2.1'")
marker='    compileOptions {'
assert g.count(marker)==1
g=g.replace(marker,'''    buildTypes {
        preview {
            initWith release
            applicationIdSuffix '.preview'
            versionNameSuffix '-preview.1'
            signingConfig null
            matchingFallbacks = ['release']
        }
    }

'''+marker)
g += "\ndependencies {\n    testImplementation 'org.robolectric:robolectric:4.14.1'\n    testImplementation 'junit:junit:4.13.2'\n    testImplementation 'org.json:json:20240303'\n}\n"
gradle.write_text(g)
manifest=Path('app/src/preview/AndroidManifest.xml')
manifest.parent.mkdir(parents=True,exist_ok=True)
manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">
    <application android:label="PIMFLEX TV Avance" tools:replace="android:label" />
</manifest>
''')
print('Portable backups and TV file transfer applied. Preview release remains isolated from stable and reference.1.')
