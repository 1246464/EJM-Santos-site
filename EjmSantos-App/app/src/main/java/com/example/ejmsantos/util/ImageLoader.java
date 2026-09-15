package com.example.ejmsantos.util;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.LruCache;
import android.widget.ImageView;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class ImageLoader {
    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(4);
    private static final LruCache<String, Bitmap> CACHE = new LruCache<>(24);

    private ImageLoader() {}

    public static void load(String url, ImageView target) {
        target.setTag(url);
        if (url == null || url.isBlank()) return;
        Bitmap cached = CACHE.get(url);
        if (cached != null) {
            target.setImageBitmap(cached);
            return;
        }

        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(10_000);
                connection.setReadTimeout(12_000);
                Bitmap bitmap = BitmapFactory.decodeStream(connection.getInputStream());
                if (bitmap != null) CACHE.put(url, bitmap);
                target.post(() -> {
                    if (url.equals(target.getTag()) && bitmap != null) target.setImageBitmap(bitmap);
                });
            } catch (Exception ignored) {
                // O fundo neutro do ImageView permanece como fallback.
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }
}
