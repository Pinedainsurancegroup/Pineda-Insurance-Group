package com.pimflextv.next;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class SecureStore {
    private static final String KEY_ALIAS = "PimFlexSessionKey";
    private static final String PREF_CIPHER = "secure_password";
    private static final String PREF_IV = "secure_password_iv";

    private SecureStore() {}

    static void savePassword(Context context, SharedPreferences prefs, String password) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || password == null) {
            clearPassword(prefs);
            return;
        }
        try {
            SecretKey key = getOrCreateKey();
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key);
            byte[] encrypted = cipher.doFinal(password.getBytes(StandardCharsets.UTF_8));
            prefs.edit()
                    .putString(PREF_CIPHER, Base64.encodeToString(encrypted, Base64.NO_WRAP))
                    .putString(PREF_IV, Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                    .apply();
        } catch (Exception e) {
            clearPassword(prefs);
        }
    }

    static String loadPassword(Context context, SharedPreferences prefs) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || prefs == null) return "";
        String encryptedText = prefs.getString(PREF_CIPHER, "");
        String ivText = prefs.getString(PREF_IV, "");
        if (encryptedText == null || encryptedText.isEmpty() || ivText == null || ivText.isEmpty()) return "";
        try {
            KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
            ks.load(null);
            SecretKey key = (SecretKey) ks.getKey(KEY_ALIAS, null);
            if (key == null) return "";
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key,
                    new GCMParameterSpec(128, Base64.decode(ivText, Base64.NO_WRAP)));
            byte[] clear = cipher.doFinal(Base64.decode(encryptedText, Base64.NO_WRAP));
            return new String(clear, StandardCharsets.UTF_8);
        } catch (Exception e) {
            clearPassword(prefs);
            return "";
        }
    }

    static void clearPassword(SharedPreferences prefs) {
        if (prefs != null) prefs.edit().remove(PREF_CIPHER).remove(PREF_IV).apply();
    }

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        SecretKey existing = (SecretKey) ks.getKey(KEY_ALIAS, null);
        if (existing != null) return existing;

        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build();
        generator.init(spec);
        return generator.generateKey();
    }
}
