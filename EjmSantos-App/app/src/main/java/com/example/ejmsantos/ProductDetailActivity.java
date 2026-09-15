package com.example.ejmsantos;

import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.example.ejmsantos.data.CartRepository;
import com.example.ejmsantos.data.FavoriteRepository;
import com.example.ejmsantos.model.Product;
import com.example.ejmsantos.util.ImageLoader;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;

import java.text.NumberFormat;
import java.util.Locale;

public class ProductDetailActivity extends AppCompatActivity {
    public static final String EXTRA_PRODUCT = "product";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_product_detail);

        Product product = (Product) getIntent().getSerializableExtra(EXTRA_PRODUCT);
        if (product == null) {
            finish();
            return;
        }

        com.google.android.material.appbar.MaterialToolbar toolbar = findViewById(R.id.detailToolbar);
        toolbar.setNavigationOnClickListener(v -> finish());
        FavoriteRepository favorites = new FavoriteRepository(this);
        android.view.MenuItem favoriteItem = toolbar.getMenu().add(
                favorites.contains(product.getId()) ? "♥" : "♡");
        favoriteItem.setShowAsAction(android.view.MenuItem.SHOW_AS_ACTION_ALWAYS);
        favoriteItem.setOnMenuItemClickListener(item -> {
            boolean selected = favorites.toggle(product.getId());
            item.setTitle(selected ? "♥" : "♡");
            Snackbar.make(toolbar, selected ? "Adicionado aos favoritos" : "Removido dos favoritos", Snackbar.LENGTH_SHORT).show();
            return true;
        });

        ImageView image = findViewById(R.id.detailImage);
        ((TextView) findViewById(R.id.detailTitle)).setText(product.getTitle());
        ((TextView) findViewById(R.id.detailDescription)).setText(
                product.getDescription().isBlank() ? "Mel artesanal selecionado pela EJM Santos." : product.getDescription());
        ((TextView) findViewById(R.id.detailPrice)).setText(
                NumberFormat.getCurrencyInstance(new Locale("pt", "BR")).format(product.getPrice()));
        ((TextView) findViewById(R.id.detailRating)).setText(product.getReviewCount() == 0
                ? "Produto novo" : String.format(Locale.getDefault(), "★ %.1f  •  %d avaliações", product.getRating(), product.getReviewCount()));
        ((TextView) findViewById(R.id.detailStock)).setText(
                product.getStock() > 0 ? product.getStock() + " unidades disponíveis" : "Produto esgotado");
        ImageLoader.load(product.getImageUrl(), image);

        MaterialButton addButton = findViewById(R.id.detailAddButton);
        addButton.setEnabled(product.getStock() > 0);
        addButton.setOnClickListener(v -> {
            CartRepository cart = new CartRepository(this);
            if (cart.add(product)) {
                Snackbar.make(addButton, "Produto adicionado ao carrinho", Snackbar.LENGTH_SHORT).show();
            } else {
                Snackbar.make(addButton, "Quantidade máxima disponível atingida", Snackbar.LENGTH_LONG).show();
            }
        });
    }
}
