package com.pinedaagencygroup.leads;

import android.app.*;
import android.content.Intent;
import android.text.InputType;
import android.widget.*;
import com.google.firebase.auth.*;
import com.google.firebase.firestore.*;
import com.google.android.gms.tasks.Task;
import java.util.*;

/** Email possession authenticates; only an audited Owner invitation grants access. */
final class EmailInvitationAccess {
    private final Activity activity;
    private AlertDialog dialog;
    private int generation;
    EmailInvitationAccess(Activity a) { activity = a; }
    void close() { generation++; if (dialog != null) dialog.dismiss(); dialog = null; }
    private boolean current(int ticket) { return generation == ticket && !activity.isDestroyed() && !activity.isFinishing(); }
    static String emailKey(String email) { return email.trim().toLowerCase(Locale.ROOT); }
    static Task<Void> send(Activity a, String email) {
        String host = a.getString(R.string.pag_firebase_project_id) + ".firebaseapp.com";
        ActionCodeSettings settings = ActionCodeSettings.newBuilder()
            .setUrl("https://" + host + "/__/auth/handler")
            .setHandleCodeInApp(true)
            .setAndroidPackageName(a.getPackageName(), false, null).build();
        FirebaseAuth.getInstance().setLanguageCode("es");
        return FirebaseAuth.getInstance().sendSignInLinkToEmail(email, settings);
    }
    void login(Runnable done) {
        close(); final int ticket = generation;
        LinearLayout fields = new LinearLayout(activity); fields.setOrientation(1); fields.setPadding(28,20,28,20);
        TextView text = new TextView(activity); text.setText("Escribe el correo que Juan autorizó. Recibirás un enlace para entrar sin contraseña."); fields.addView(text);
        EditText email = new EditText(activity); email.setHint("Correo autorizado"); email.setSingleLine(true);
        email.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS); fields.addView(email);
        email.setText(activity.getSharedPreferences("pag_email_access",0).getString("email",""));
        dialog = new AlertDialog.Builder(activity).setTitle("Entrar como agente").setView(fields)
            .setPositiveButton("Recibir enlace",null).setNeutralButton("Tengo el enlace",null).setNegativeButton("Volver",null).create();
        AlertDialog d=dialog; d.show();
        d.getButton(-1).setOnClickListener(v->{
            String address=emailKey(email.getText().toString());
            if (!android.util.Patterns.EMAIL_ADDRESS.matcher(address).matches()) { text.setText("Escribe un correo válido."); return; }
            d.getButton(-1).setEnabled(false);
            send(activity,address).addOnCompleteListener(activity,t->{
                if (!current(ticket)) return; d.getButton(-1).setEnabled(true);
                if (t.isSuccessful()) {
                    activity.getSharedPreferences("pag_email_access",0).edit().putString("email",address).apply();
                    text.setText("Enlace enviado. Ábrelo en este teléfono. Si el correo está en otro dispositivo, copia el enlace y usa Tengo el enlace. Revisa también spam.");
                } else text.setText("No se pudo enviar el enlace. Revisa la conexión o inténtalo más tarde.");
            });
        });
        d.getButton(-3).setOnClickListener(v->pasteLink(done));
    }
    private void pasteLink(Runnable done) {
        close();
        EditText link=new EditText(activity); link.setHint("Pega el enlace recibido por correo"); link.setSaveEnabled(false);
        dialog=new AlertDialog.Builder(activity).setTitle("Abrir mi invitación").setView(link)
            .setPositiveButton("Continuar",null).setNegativeButton("Volver",null).create();
        AlertDialog d=dialog;d.show();d.getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        d.getButton(-1).setOnClickListener(v->{String value=link.getText().toString().trim();if(!accept(value,done))link.setError("Pega el enlace completo de acceso de PAG Leads.");});
    }
    boolean accept(Intent intent,Runnable done) { return intent != null && intent.getData()!=null && accept(intent.getData().toString(),done); }
    private boolean accept(String link,Runnable done) {
        // The SDK validates the one-time code; never read an email from URL parameters.
        android.net.Uri uri=android.net.Uri.parse(link);
        String host=activity.getString(R.string.pag_firebase_project_id)+".firebaseapp.com";
        if(!"https".equals(uri.getScheme()) || !host.equals(uri.getHost()) || !FirebaseAuth.getInstance().isSignInWithEmailLink(link)) return false;
        close(); final int ticket=generation;
        LinearLayout fields=new LinearLayout(activity);fields.setOrientation(1);fields.setPadding(28,20,28,20);
        TextView info=new TextView(activity);info.setText("Confirma el correo al que Juan envió la invitación.");fields.addView(info);
        EditText email=new EditText(activity);email.setHint("Correo de la invitación");email.setSingleLine(true);
        email.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS);
        email.setText(activity.getSharedPreferences("pag_email_access",0).getString("email",""));fields.addView(email);
        dialog=new AlertDialog.Builder(activity).setTitle("Entrar a PAG Leads").setView(fields)
            .setPositiveButton("Entrar",null).setNegativeButton("Volver",(d,w)->{activity.getIntent().setData(null);done.run();}).create();
        AlertDialog d=dialog;d.show();d.setCancelable(false);
        d.getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        d.getButton(-1).setOnClickListener(v->{
            String address=emailKey(email.getText().toString());
            if(!android.util.Patterns.EMAIL_ADDRESS.matcher(address).matches()){info.setText("Escribe el correo de la invitación.");return;}
            d.getButton(-1).setEnabled(false);
            FirebaseAuth.getInstance().signInWithEmailLink(address,link).addOnCompleteListener(activity,t->{
                if(!current(ticket))return;
                if(t.isSuccessful()) {
                    activity.getSharedPreferences("pag_email_access",0).edit().putString("email",address).apply();
                    activity.getIntent().setData(null);close();done.run();
                } else {d.getButton(-1).setEnabled(true);info.setText("El enlace no es válido para ese correo o ya venció. Solicita un enlace nuevo en Entrar como agente.");}
            });
        });
        return true;
    }
    /** Redeem once, atomically binding the verified UID and approved scopes. Never reactivate an existing profile. */
    Task<Void> redeem() {
        FirebaseUser user=FirebaseAuth.getInstance().getCurrentUser();
        if(user==null || !user.isEmailVerified() || user.getEmail()==null)
            return com.google.android.gms.tasks.Tasks.forException(new IllegalStateException("EMAIL_REQUIRED"));
        FirebaseFirestore db=FirebaseFirestore.getInstance(); String uid=user.getUid(), key=emailKey(user.getEmail());
        DocumentReference invitation=db.collection("agentInvitations").document(key), profile=db.collection("users").document(uid), request=db.collection("accessRequests").document(uid);
        String eventId=UUID.randomUUID().toString();
        return db.runTransaction(tx->{
            DocumentSnapshot i=tx.get(invitation),p=tx.get(profile),r=tx.get(request);
            if(p.exists()) return null;
            if(!i.exists() || !Boolean.TRUE.equals(i.getBoolean("active")) || !"".equals(i.getString("claimedUid")))
                throw new IllegalStateException("INVITATION_REQUIRED");
            Map<String,Object> after=new HashMap<>();after.put("role","agent");after.put("active",true);after.put("suspended",false);
            after.put("email",user.getEmail());after.put("name",i.getString("name"));after.put("scopes",i.get("scopes"));
            after.put("revision",1L);after.put("lastEventId",eventId);after.put("updatedBy",uid);after.put("updatedAt",FieldValue.serverTimestamp());
            Map<String,Object> audit=new HashMap<>();audit.put("before",new HashMap<>());audit.put("after",after);audit.put("actorUid",uid);audit.put("createdAt",FieldValue.serverTimestamp());
            if(!r.exists()) {Map<String,Object> req=new HashMap<>();req.put("email",user.getEmail());req.put("name",i.getString("name"));req.put("createdAt",FieldValue.serverTimestamp());tx.set(request,req);}
            tx.set(profile,after);tx.set(profile.collection("audit").document(eventId),audit);
            tx.update(invitation,"claimedUid",uid,"claimedAt",FieldValue.serverTimestamp());
            return null;
        });
    }
}
