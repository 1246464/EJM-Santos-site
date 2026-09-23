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
    private final String supplierName;
    private final String brandName;
    private final String fulfillmentOriginName;
    private final boolean directShipping;
    private final int preparationDays;

    public Product(int id, String title, String description, double price, String image,
                   int stock, double rating, int reviewCount) {
        this(id, title, description, price, image, stock, rating, reviewCount,
                "", "", "", false, 0);
    }

    public Product(int id, String title, String description, double price, String image,
                   int stock, double rating, int reviewCount, String supplierName,
                   String brandName, String fulfillmentOriginName, boolean directShipping,
                   int preparationDays) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.price = price;
        this.image = image;
        this.stock = stock;
        this.rating = rating;
        this.reviewCount = reviewCount;
        this.supplierName = supplierName == null ? "" : supplierName;
        this.brandName = brandName == null ? "" : brandName;
        this.fulfillmentOriginName = fulfillmentOriginName == null ? "" : fulfillmentOriginName;
        this.directShipping = directShipping;
        this.preparationDays = Math.max(preparationDays, 0);
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
                json.optInt("n_reviews", 0),
                json.optString("supplier_name", ""),
                json.optString("brand_name", ""),
                json.optString("fulfillment_origin_name", ""),
                json.optBoolean("direct_shipping", false),
                json.optInt("preparation_days", 0)
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
                .put("n_reviews", reviewCount)
                .put("supplier_name", supplierName)
                .put("brand_name", brandName)
                .put("fulfillment_origin_name", fulfillmentOriginName)
                .put("direct_shipping", directShipping)
                .put("preparation_days", preparationDays);
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
    public String getSupplierName() { return supplierName; }
    public String getBrandName() { return brandName; }
    public String getFulfillmentOriginName() { return fulfillmentOriginName; }
    public boolean isDirectShipping() { return directShipping; }
    public int getPreparationDays() { return preparationDays; }

    public String getSellerLabel() {
        if (!brandName.isBlank()) return brandName;
        return supplierName;
    }

    public String getShippingSummary() {
        String preparation = preparationDays == 0
                ? "pronto para envio"
                : "preparo em até " + preparationDays + " dia(s) útil(eis)";
        if (directShipping) return "Envio direto do parceiro • " + preparation;
        if (!fulfillmentOriginName.isBlank()) {
            return "Sai de " + fulfillmentOriginName + " • " + preparation;
        }
        return "Entrega calculada no checkout";
    }
}
