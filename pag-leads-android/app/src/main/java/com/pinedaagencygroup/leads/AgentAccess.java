package com.pinedaagencygroup.leads;

import android.app.*;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.*;
import com.google.firebase.auth.*;
import com.google.firebase.firestore.*;
import java.util.*;

/** Native account enrolment. A verified email requests access; only Juan grants it. */
final class AgentAccess {
    private final Activity activity;
    private AlertDialog dialog;
    private int generation;
    AgentAccess(Activity activity) { this.activity = activity; }
    void close() { generation++; if (dialog != null) dialog.dismiss(); dialog = null; }
    private boolean current(int n) { return n == generation && !activity.isFinishing() && !activity.isDestroyed(); }
    private EditText field(LinearLayout view, String label, int type) {
        EditText e = new EditText(activity); e.setHint(label); e.setInputType(type); e.setSingleLine(true);
        e.setSaveEnabled(false); view.addView(e); return e;
    }
    void account(boolean create, Runnable done) {
        close(); final int ticket = generation;
        LinearLayout fields = new LinearLayout(activity); fields.setOrientation(1); fields.setPadding(28,20,28,20);
        EditText email = field(fields,"Correo", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        EditText password = field(fields,"Contraseña de PAG Leads", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        EditText repeat = create ? field(fields,"Repite tu contraseña", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD) : null;
        TextView status = new TextView(activity); fields.addView(status);
        status.setText(create ? "Usa una contraseña exclusiva de PAG Leads. Crear una cuenta no concede acceso a prospectos." : "Usa tu contraseña de PAG Leads, no la de Gmail.");
        dialog = new AlertDialog.Builder(activity).setTitle(create ? "Solicitar acceso" : "Entrar con correo")
            .setView(fields).setPositiveButton(create ? "Crear cuenta" : "Entrar",null).setNegativeButton("Cancelar",null)
            .setNeutralButton(create ? "Ya tengo cuenta" : "Recuperar contraseña",null).create();
        AlertDialog d = dialog; d.show(); d.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        d.setOnDismissListener(x -> {password.setText(""); if(repeat != null) repeat.setText("");});
        d.getButton(-1).setOnClickListener(v -> {
            String address=email.getText().toString().trim(), secret=password.getText().toString();
            if (!android.util.Patterns.EMAIL_ADDRESS.matcher(address).matches() || secret.length()>128 ||
                secret.length() < (create ? 12 : 1) || (create && !secret.equals(repeat.getText().toString()))) {
                status.setText("Revisa el correo y la contraseña. Para crearla usa 12 a 128 caracteres y repítela igual."); return;
            }
            d.getButton(-1).setEnabled(false); d.getButton(-3).setEnabled(false);
            FirebaseAuth auth=FirebaseAuth.getInstance(); auth.setLanguageCode("es");
            com.google.android.gms.tasks.Task<AuthResult> task = create ? auth.createUserWithEmailAndPassword(address,secret) : auth.signInWithEmailAndPassword(address,secret);
            task.addOnCompleteListener(activity, result -> {
                if (!current(ticket)) return;
                password.setText(""); if(repeat != null) repeat.setText("");
                d.getButton(-1).setEnabled(true); d.getButton(-3).setEnabled(true);
                if(result.isSuccessful()) { close(); done.run(); }
                else status.setText("No se completó el acceso. Revisa los datos y la conexión. Si ya tienes una cuenta, entra o recupera tu contraseña.");
            });
        });
        d.getButton(-3).setOnClickListener(v -> {
            if (create) { account(false,done); return; }
            String address=email.getText().toString().trim();
            if(!android.util.Patterns.EMAIL_ADDRESS.matcher(address).matches()) {status.setText("Escribe tu correo.");return;}
            d.getButton(-3).setEnabled(false);
            FirebaseAuth.getInstance().sendPasswordResetEmail(address).addOnCompleteListener(activity,t -> {
                if(!current(ticket))return; d.getButton(-3).setEnabled(true);
                status.setText(t.isSuccessful() ? "Si el correo tiene una cuenta, recibirás instrucciones. Revisa también spam." : "No se pudo solicitar la recuperación. Revisa tu conexión.");
            });
        });
    }
    void request(Runnable done) {
        FirebaseUser user=FirebaseAuth.getInstance().getCurrentUser(); if(user==null){account(true,done);return;}
        close(); final int ticket=generation;
        if(!user.isEmailVerified()) {
            dialog=new AlertDialog.Builder(activity).setTitle("Verifica tu correo")
                .setMessage("Confirma "+user.getEmail()+" antes de solicitar acceso. Después Juan decidirá qué secciones puedes trabajar.")
                .setPositiveButton("Enviar verificación",(d,w)->user.sendEmailVerification().addOnCompleteListener(activity,t->{
                    if(!current(ticket))return;
                    new AlertDialog.Builder(activity).setMessage(t.isSuccessful()?"Revisa tu correo. Luego pulsa Volver a comprobar acceso.":"No se pudo enviar. Espera un momento y vuelve a intentarlo.").setPositiveButton("Entendido",null).show();
                })).setNegativeButton("Volver",null).show(); return;
        }
        FirebaseFirestore db=FirebaseFirestore.getInstance();
        db.collection("accessRequests").document(user.getUid()).get(Source.SERVER).addOnCompleteListener(activity,t->{
            if(!current(ticket))return;
            if(!t.isSuccessful()){message("No se pudo consultar tu solicitud. Revisa tu conexión.");return;}
            if(t.getResult().exists()){message("Tu solicitud ya está registrada. Juan debe aprobarla o revisar tu acceso.");return;}
            LinearLayout fields=new LinearLayout(activity);fields.setOrientation(1);fields.setPadding(28,20,28,20);
            EditText name=field(fields,"Nombre completo",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_WORDS);
            if(user.getDisplayName()!=null)name.setText(user.getDisplayName());
            TextView info=new TextView(activity);info.setText(user.getEmail()+"\nSolo Juan puede aprobar tus permisos.");fields.addView(info);
            dialog=new AlertDialog.Builder(activity).setTitle("Solicitar autorización a Juan").setView(fields).setPositiveButton("Solicitar",null).setNegativeButton("Cancelar",null).create();
            AlertDialog d=dialog;d.show();d.getButton(-1).setOnClickListener(v->{
                String n=name.getText().toString().trim();if(n.isEmpty()||n.length()>120){info.setText("Escribe tu nombre (máximo 120 caracteres).");return;}
                Map<String,Object> request=new HashMap<>();request.put("name",n);request.put("email",user.getEmail());request.put("createdAt",FieldValue.serverTimestamp());
                d.getButton(-1).setEnabled(false);
                db.collection("accessRequests").document(user.getUid()).set(request).addOnCompleteListener(activity,saved->{
                    if(!current(ticket))return;
                    if(saved.isSuccessful()){close();done.run();}else{d.getButton(-1).setEnabled(true);info.setText("No se pudo registrar. Vuelve a comprobar el acceso antes de reintentar.");}
                });
            });
        });
    }
    private void message(String text){dialog=new AlertDialog.Builder(activity).setTitle("PAG Leads").setMessage(text).setPositiveButton("Entendido",null).show();}
}
