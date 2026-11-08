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
        saveSecret(context, prefs, "current_password", password);
        String cipher = prefs == null ? "" : prefs.getString(secretCipherKey("current_password"), "");
        String iv = prefs == null ? "" : prefs.getString(secretIvKey("current_password"), "");
        if (prefs != null) prefs.edit().putString(PREF_CIPHER, cipher).putString(PREF_IV, iv).apply();
    }

    static String loadPassword(Context context, SharedPreferences prefs) {
        String value = loadSecret(context, prefs, "current_password");
        if (!value.isEmpty()) return value;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M || prefs == null) return "";
        String encryptedText = prefs.getString(PREF_CIPHER, "");
        String ivText = prefs.getString(PREF_IV, "");
        return decryptStored(prefs, encryptedText, ivText);
    }

    static void clearPassword(SharedPreferences prefs) {
        clearSecret(prefs, "current_password");
        if (prefs != null) prefs.edit().remove(PREF_CIPHER).remove(PREF_IV).apply();
    }

    static void saveSecret(Context context, SharedPreferences prefs, String slot, String value) {
        if (prefs == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.M || value == null) {
            clearSecret(prefs, slot);
            return;
        }
        try {
            SecretKey key = getOrCreateKey();
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key);
            byte[] encrypted = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
            prefs.edit()
                    .putString(secretCipherKey(slot), Base64.encodeToString(encrypted, Base64.NO_WRAP))
                    .putString(secretIvKey(slot), Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                    .apply();
        } catch (Exception e) {
            clearSecret(prefs, slot);
        }
    }

    static String loadSecret(Context context, SharedPreferences prefs, String slot) {
        if (prefs == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return "";
        return decryptStored(
                prefs,
                prefs.getString(secretCipherKey(slot), ""),
                prefs.getString(secretIvKey(slot), "")
        );
    }

    static void clearSecret(SharedPreferences prefs, String slot) {
        if (prefs != null) prefs.edit()
                .remove(secretCipherKey(slot))
                .remove(secretIvKey(slot))
                .apply();
    }

    private static String decryptStored(SharedPreferences prefs, String encryptedText, String ivText) {
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
            return "";
        }
    }

    private static String safeSlot(String slot) {
        if (slot == null || slot.isEmpty()) return "default";
        return slot.replaceAll("[^A-Za-z0-9_.-]", "_");
    }

    private static String secretCipherKey(String slot) {
        return "secure_secret_" + safeSlot(slot) + "_cipher";
    }

    private static String secretIvKey(String slot) {
        return "secure_secret_" + safeSlot(slot) + "_iv";
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
