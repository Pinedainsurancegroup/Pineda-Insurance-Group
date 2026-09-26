package com.pinedaagencygroup.leads;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Build;
import android.text.InputType;
import android.view.View;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.google.firebase.auth.EmailAuthProvider;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseAuthException;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.UserInfo;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.Source;

/** Native password entry. No password crosses the WebView bridge or is stored by PAG. */
final class OwnerPasswordAccess {
    private static final String OWNER_EMAIL = "juanpinedainsurance@gmail.com";
    private static final String OWNER_UID = "oPfL5Zj374PvyoDEsI6kVIwajJo2";
    private final Activity activity;
    private final Runnable confirmGoogle;
    private AlertDialog dialog;
    private int generation;

    OwnerPasswordAccess(Activity activity, Runnable confirmGoogle) {
        this.activity = activity;
        this.confirmGoogle = confirmGoogle;
    }

    void close() {
        generation++;
        if (dialog != null) { dialog.dismiss(); dialog = null; }
    }

    private boolean sameOwner(FirebaseUser user) {
        return user != null && OWNER_UID.equals(user.getUid()) &&
                OWNER_EMAIL.equalsIgnoreCase(user.getEmail()) && user.isEmailVerified();
    }

    private boolean current(int ticket) {
        return ticket == generation && !activity.isFinishing() && !activity.isDestroyed();
    }

    void signIn(Runnable verifiedSignIn) {
        if (!FirebasePushManager.ensureInitialized(activity)) return;
        entry(false, null, verifiedSignIn);
    }

    void configure() {
        if (!FirebasePushManager.ensureInitialized(activity)) return;
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (!sameOwner(user)) return;
        close();
        final int ticket = generation;
        FirebaseFirestore.getInstance().collection("users").document(user.getUid())
                .get(Source.SERVER).addOnCompleteListener(activity, task -> {
                    if (!current(ticket) || !sameOwner(FirebaseAuth.getInstance().getCurrentUser())) return;
                    DocumentSnapshot profile = task.isSuccessful() ? task.getResult() : null;
                    if (!allowed(profile)) {
                        info("No se pudo comprobar tu permiso de Owner. Revisa tu conexión.");
                        return;
                    }
                    for (UserInfo provider : user.getProviderData()) {
                        if (EmailAuthProvider.PROVIDER_ID.equals(provider.getProviderId())) {
                            info("Tu contraseña de PAG Leads ya está configurada. Puedes usarla en el otro teléfono. Si la olvidaste, usa Recuperar contraseña en la pantalla de acceso.");
                            return;
                        }
                    }
                    entry(true, user, () -> {});
                });
    }

    private boolean allowed(DocumentSnapshot profile) {
        return profile != null && profile.exists() && "owner".equals(profile.getString("role")) &&
                Boolean.TRUE.equals(profile.getBoolean("active")) &&
                !Boolean.TRUE.equals(profile.getBoolean("suspended"));
    }

    private EditText field(LinearLayout layout, String label, int type) {
        TextView title = new TextView(activity);
        title.setText(label);
        layout.addView(title);
        EditText input = new EditText(activity);
        input.setSingleLine(true);
        input.setInputType(type);
        input.setSaveEnabled(false);
        if (Build.VERSION.SDK_INT >= 26) input.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        layout.addView(input);
        return input;
    }

    private void entry(boolean setup, FirebaseUser owner, Runnable signedIn) {
        close();
        final int ticket = generation;
        LinearLayout fields = new LinearLayout(activity);
        fields.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (20 * activity.getResources().getDisplayMetrics().density);
        fields.setPadding(pad, pad / 2, pad, pad / 2);
        TextView help = new TextView(activity);
        help.setText(setup
                ? "Crea una contraseña exclusiva de PAG Leads, de 12 a 128 caracteres. Conservarás tu cuenta, leads e historial."
                : "Acceso del Owner con la contraseña de PAG Leads. Puedes crearla en Ajustes del teléfono donde ya ingresaste con Google.");
        fields.addView(help);
        EditText email = field(fields, "Correo del Owner", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        email.setText(setup ? OWNER_EMAIL : "");
        email.setEnabled(!setup);
        EditText password = field(fields, "Contraseña de PAG Leads", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        EditText repeat = setup ? field(fields, "Repetir contraseña", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD) : null;
        TextView status = new TextView(activity);
        status.setText("Usa una contraseña distinta de la de tu correo Google.");
        fields.addView(status);
        ScrollView scroll = new ScrollView(activity);
        scroll.addView(fields);
        AlertDialog.Builder builder = new AlertDialog.Builder(activity)
                .setTitle(setup ? "Crear contraseña de PAG Leads" : "Entrar con correo")
                .setView(scroll).setPositiveButton(setup ? "Crear contraseña" : "Entrar", null)
                .setNegativeButton("Cancelar", null);
        if (!setup) builder.setNeutralButton("Recuperar contraseña", null);
        AlertDialog entry = builder.create();
        dialog = entry;
        entry.setOnDismissListener(d -> {
            password.setText("");
            if (repeat != null) repeat.setText("");
            if (dialog == entry) { dialog = null; generation++; }
        });
        entry.show();
        if (entry.getWindow() != null) entry.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        entry.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (!current(ticket)) return;
            String address = email.getText().toString().trim();
            if (!OWNER_EMAIL.equalsIgnoreCase(address)) {
                status.setText("En esta versión el acceso manual es exclusivo del correo Owner autorizado.");
                return;
            }
            String secret = password.getText().toString();
            if (secret.isEmpty() || secret.length() > 128 || (setup && secret.length() < 12)) {
                status.setText(setup ? "Escribe entre 12 y 128 caracteres." : "Escribe tu contraseña de PAG Leads.");
                return;
            }
            if (setup && !secret.equals(repeat.getText().toString())) {
                status.setText("Las contraseñas no coinciden.");
                return;
            }
            busy(entry, true);
            status.setText(setup ? "Comprobando tu cuenta…" : "Iniciando sesión…");
            if (setup) {
                // Recheck the profile at submission, not just when opening the dialog.
                FirebaseFirestore.getInstance().collection("users").document(OWNER_UID).get(Source.SERVER)
                        .addOnCompleteListener(activity, profileTask -> {
                            if (!current(ticket)) return;
                            FirebaseUser currentUser = FirebaseAuth.getInstance().getCurrentUser();
                            if (!sameOwner(currentUser) || currentUser != owner || !profileTask.isSuccessful() || !allowed(profileTask.getResult())) {
                                password.setText(""); repeat.setText("");
                                busy(entry, false); status.setText("No se pudo validar tu permiso. Vuelve a entrar con Google.");
                                return;
                            }
                            // Linking preserves the existing UID. Never create a second user or replace Google.
                            owner.linkWithCredential(EmailAuthProvider.getCredential(OWNER_EMAIL, secret))
                                    .addOnCompleteListener(activity, task -> {
                                        if (!current(ticket)) return;
                                        password.setText(""); repeat.setText("");
                                        if (task.isSuccessful() && sameOwner(task.getResult().getUser())) {
                                            entry.dismiss();
                                            info("Contraseña creada. Ya puedes entrar con tu correo y esta contraseña en el otro teléfono. Tu información sigue en la misma cuenta.");
                                        } else {
                                            busy(entry, false);
                                            status.setText(error(task.getException(), true));
                                            if (task.getException() instanceof FirebaseAuthException &&
                                                    "ERROR_REQUIRES_RECENT_LOGIN".equals(((FirebaseAuthException) task.getException()).getErrorCode())) {
                                                entry.dismiss();
                                                dialog = new AlertDialog.Builder(activity).setTitle("Confirmar identidad")
                                                        .setMessage("Confirma tu cuenta con Google. Luego vuelve a Ajustes para crear la contraseña de PAG Leads.")
                                                        .setPositiveButton("Continuar con Google", (d, which) -> { close(); confirmGoogle.run(); })
                                                        .setNegativeButton("Cancelar", null).show();
                                            }
                                        }
                                    });
                        });
            } else {
                FirebaseAuth.getInstance().signInWithEmailAndPassword(OWNER_EMAIL, secret)
                        .addOnCompleteListener(activity, task -> {
                            if (!current(ticket)) return;
                            password.setText("");
                            if (task.isSuccessful() && sameOwner(task.getResult().getUser())) {
                                entry.dismiss();
                                signedIn.run(); // PAGAuthGate still requires the current server role and suspension check.
                            } else {
                                if (task.isSuccessful()) FirebaseAuth.getInstance().signOut();
                                busy(entry, false);
                                status.setText(task.isSuccessful() ? "Esta cuenta no corresponde al Owner autorizado." : error(task.getException(), false));
                            }
                        });
            }
        });
        if (!setup) entry.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
            if (!OWNER_EMAIL.equalsIgnoreCase(email.getText().toString().trim())) {
                status.setText("Escribe el correo del Owner para recuperar tu contraseña."); return;
            }
            password.setText("");
            busy(entry, true);
            FirebaseAuth.getInstance().setLanguageCode("es");
            FirebaseAuth.getInstance().sendPasswordResetEmail(OWNER_EMAIL).addOnCompleteListener(activity, task -> {
                if (!current(ticket)) return;
                busy(entry, false);
                status.setText(task.isSuccessful() ? "Revisa tu correo y la carpeta de spam para recuperar la contraseña de PAG Leads." : error(task.getException(), false));
            });
        });
    }

    private void busy(AlertDialog entry, boolean busy) {
        entry.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(!busy);
        if (entry.getButton(AlertDialog.BUTTON_NEUTRAL) != null)
            entry.getButton(AlertDialog.BUTTON_NEUTRAL).setEnabled(!busy);
    }

    private String error(Exception exception, boolean setup) {
        String code = exception instanceof FirebaseAuthException ? ((FirebaseAuthException) exception).getErrorCode() : "";
        if ("ERROR_REQUIRES_RECENT_LOGIN".equals(code)) return "Google pide confirmar nuevamente tu identidad. Vuelve a entrar con Google y repite este paso.";
        if ("ERROR_OPERATION_NOT_ALLOWED".equals(code)) return "Falta activar el acceso por correo en Firebase. Tu acceso con Google sigue disponible.";
        if ("ERROR_WEAK_PASSWORD".equals(code)) return "Elige una contraseña más larga y difícil de adivinar.";
        if ("ERROR_PROVIDER_ALREADY_LINKED".equals(code)) return "Ya existe una contraseña de PAG Leads. Usa Recuperar contraseña si la olvidaste.";
        if ("ERROR_TOO_MANY_REQUESTS".equals(code)) return "Hubo demasiados intentos. Espera unos minutos antes de volver a intentar.";
        return setup ? "No se pudo crear la contraseña. Revisa la conexión y vuelve a intentar. Tu cuenta se conserva." : "No se pudo entrar. Revisa tu correo, contraseña de PAG Leads y conexión.";
    }

    private void info(String text) {
        if (!activity.isFinishing() && !activity.isDestroyed())
            new AlertDialog.Builder(activity).setTitle("PAG Leads").setMessage(text).setPositiveButton("Entendido", null).show();
    }
}
