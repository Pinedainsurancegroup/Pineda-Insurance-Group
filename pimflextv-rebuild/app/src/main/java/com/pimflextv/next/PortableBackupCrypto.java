package com.pimflextv.next;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

/** Portable, bounded, authenticated format. No plaintext temporary files. */
final class PortableBackupCrypto {
    private static final byte[] MAGIC = "PIMFLEXBACKUP2\n".getBytes(StandardCharsets.US_ASCII);
    // SHA-1 PBKDF2 is available on every supported Android version (API 21+).
    private static final int ITERATIONS = 600_000;
    private static final int HEADER = MAGIC.length + 4 + 16 + 12;
    static final int MAX_CLEAR = 4 * 1024 * 1024;
    static final int MAX_FILE = MAX_CLEAR + HEADER + 16;

    static byte[] readBounded(InputStream in) throws Exception {
        if (in == null) throw new Exception("No se pudo abrir el archivo.");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int n;
        while ((n = in.read(buffer)) != -1) {
            if (out.size() + n > MAX_FILE) throw new Exception("El respaldo supera 4 MB.");
            out.write(buffer, 0, n);
        }
        return out.toByteArray();
    }

    static boolean isEncrypted(byte[] file) {
        return file.length >= MAGIC.length && Arrays.equals(MAGIC, Arrays.copyOf(file, MAGIC.length));
    }

    static byte[] encrypt(byte[] clear, char[] password) throws Exception {
        checkPassword(password);
        if (clear.length == 0 || clear.length > MAX_CLEAR) throw new Exception("Tamaño de respaldo inválido.");
        byte[] salt = new byte[16], iv = new byte[12];
        SecureRandom random = new SecureRandom();
        random.nextBytes(salt);
        random.nextBytes(iv);
        byte[] header = ByteBuffer.allocate(HEADER).put(MAGIC).putInt(ITERATIONS).put(salt).put(iv).array();
        byte[] key = derive(password, salt);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, iv));
            cipher.updateAAD(header);
            byte[] encrypted = cipher.doFinal(clear);
            return ByteBuffer.allocate(header.length + encrypted.length).put(header).put(encrypted).array();
        } finally {
            Arrays.fill(key, (byte) 0);
        }
    }

    static byte[] decrypt(byte[] file, char[] password) throws Exception {
        checkPassword(password);
        if (!isEncrypted(file) || file.length < HEADER + 17 || file.length > MAX_FILE)
            throw new Exception("Respaldo incompleto o formato no reconocido.");
        ByteBuffer header = ByteBuffer.wrap(file, 0, HEADER);
        header.position(MAGIC.length);
        if (header.getInt() != ITERATIONS) throw new Exception("Versión de cifrado no compatible.");
        byte[] salt = new byte[16], iv = new byte[12];
        header.get(salt).get(iv);
        byte[] key = derive(password, salt);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, iv));
            cipher.updateAAD(file, 0, HEADER);
            return cipher.doFinal(file, HEADER, file.length - HEADER);
        } catch (GeneralSecurityException e) {
            throw new Exception("Contraseña incorrecta o archivo dañado.");
        } finally {
            Arrays.fill(key, (byte) 0);
        }
    }

    private static byte[] derive(char[] password, byte[] salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(password, salt, ITERATIONS, 256);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA1").generateSecret(spec).getEncoded();
        } finally { spec.clearPassword(); }
    }

    private static void checkPassword(char[] password) throws Exception {
        if (password == null || password.length < 12 || password.length > 128)
            throw new Exception("Usa una contraseña de 12 a 128 caracteres.");
    }
}
