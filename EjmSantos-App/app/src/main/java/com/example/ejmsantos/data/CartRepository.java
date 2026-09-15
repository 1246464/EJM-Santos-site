package com.example.ejmsantos.data;

import android.content.Context;
import android.content.SharedPreferences;

import com.example.ejmsantos.model.Product;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class CartRepository {
    public static class Entry {
        public final Product product;
        public int quantity;

        Entry(Product product, int quantity) {
            this.product = product;
            this.quantity = quantity;
        }

        public double subtotal() { return product.getPrice() * quantity; }
    }

    private static final String PREFS = "ejm_cart";
    private static final String KEY_ITEMS = "items";
    private final SharedPreferences preferences;

    public CartRepository(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public synchronized List<Entry> getItems() {
        List<Entry> items = new ArrayList<>();
        try {
            JSONArray array = new JSONArray(preferences.getString(KEY_ITEMS, "[]"));
            for (int i = 0; i < array.length(); i++) {
                JSONObject item = array.getJSONObject(i);
                items.add(new Entry(Product.fromJson(item.getJSONObject("product")),
                        item.optInt("quantity", 1)));
            }
        } catch (Exception ignored) {
            preferences.edit().remove(KEY_ITEMS).apply();
        }
        return items;
    }

    public synchronized boolean add(Product product) {
        return addQuantity(product, 1) == 1;
    }

    public synchronized int addQuantity(Product product, int requestedQuantity) {
        if (requestedQuantity <= 0 || product.getStock() <= 0) return 0;
        List<Entry> items = getItems();
        for (Entry entry : items) {
            if (entry.product.getId() == product.getId()) {
                int added = Math.min(requestedQuantity, product.getStock() - entry.quantity);
                if (added <= 0) return 0;
                entry.quantity += added;
                save(items);
                return added;
            }
        }
        int added = Math.min(requestedQuantity, product.getStock());
        items.add(new Entry(product, added));
        save(items);
        return added;
    }

    public synchronized void setQuantity(int productId, int quantity) {
        List<Entry> items = getItems();
        for (int i = 0; i < items.size(); i++) {
            Entry entry = items.get(i);
            if (entry.product.getId() == productId) {
                if (quantity <= 0) items.remove(i);
                else entry.quantity = Math.min(quantity, entry.product.getStock());
                break;
            }
        }
        save(items);
    }

    public synchronized void remove(int productId) { setQuantity(productId, 0); }

    public int getItemCount() {
        int count = 0;
        for (Entry entry : getItems()) count += entry.quantity;
        return count;
    }

    public double getTotal() {
        double total = 0;
        for (Entry entry : getItems()) total += entry.subtotal();
        return total;
    }

    public JSONArray toCheckoutJson() {
        JSONArray result = new JSONArray();
        try {
            for (Entry entry : getItems()) {
                result.put(new JSONObject()
                        .put("product_id", entry.product.getId())
                        .put("quantity", entry.quantity));
            }
        } catch (Exception ignored) {}
        return result;
    }

    public void clear() {
        preferences.edit().remove(KEY_ITEMS).apply();
    }

    private void save(List<Entry> items) {
        JSONArray array = new JSONArray();
        try {
            for (Entry entry : items) {
                array.put(new JSONObject()
                        .put("product", entry.product.toJson())
                        .put("quantity", entry.quantity));
            }
            preferences.edit().putString(KEY_ITEMS, array.toString()).apply();
        } catch (Exception ignored) {}
    }
}
