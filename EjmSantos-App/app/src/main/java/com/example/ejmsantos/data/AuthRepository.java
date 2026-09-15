package com.example.ejmsantos.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

public class AuthRepository {
    private static final String PREFS = "ejm_auth";
    private final SharedPreferences preferences;

    public AuthRepository(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public void saveSession(JSONObject response) {
        JSONObject user = response.optJSONObject("user");
        if (user == null) return;
        preferences.edit()
                .putString("token", response.optString("token"))
                .putString("name", user.optString("nome"))
                .putString("email", user.optString("email"))
                .apply();
    }

    public boolean isLoggedIn() { return !getToken().isBlank(); }
    public String getToken() { return preferences.getString("token", ""); }
    public String getName() { return preferences.getString("name", ""); }
    public String getEmail() { return preferences.getString("email", ""); }
    public void logout() { preferences.edit().clear().apply(); }
}
