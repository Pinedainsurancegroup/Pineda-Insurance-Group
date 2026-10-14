package com.pinedaagencygroup.leads;

import android.app.Activity;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.GetCredentialException;

import com.google.android.libraries.identity.googleid.GetGoogleIdOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.Source;
import com.google.firebase.firestore.ListenerRegistration;
import com.google.firebase.firestore.MetadataChanges;

import java.util.concurrent.Executor;

/** Blocks the legacy recruitment UI until the current server profile confirms owner access. */
final class PAGAuthGate {
    interface Listener { void onOwnerVerified(); void onAccessRevoked(); void onAgentVerified(DocumentSnapshot profile); }

    private final Activity activity;
    private final Listener listener;
    private final LinearLayout view;
    private final TextView message;
    private final Button button;
    private final Button emailButton;
    private final OwnerPasswordAccess passwords;
    private final AgentAccess agents;
    private final EmailInvitationAccess invitations;
    private final Button requestButton, retryButton, signOutButton;
    private final Executor ui;
    private final AccessCheck check = new AccessCheck();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ListenerRegistration profileWatch;
    private Runnable timeout;

    PAGAuthGate(Activity activity, Listener listener) {
        this.activity = activity;
        this.listener = listener;
        this.ui = activity::runOnUiThread;
        passwords = new OwnerPasswordAccess(activity, this::signIn);
        agents = new AgentAccess(activity);
        invitations = new EmailInvitationAccess(activity);
        view = new LinearLayout(activity);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setGravity(Gravity.CENTER);
        view.setPadding(32, 32, 32, 32);
        message = new TextView(activity);
        message.setTextSize(18);
        button = new Button(activity);
        button.setText("Entrar como administrador · Google");
        button.setOnClickListener(v -> signIn());
        emailButton = new Button(activity);
        emailButton.setText("Entrar como agente · sin contraseña");
        emailButton.setOnClickListener(v -> invitations.login(this::verify));
        view.addView(message);
        view.addView(emailButton);
        view.addView(button);
        requestButton = new Button(activity); requestButton.setText("Acceso anterior con contraseña");
        requestButton.setOnClickListener(v -> agents.account(false, this::verify)); requestButton.setVisibility(android.view.View.GONE); view.addView(requestButton);
        retryButton = new Button(activity); retryButton.setText("Volver a comprobar acceso");
        retryButton.setOnClickListener(v -> refresh()); view.addView(retryButton);
        signOutButton = new Button(activity); signOutButton.setText("Cambiar de cuenta / cerrar sesión");
        signOutButton.setOnClickListener(v -> { pause(); FirebaseAuth.getInstance().signOut(); verify(); }); view.addView(signOutButton);
        show("Verificando acceso a PAG Leads…", false);
    }

    LinearLayout view() { return view; }

    boolean openInvitation(android.content.Intent intent) { return invitations.accept(intent, this::verify); }

    void configureOwnerPassword() { passwords.configure(); }

    void verify() {
        pause();
        if (!FirebasePushManager.ensureInitialized(activity)) {
            show("Falta la configuración de Firebase de esta compilación.", false);
            listener.onAccessRevoked();
            return;
        }
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) {
            show("Inicia sesión para abrir PAG Leads.", true);
            listener.onAccessRevoked();
            return;
        }
        final String uid = user.getUid();
        final int ticket = check.begin(uid);
        show("Verificando permisos…", false);
        timeout = () -> {
            if (!isCurrent(ticket)) return;
            pause();
            listener.onAccessRevoked();
            show("No se pudo comprobar el acceso. Revisa tu conexión y vuelve a intentar.", true);
        };
        handler.postDelayed(timeout, 15000);
        // A cached profile is never sufficient: suspension must apply to an old session.
        FirebaseFirestore.getInstance().collection("users").document(user.getUid())
                .get(Source.SERVER).addOnCompleteListener(ui, task -> {
                    if (!isCurrent(ticket)) return;
                    handler.removeCallbacks(timeout);
                    if (task.isSuccessful() && task.getResult() != null && allowed(task.getResult())) {
                        DocumentSnapshot profile = task.getResult();
                        if ("owner".equals(profile.getString("role"))) listener.onOwnerVerified();
                        else listener.onAgentVerified(profile);
                        watchProfile(uid, ticket, profile);
                    } else {
                        pause();
                        listener.onAccessRevoked();
                        if (task.isSuccessful() && task.getResult() != null && !task.getResult().exists() && user.isEmailVerified()) {
                            final int claimTicket = check.begin(uid);
                            show("Comprobando tu invitación…", false);
                            invitations.redeem().addOnCompleteListener(activity, claim -> {
                                if (!isCurrent(claimTicket)) return;
                                if (claim.isSuccessful()) verify();
                                else show("Juan debe invitar este correo y autorizar sus permisos. Si ya te invitó, revisa la conexión y vuelve a comprobar.", true);
                            });
                        } else show("Cuenta sin acceso activo. Juan debe revisar tu autorización.", true);
                    }
                });
    }

    private boolean isCurrent(int ticket) {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        return check.accepts(ticket, user == null ? null : user.getUid());
    }

    private void watchProfile(String uid, int ticket, DocumentSnapshot original) {
        if (!isCurrent(ticket)) return;
        profileWatch = FirebaseFirestore.getInstance().collection("users").document(uid)
                .addSnapshotListener(MetadataChanges.INCLUDE, (doc, error) -> {
                    if (!isCurrent(ticket)) return;
                    // Cache can never renew permission. Server denial closes the open screen too.
                    if (error != null || (doc != null && !doc.getMetadata().isFromCache() && !allowed(doc))) {
                        pause();
                        listener.onAccessRevoked();
                        show("Cuenta sin acceso activo.", true);
                    } else if (doc != null && !doc.getMetadata().isFromCache() &&
                        !java.util.Objects.equals(doc.getData(), original.getData())) {
                        listener.onAccessRevoked(); verify();
                    }
                });
    }

    void pause() {
        passwords.close();
        agents.close();
        invitations.close();
        check.cancel();
        if (timeout != null) handler.removeCallbacks(timeout);
        if (profileWatch != null) { profileWatch.remove(); profileWatch = null; }
    }

    private boolean allowed(DocumentSnapshot doc) {
        FirebaseUser u = FirebaseAuth.getInstance().getCurrentUser();
        boolean role = "owner".equals(doc.getString("role")) || ("agent".equals(doc.getString("role")) &&
            u != null && u.isEmailVerified() && java.util.Objects.equals(u.getEmail(), doc.getString("email")));
        return doc.exists() && role &&
                Boolean.TRUE.equals(doc.getBoolean("active")) &&
                !Boolean.TRUE.equals(doc.getBoolean("suspended"));
    }

    private void refresh() {
        FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
        if (user == null) { verify(); return; }
        user.reload().continueWithTask(t -> {
            if (!t.isSuccessful()) throw t.getException();
            return user.getIdToken(true);
        }).addOnCompleteListener(activity, t -> verify());
    }

    private void signIn() {
        if (!FirebasePushManager.ensureInitialized(activity)) {
            show("Falta la configuración de Firebase de esta compilación.", false);
            return;
        }
        String webClientId = activity.getString(R.string.pag_firebase_web_client_id).trim();
        if (webClientId.isEmpty()) {
            show("Falta la configuración de Google de esta compilación.", false);
            return;
        }
        show("Abriendo Google…", false);
        GetGoogleIdOption option = new GetGoogleIdOption.Builder()
                .setServerClientId(webClientId)
                .setFilterByAuthorizedAccounts(false)
                .build();
        GetCredentialRequest request = new GetCredentialRequest.Builder()
                .addCredentialOption(option).build();
        CredentialManager.create(activity).getCredentialAsync(activity, request,
                new CancellationSignal(), ui, new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                    @Override public void onResult(GetCredentialResponse response) {
                        Credential credential = response.getCredential();
                        if (!(credential instanceof CustomCredential) ||
                                !GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
                            show("Google no devolvió una cuenta válida.", true);
                            return;
                        }
                        try {
                            String idToken = GoogleIdTokenCredential.createFrom(
                                    ((CustomCredential) credential).getData()).getIdToken();
                            FirebaseAuth.getInstance().signInWithCredential(
                                    GoogleAuthProvider.getCredential(idToken, null))
                                    .addOnCompleteListener(activity, task -> {
                                        if (task.isSuccessful()) verify();
                                        else show("No se pudo iniciar sesión con Google.", true);
                                    });
                        } catch (Exception e) {
                            show("No se pudo leer la cuenta de Google.", true);
                        }
                    }
                    @Override public void onError(GetCredentialException e) {
                        show("No se completó el acceso con Google. Puedes volver a intentarlo.", true);
                    }
                });
    }

    private void show(String text, boolean enabled) {
        message.setText(text);
        button.setEnabled(enabled);
        emailButton.setEnabled(enabled);
        requestButton.setEnabled(enabled);
        retryButton.setEnabled(enabled);
        signOutButton.setEnabled(enabled);
        boolean signedIn = FirebasePushManager.ensureInitialized(activity) && FirebaseAuth.getInstance().getCurrentUser() != null;
        retryButton.setVisibility(signedIn ? android.view.View.VISIBLE : android.view.View.GONE);
        signOutButton.setVisibility(signedIn ? android.view.View.VISIBLE : android.view.View.GONE);
    }
}
