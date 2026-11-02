package com.pinedaagencygroup.leads;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import com.google.android.gms.tasks.Tasks;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.Source;
import com.google.firebase.messaging.FirebaseMessaging;
import java.util.concurrent.TimeUnit;

/** Staging-only checks after manual login with a synthetic fixture account.
 * No database mutations, outbound messages, installs, or credential logging.
 */
public final class StagingFunctionalInstrumentation extends Instrumentation {
    private Bundle arguments;
    @Override public void onCreate(Bundle args) { arguments = args; super.onCreate(args); start(); }
    private void require(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        SharedPreferences fixture = null;
        try {
            Context context = getTargetContext();
            require("com.pinedaagencygroup.leads.staging".equals(context.getPackageName()), "isolated-staging-package-required");
            String expectedProject = arguments.getString("expectedProject", "");
            String expectedUid = arguments.getString("expectedUid", "");
            require(!expectedProject.isEmpty() && !expectedUid.isEmpty(), "explicit-staging-fixture-required");
            require(!"pag-leads-8c6ef".equals(expectedProject), "production-project-prohibited");
            require(expectedProject.equals(context.getString(R.string.pag_firebase_project_id)), "staging-project-mismatch");
            require(FirebasePushManager.ensureInitialized(context), "firebase-initialization-failed");
            require(expectedProject.equals(com.google.firebase.FirebaseApp.getInstance().getOptions().getProjectId()), "active-project-mismatch");
            FirebaseUser user = FirebaseAuth.getInstance().getCurrentUser();
            require(user != null && expectedUid.equals(user.getUid()), "manual-staging-login-required");
            require(Tasks.await(user.getIdToken(true), 30, TimeUnit.SECONDS).getToken() != null, "id-token-refresh-failed");
            DocumentSnapshot profile = Tasks.await(FirebaseFirestore.getInstance().collection("users")
                    .document(expectedUid).get(Source.SERVER), 30, TimeUnit.SECONDS);
            require(profile.exists() && Boolean.TRUE.equals(profile.getBoolean("active")) &&
                    !Boolean.TRUE.equals(profile.getBoolean("suspended")), "active-staging-profile-required");
            require(!Tasks.await(FirebaseMessaging.getInstance().getToken(), 30, TimeUnit.SECONDS).isEmpty(), "fcm-token-unavailable");
            fixture = context.getSharedPreferences("staging_vault_fixture", Context.MODE_PRIVATE);
            require(fixture.getAll().isEmpty(), "fixture-store-not-empty-preserve-for-review");
            require(fixture.edit().putString("token", "synthetic-staging-only").commit(), "fixture-write-failed");
            require("synthetic-staging-only".equals(TokenVault.read(fixture)), "vault-migration-failed");
            require(!fixture.contains("token"), "plaintext-token-remains");
            fixture.edit().putString("token_ciphertext", "invalid:ciphertext").commit();
            require(TokenVault.read(fixture).isEmpty(), "vault-corruption-not-rejected");
            require(fixture.edit().clear().commit(), "fixture-cleanup-failed");
            result.putString("stream", "STAGING_COMPONENT_CHECKS_PASS: login/token refresh, server profile read, FCM token, synthetic vault migration. No push sent; WebView upgrade and sync remain separate tests.\n");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            // Do not echo SDK error messages: they can contain account details or endpoints.
            result.putString("stream", "STAGING_COMPONENT_CHECKS_FAIL: " + error.getClass().getSimpleName() + "; inspect fixture and prerequisites without logging credentials.\n");
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
