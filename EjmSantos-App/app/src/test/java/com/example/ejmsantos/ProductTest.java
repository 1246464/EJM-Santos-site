package com.example.ejmsantos;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import com.example.ejmsantos.model.Product;

import org.junit.Test;

public class ProductTest {
    @Test
    public void exposesProductDataAndBuildsImageUrl() {
        Product product = new Product(
                7, "Mel Silvestre", "Mel artesanal", 49.90,
                "mel.webp", 3, 4.8, 12);

        assertEquals(7, product.getId());
        assertEquals("Mel Silvestre", product.getTitle());
        assertEquals(49.90, product.getPrice(), 0.001);
        assertTrue(product.getImageUrl().endsWith("/static/imagens/mel.webp"));
    }
}
