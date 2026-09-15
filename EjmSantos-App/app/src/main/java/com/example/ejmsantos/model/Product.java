package com.example.ejmsantos.model;

import com.example.ejmsantos.BuildConfig;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.Serializable;

public class Product implements Serializable {
    private final int id;
    private final String title;
    private final String description;
    private final double price;
    private final String image;
    private final int stock;
    private final double rating;
    private final int reviewCount;

    public Product(int id, String title, String description, double price, String image,
                   int stock, double rating, int reviewCount) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.price = price;
        this.image = image;
        this.stock = stock;
        this.rating = rating;
        this.reviewCount = reviewCount;
    }

    public static Product fromJson(JSONObject json) throws JSONException {
        return new Product(
                json.getInt("id"),
                json.optString("titulo", "Produto"),
                json.optString("descricao", ""),
                json.optDouble("preco", 0),
                json.optString("imagem", ""),
                json.optInt("estoque", 0),
                json.optDouble("media", 0),
                json.optInt("n_reviews", 0)
        );
    }

    public JSONObject toJson() throws JSONException {
        return new JSONObject()
                .put("id", id)
                .put("titulo", title)
                .put("descricao", description)
                .put("preco", price)
                .put("imagem", image)
                .put("estoque", stock)
                .put("media", rating)
                .put("n_reviews", reviewCount);
    }

    public String getImageUrl() {
        if (image == null || image.isBlank()) return "";
        if (image.startsWith("http://") || image.startsWith("https://")) return image;
        String clean = image.startsWith("imagens/") ? image.substring(8) : image;
        while (clean.startsWith("/")) clean = clean.substring(1);
        return BuildConfig.API_BASE_URL + "static/imagens/" + clean;
    }

    public int getId() { return id; }
    public String getTitle() { return title; }
    public String getDescription() { return description; }
    public double getPrice() { return price; }
    public int getStock() { return stock; }
    public double getRating() { return rating; }
    public int getReviewCount() { return reviewCount; }
}
