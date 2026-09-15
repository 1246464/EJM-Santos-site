package com.example.ejmsantos.data;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public class AuthRepository {
    private static final String PREFS = "ejm_auth";
    private static final String KEY_TOKEN = "token_encrypted";
    private static final String LEGACY_TOKEN = "token";
    private static final String KEY_ALIAS = "ejm_mobile_session_key";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private final SharedPreferences preferences;

    public AuthRepository(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public boolean saveSession(JSONObject response) {
        JSONObject user = response.optJSONObject("user");
        String token = response.optString("token");
        if (user == null || token.isBlank()) return false;
        try {
            preferences.edit()
                    .putString(KEY_TOKEN, encrypt(token))
                    .remove(LEGACY_TOKEN)
                    .putString("name", user.optString("nome"))
                    .putString("email", user.optString("email"))
                    .apply();
            return true;
        } catch (Exception exception) {
            preferences.edit().remove(KEY_TOKEN).remove(LEGACY_TOKEN).apply();
            return false;
        }
    }

    public boolean isLoggedIn() { return !getToken().isBlank(); }
    public String getToken() {
        String encrypted = preferences.getString(KEY_TOKEN, "");
        if (!encrypted.isBlank()) {
            try {
                return decrypt(encrypted);
            } catch (Exception exception) {
                preferences.edit().remove(KEY_TOKEN).apply();
                return "";
            }
        }

        // Migra automaticamente sessões criadas pelas versões anteriores.
        String legacy = preferences.getString(LEGACY_TOKEN, "");
        if (!legacy.isBlank()) {
            try {
                preferences.edit().putString(KEY_TOKEN, encrypt(legacy))
                        .remove(LEGACY_TOKEN).apply();
                return legacy;
            } catch (Exception exception) {
                preferences.edit().remove(LEGACY_TOKEN).apply();
            }
        }
        return "";
    }
    public String getName() { return preferences.getString("name", ""); }
    public String getEmail() { return preferences.getString("email", ""); }
    public void logout() { preferences.edit().clear().apply(); }

    private String encrypt(String value) throws Exception {
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        String iv = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP);
        String payload = Base64.encodeToString(
                cipher.doFinal(value.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
        return iv + ":" + payload;
    }

    private String decrypt(String value) throws Exception {
        String[] parts = value.split(":", 2);
        if (parts.length != 2) throw new IllegalArgumentException("Sessão inválida");
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(
                Cipher.DECRYPT_MODE,
                getOrCreateKey(),
                new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
        byte[] clear = cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP));
        return new String(clear, StandardCharsets.UTF_8);
    }

    private SecretKey getOrCreateKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        java.security.Key existing = keyStore.getKey(KEY_ALIAS, null);
        if (existing instanceof SecretKey) return (SecretKey) existing;

        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .build());
        return generator.generateKey();
    }
}
