package com.example.ejmsantos.data;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.HashSet;
import java.util.Collections;
import java.util.Set;

public class FavoriteRepository {
    private static final String PREFS = "ejm_favorites";
    private static final String KEY_IDS = "product_ids";
    private final SharedPreferences preferences;

    public FavoriteRepository(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public boolean contains(int productId) {
        return preferences.getStringSet(KEY_IDS, Collections.emptySet()).contains(String.valueOf(productId));
    }

    public boolean toggle(int productId) {
        Set<String> ids = new HashSet<>(preferences.getStringSet(KEY_IDS, Collections.emptySet()));
        String value = String.valueOf(productId);
        boolean favorite;
        if (ids.contains(value)) {
            ids.remove(value);
            favorite = false;
        } else {
            ids.add(value);
            favorite = true;
        }
        preferences.edit().putStringSet(KEY_IDS, ids).apply();
        return favorite;
    }
}
