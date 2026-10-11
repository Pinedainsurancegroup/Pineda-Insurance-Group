package com.pimflextv.next;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.text.InputFilter;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;

/** SAF file transfer works without an account, network, or storage permission. */
final class PortableBackupScreen {
    private final Activity activity;
    private final SharedPreferences prefs;
    private final ExecutorService io;
    private final Runnable afterRestore;
    private boolean busy;
    private TextView status;

    PortableBackupScreen(Activity a, SharedPreferences p, ExecutorService executor, Runnable restored) {
        activity=a; prefs=p; io=executor; afterRestore=restored;
    }

    void render(LinearLayout root) {
        text(root, "RESPALDO PROTEGIDO", 23);
        text(root, "Guarda cuentas, favoritos, historial, fuentes y ajustes en un archivo con contraseña. "
                + "Las contraseñas de las cuentas solo se incluyen si lo eliges al exportar.", 17);
        button(root, "CREAR ARCHIVO PROTEGIDO", () -> pick(true));
        button(root, "IMPORTAR RESPALDO", () -> pick(false));
        text(root, "PARA PASAR TUS CUENTAS AL TV", 20);
        text(root, "1. Crea el respaldo e incluye las contraseñas de tus cuentas.\n"
                + "2. Copia el archivo .pimbackup al TV, por ejemplo mediante USB.\n"
                + "3. Abre esta pantalla en el TV e importa el archivo con su contraseña.\n"
                + "4. Revisa los datos y confirma. Después pulsa ENTRAR para conectar.", 17);
        text(root, "Necesitas un selector de archivos en el equipo. No se copian videos descargados, grabaciones, "
                + "archivos de subtítulos, perfiles VPN ni el PIN parental. Configura esos elementos en el destino. "
                + "Guarda la contraseña del respaldo: no se puede recuperar.", 15);
        text(root, "Puedes importar los respaldos JSON anteriores. Si les faltan las contraseñas de las cuentas, "
                + "deberás escribirlas al iniciar sesión. No compartas esos archivos antiguos sin protección.", 15);
        status = text(root, "Listo para crear o importar un respaldo.", 16);
    }

    private boolean alive() { return !activity.isFinishing() && !activity.isDestroyed(); }
    private void ui(Runnable work) { activity.runOnUiThread(() -> { if (alive()) work.run(); }); }
    private void state(String value) { if (status != null) status.setText(value); }
    private boolean begin(String message) {
        if (busy) { state("Espera a que termine la operación actual."); return false; }
        busy=true; state(message); return true;
    }
    private void error(String message) {
        busy=false; state(message);
        new AlertDialog.Builder(activity).setTitle("Respaldo").setMessage(message).setPositiveButton("Aceptar", null).show();
    }

    void pick(boolean exporting) {
        if (busy) return;
        try {
            Intent intent = new Intent(exporting ? Intent.ACTION_CREATE_DOCUMENT : Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType(exporting ? "application/octet-stream" : "*/*");
            if (exporting) intent.putExtra(Intent.EXTRA_TITLE, "PIMFLEX_" + new java.text.SimpleDateFormat("yyyyMMdd_HHmmss", java.util.Locale.ROOT).format(new java.util.Date()) + ".pimbackup");
            else intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            activity.startActivityForResult(intent, exporting ? 4104 : 4105);
        } catch (Exception e) { error("Este equipo no tiene un selector de archivos compatible. Instala o habilita uno e inténtalo de nuevo."); }
    }

    void exportTo(Uri uri) {
        if (!alive() || busy) return;
        askPassword(true, (password, secrets) -> {
            if (!begin("Cifrando respaldo…")) { Arrays.fill(password, '\0'); return; }
            io.execute(() -> {
                byte[] clear=null, encrypted=null;
                try {
                    JSONObject payload = PortableBackupStore.capture(activity, prefs, secrets);
                    int count = PortableBackupData.parse(payload).secrets;
                    clear=payload.toString().getBytes(StandardCharsets.UTF_8);
                    encrypted=PortableBackupCrypto.encrypt(clear, password);
                    if (!alive() || Thread.currentThread().isInterrupted()) return;
                    try (OutputStream out=activity.getContentResolver().openOutputStream(uri, "wt")) {
                        if (out == null) throw new Exception("No se pudo abrir el destino.");
                        out.write(encrypted); out.flush();
                    }
                    ui(() -> {
                        busy=false;
                        String message="Respaldo protegido creado. Contraseñas de cuentas incluidas: " + count + ".";
                        state(message);
                        new AlertDialog.Builder(activity).setTitle("Respaldo creado").setMessage(message)
                                .setPositiveButton("Aceptar", null).show();
                    });
                } catch (Exception e) { ui(() -> error("No se completó el respaldo. Comprueba el espacio disponible y los datos guardados.")); }
                finally {
                    Arrays.fill(password, '\0');
                    if (clear != null) Arrays.fill(clear, (byte)0);
                    if (encrypted != null) Arrays.fill(encrypted, (byte)0);
                }
            });
        });
    }

    void importFrom(Uri uri) {
        if (!alive() || !begin("Leyendo respaldo…")) return;
        io.execute(() -> {
            try (InputStream in=activity.getContentResolver().openInputStream(uri)) {
                byte[] bytes=PortableBackupCrypto.readBounded(in);
                if (PortableBackupCrypto.isEncrypted(bytes)) {
                    ui(() -> {
                        busy=false;
                        askPassword(false, (password, unused) -> decrypt(bytes, password), () -> Arrays.fill(bytes, (byte)0));
                    });
                } else {
                    try {
                        JSONObject root=PortableBackupData.readJson(new String(bytes, StandardCharsets.UTF_8));
                        // A plaintext file must never masquerade as a protected portable backup.
                        if (!"PIMFLEX_BACKUP_1".equals(root.optString("format"))) throw new Exception("Formato no reconocido.");
                        PortableBackupData.Parsed parsed=PortableBackupData.parse(root);
                        ui(() -> preview(parsed));
                    } finally { Arrays.fill(bytes, (byte)0); }
                }
            } catch (Exception e) { ui(() -> error("No se pudo leer el respaldo. Usa un archivo .pimbackup o un respaldo JSON anterior válido (máximo 4 MB).")); }
        });
    }

    private void decrypt(byte[] bytes, char[] password) {
        if (!begin("Abriendo respaldo protegido…")) { Arrays.fill(password, '\0'); Arrays.fill(bytes, (byte)0); return; }
        io.execute(() -> {
            byte[] clear=null;
            try {
                clear=PortableBackupCrypto.decrypt(bytes, password);
                PortableBackupData.Parsed parsed=PortableBackupData.parse(PortableBackupData.readJson(new String(clear, StandardCharsets.UTF_8)));
                ui(() -> preview(parsed));
            } catch (Exception e) { ui(() -> error("Contraseña incorrecta o respaldo dañado/incompatible. No se cambió ningún dato.")); }
            finally {
                Arrays.fill(bytes, (byte)0); Arrays.fill(password, '\0');
                if (clear != null) Arrays.fill(clear, (byte)0);
            }
        });
    }

    private void preview(PortableBackupData.Parsed data) {
        busy=false;
        String details="Cuentas en el archivo: " + data.accounts.length() + "\n"
                + "Con contraseña guardada: " + data.secrets + "\n"
                + "Grupos de ajustes y datos compatibles: " + data.prefs.size() + "\n\n"
                + "Se añaden las cuentas que falten y se combinan los favoritos. Las cuentas, contraseñas, "
                + "ajustes e historiales que ya existan se conservan. No se conectará a ningún servidor hasta que tú lo elijas."
                + (data.legacy ? "\n\nEste respaldo antiguo no incluye las contraseñas de las cuentas." : "")
                + (Build.VERSION.SDK_INT < 23 && data.secrets > 0 ? "\n\nEste equipo necesita Android 6 o superior para guardar las contraseñas incluidas." : "");
        new AlertDialog.Builder(activity).setTitle("Revisar antes de importar").setMessage(details)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("AÑADIR DATOS", (d,w) -> {
                    if (!begin("Guardando datos…")) return;
                    io.execute(() -> {
                        try {
                            if (!alive()) return;
                            int added=PortableBackupStore.restore(activity, prefs, data);
                            ui(() -> {
                                busy=false;
                                new AlertDialog.Builder(activity).setTitle("Importación terminada")
                                        .setMessage("Cuentas nuevas: " + added + ". Pulsa Continuar y luego ENTRAR para validar tu cuenta.")
                                        .setPositiveButton("Continuar", (x,y) -> afterRestore.run()).show();
                                state("Importación terminada. Cuentas nuevas: " + added + ".");
                            });
                        } catch (Exception e) { ui(() -> error("No se pudo importar. Comprueba el límite de 12 cuentas, el espacio disponible y la versión de Android (6 o superior si incluye contraseñas).")); }
                    });
                }).show();
    }

    private interface PasswordAction { void run(char[] password, boolean includeSecrets); }
    private void askPassword(boolean exporting, PasswordAction action) { askPassword(exporting, action, () -> {}); }
    private void askPassword(boolean exporting, PasswordAction action, Runnable cancel) {
        LinearLayout form=new LinearLayout(activity); form.setOrientation(LinearLayout.VERTICAL);
        int pad=(int)(20*activity.getResources().getDisplayMetrics().density); form.setPadding(pad,pad,pad,pad);
        EditText password=new EditText(activity); password.setHint("Contraseña del respaldo (mínimo 12 caracteres)");
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        password.setFilters(new InputFilter[]{new InputFilter.LengthFilter(128)}); form.addView(password);
        EditText confirm=new EditText(activity); confirm.setHint("Repite la contraseña");
        confirm.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        confirm.setFilters(new InputFilter[]{new InputFilter.LengthFilter(128)});
        CheckBox secrets=new CheckBox(activity); secrets.setText("Incluir las contraseñas de mis cuentas guardadas");
        if (exporting) { form.addView(confirm); form.addView(secrets); }
        ScrollView scroll=new ScrollView(activity); scroll.addView(form);
        AlertDialog dialog=new AlertDialog.Builder(activity).setTitle(exporting ? "Proteger respaldo" : "Abrir respaldo")
                .setView(scroll).setPositiveButton(exporting ? "CREAR" : "ABRIR", null).setNegativeButton("Cancelar", (d,w) -> cancel.run()).create();
        dialog.setOnCancelListener(d -> cancel.run());
        dialog.setOnDismissListener(d -> { password.setText(""); confirm.setText(""); });
        if (dialog.getWindow() != null) dialog.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            char[] value=new char[password.length()]; password.getText().getChars(0, password.length(), value, 0);
            if (value.length < 12) { password.setError("Usa al menos 12 caracteres."); Arrays.fill(value, '\0'); return; }
            if (exporting && !android.text.TextUtils.equals(password.getText(), confirm.getText())) {
                confirm.setError("Las contraseñas no coinciden."); Arrays.fill(value, '\0'); return;
            }
            boolean include=secrets.isChecked(); dialog.dismiss(); action.run(value, include);
        }));
        dialog.show();
    }

    private TextView text(LinearLayout parent, String value, int size) {
        TextView view=new TextView(activity); view.setText(value); view.setTextColor(Color.WHITE); view.setTextSize(size);
        int pad=(int)(10*activity.getResources().getDisplayMetrics().density); view.setPadding(pad,pad,pad,pad); parent.addView(view); return view;
    }
    private void button(LinearLayout parent, String title, Runnable action) {
        Button button=new Button(activity); button.setText(title); button.setFocusable(true);
        button.setOnClickListener(v -> action.run()); parent.addView(button);
    }
}
