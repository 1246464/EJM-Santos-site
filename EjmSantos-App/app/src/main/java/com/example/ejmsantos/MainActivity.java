package com.example.ejmsantos;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.example.ejmsantos.data.ApiClient;
import com.example.ejmsantos.data.AuthRepository;
import com.example.ejmsantos.data.CartRepository;
import com.example.ejmsantos.data.FavoriteRepository;
import com.example.ejmsantos.model.Product;
import com.example.ejmsantos.util.ImageLoader;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.snackbar.Snackbar;
import com.google.android.material.textfield.TextInputLayout;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {
    private final NumberFormat currency = NumberFormat.getCurrencyInstance(new Locale("pt", "BR"));
    private final List<Product> products = new ArrayList<>();

    private FrameLayout contentContainer;
    private BottomNavigationView bottomNavigation;
    private CartRepository cartRepository;
    private AuthRepository authRepository;
    private FavoriteRepository favoriteRepository;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main_native);

        View root = findViewById(R.id.main);
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });

        contentContainer = findViewById(R.id.contentContainer);
        bottomNavigation = findViewById(R.id.bottomNavigation);
        cartRepository = new CartRepository(this);
        authRepository = new AuthRepository(this);
        favoriteRepository = new FavoriteRepository(this);

        bottomNavigation.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) showHome();
            else if (id == R.id.nav_cart) showCart();
            else if (id == R.id.nav_account) showAccount();
            return true;
        });

        showHome();
        updateCartBadge();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateCartBadge();
    }

    private void showHome() {
        setToolbar("EJM Santos 🍯", "Mel puro, direto do produtor");
        View screen = LayoutInflater.from(this).inflate(R.layout.screen_home, contentContainer, false);
        contentContainer.removeAllViews();
        contentContainer.addView(screen);

        EditText search = screen.findViewById(R.id.searchInput);
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterProducts(s.toString(), screen);
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        screen.findViewById(R.id.retryButton).setOnClickListener(v -> loadProducts(screen));
        if (products.isEmpty()) loadProducts(screen);
        else renderProducts(products, screen);
    }

    private void loadProducts(View screen) {
        ProgressBar progress = screen.findViewById(R.id.loadingIndicator);
        View error = screen.findViewById(R.id.errorState);
        progress.setVisibility(View.VISIBLE);
        error.setVisibility(View.GONE);

        ApiClient.getProducts(new ApiClient.Callback<>() {
            @Override public void onSuccess(List<Product> result) {
                products.clear();
                products.addAll(result);
                progress.setVisibility(View.GONE);
                renderProducts(products, screen);
            }

            @Override public void onError(String message) {
                progress.setVisibility(View.GONE);
                error.setVisibility(View.VISIBLE);
            }
        });
    }

    private void filterProducts(String query, View screen) {
        String normalized = query.trim().toLowerCase(Locale.ROOT);
        if (normalized.isEmpty()) {
            renderProducts(products, screen);
            return;
        }
        List<Product> filtered = new ArrayList<>();
        for (Product product : products) {
            String haystack = (product.getTitle() + " " + product.getDescription()).toLowerCase(Locale.ROOT);
            if (haystack.contains(normalized)) filtered.add(product);
        }
        renderProducts(filtered, screen);
    }

    private void renderProducts(List<Product> visibleProducts, View screen) {
        GridLayout grid = screen.findViewById(R.id.productGrid);
        grid.removeAllViews();

        if (visibleProducts.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("Nenhum produto encontrado");
            empty.setTextSize(16);
            empty.setPadding(dp(8), dp(24), dp(8), dp(24));
            grid.addView(empty);
            return;
        }

        for (Product product : visibleProducts) {
            MaterialCardView card = (MaterialCardView) LayoutInflater.from(this)
                    .inflate(R.layout.item_product, grid, false);
            GridLayout.LayoutParams params = new GridLayout.LayoutParams();
            params.width = 0;
            params.height = GridLayout.LayoutParams.WRAP_CONTENT;
            params.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
            params.setMargins(dp(2), dp(2), dp(2), dp(8));
            card.setLayoutParams(params);

            ImageView image = card.findViewById(R.id.productImage);
            TextView title = card.findViewById(R.id.productTitle);
            TextView price = card.findViewById(R.id.productPrice);
            TextView rating = card.findViewById(R.id.productRating);
            TextView stock = card.findViewById(R.id.productStock);
            MaterialButton add = card.findViewById(R.id.addButton);
            MaterialButton favorite = card.findViewById(R.id.favoriteButton);

            title.setText(product.getTitle());
            price.setText(currency.format(product.getPrice()));
            rating.setText(product.getReviewCount() == 0
                    ? "Novo na loja" : String.format(Locale.getDefault(), "★ %.1f  (%d)", product.getRating(), product.getReviewCount()));
            stock.setText(product.getStock() > 0 ? "Em estoque" : "Produto esgotado");
            add.setEnabled(product.getStock() > 0);
            favorite.setText(favoriteRepository.contains(product.getId()) ? "♥" : "♡");
            ImageLoader.load(product.getImageUrl(), image);

            card.setOnClickListener(v -> openProduct(product));
            add.setOnClickListener(v -> addToCart(product));
            favorite.setOnClickListener(v -> {
                boolean selected = favoriteRepository.toggle(product.getId());
                favorite.setText(selected ? "♥" : "♡");
                Snackbar.make(contentContainer,
                        selected ? "Adicionado aos favoritos" : "Removido dos favoritos",
                        Snackbar.LENGTH_SHORT).show();
            });
            grid.addView(card);
        }
    }

    private void openProduct(Product product) {
        Intent intent = new Intent(this, ProductDetailActivity.class);
        intent.putExtra(ProductDetailActivity.EXTRA_PRODUCT, product);
        startActivity(intent);
    }

    private void addToCart(Product product) {
        if (cartRepository.add(product)) {
            updateCartBadge();
            Snackbar.make(contentContainer, product.getTitle() + " adicionado ao carrinho", Snackbar.LENGTH_SHORT).show();
        } else {
            Snackbar.make(contentContainer, "Quantidade máxima disponível atingida", Snackbar.LENGTH_SHORT).show();
        }
    }

    private void showCart() {
        setToolbar("Carrinho", "Revise os itens da sua compra");
        View screen = LayoutInflater.from(this).inflate(R.layout.screen_cart, contentContainer, false);
        contentContainer.removeAllViews();
        contentContainer.addView(screen);

        LinearLayout container = screen.findViewById(R.id.cartItemsContainer);
        TextView empty = screen.findViewById(R.id.emptyCartText);
        TextView total = screen.findViewById(R.id.cartTotal);
        View summary = screen.findViewById(R.id.cartSummary);
        List<CartRepository.Entry> items = cartRepository.getItems();

        empty.setVisibility(items.isEmpty() ? View.VISIBLE : View.GONE);
        ((View) container.getParent()).setVisibility(items.isEmpty() ? View.GONE : View.VISIBLE);
        summary.setVisibility(items.isEmpty() ? View.GONE : View.VISIBLE);

        for (CartRepository.Entry entry : items) {
            View row = LayoutInflater.from(this).inflate(R.layout.item_cart, container, false);
            ImageLoader.load(entry.product.getImageUrl(), row.findViewById(R.id.cartItemImage));
            ((TextView) row.findViewById(R.id.cartItemTitle)).setText(entry.product.getTitle());
            ((TextView) row.findViewById(R.id.cartItemPrice)).setText(currency.format(entry.subtotal()));
            ((TextView) row.findViewById(R.id.cartItemQuantity)).setText(String.valueOf(entry.quantity));
            row.findViewById(R.id.decreaseButton).setOnClickListener(v -> {
                cartRepository.setQuantity(entry.product.getId(), entry.quantity - 1);
                updateCartBadge();
                showCart();
            });
            row.findViewById(R.id.increaseButton).setOnClickListener(v -> {
                cartRepository.setQuantity(entry.product.getId(), entry.quantity + 1);
                updateCartBadge();
                showCart();
            });
            row.findViewById(R.id.removeButton).setOnClickListener(v -> {
                cartRepository.remove(entry.product.getId());
                updateCartBadge();
                showCart();
            });
            container.addView(row);
        }

        total.setText("Total: " + currency.format(cartRepository.getTotal()));
        screen.findViewById(R.id.checkoutButton).setOnClickListener(v -> continueCheckout());
    }

    private void continueCheckout() {
        if (!authRepository.isLoggedIn()) {
            bottomNavigation.setSelectedItemId(R.id.nav_account);
            Snackbar.make(contentContainer, "Entre na sua conta para continuar", Snackbar.LENGTH_LONG).show();
            return;
        }
        startActivity(new Intent(this, CheckoutActivity.class));
    }

    private void showAccount() {
        setToolbar("Minha conta", "Acompanhe sua experiência EJM Santos");
        View screen = LayoutInflater.from(this).inflate(R.layout.screen_account, contentContainer, false);
        contentContainer.removeAllViews();
        contentContainer.addView(screen);

        View loggedOut = screen.findViewById(R.id.loggedOutSection);
        View loggedIn = screen.findViewById(R.id.loggedInSection);
        if (authRepository.isLoggedIn()) {
            loggedOut.setVisibility(View.GONE);
            loggedIn.setVisibility(View.VISIBLE);
            ((TextView) screen.findViewById(R.id.profileName)).setText(authRepository.getName());
            ((TextView) screen.findViewById(R.id.profileEmail)).setText(authRepository.getEmail());
            screen.findViewById(R.id.addAddressButton).setOnClickListener(v -> showAddressDialog(screen));
            screen.findViewById(R.id.logoutButton).setOnClickListener(v -> {
                authRepository.logout();
                showAccount();
            });
            loadAccountData(screen);
            return;
        }

        loggedOut.setVisibility(View.VISIBLE);
        loggedIn.setVisibility(View.GONE);
        bindAuthForm(screen);
    }

    private void bindAuthForm(View screen) {
        TextInputLayout nameLayout = screen.findViewById(R.id.nameLayout);
        EditText nameInput = screen.findViewById(R.id.nameInput);
        EditText emailInput = screen.findViewById(R.id.emailInput);
        EditText passwordInput = screen.findViewById(R.id.passwordInput);
        TextView authTitle = screen.findViewById(R.id.authTitle);
        MaterialButton authButton = screen.findViewById(R.id.authButton);
        Button toggle = screen.findViewById(R.id.toggleAuthMode);
        ProgressBar progress = screen.findViewById(R.id.authProgress);
        final boolean[] registerMode = {false};

        toggle.setOnClickListener(v -> {
            registerMode[0] = !registerMode[0];
            nameLayout.setVisibility(registerMode[0] ? View.VISIBLE : View.GONE);
            authTitle.setText(registerMode[0] ? "Crie sua conta" : "Entre para acompanhar seus pedidos");
            authButton.setText(registerMode[0] ? "Criar conta" : "Entrar");
            toggle.setText(registerMode[0] ? "Já tenho uma conta" : "Ainda não tenho conta");
        });

        authButton.setOnClickListener(v -> {
            String name = nameInput.getText() == null ? "" : nameInput.getText().toString().trim();
            String email = emailInput.getText() == null ? "" : emailInput.getText().toString().trim();
            String password = passwordInput.getText() == null ? "" : passwordInput.getText().toString();
            if (email.isEmpty() || password.isEmpty() || (registerMode[0] && name.length() < 3)) {
                Snackbar.make(contentContainer, "Preencha todos os campos corretamente", Snackbar.LENGTH_LONG).show();
                return;
            }

            progress.setVisibility(View.VISIBLE);
            authButton.setEnabled(false);
            ApiClient.Callback<JSONObject> callback = new ApiClient.Callback<>() {
                @Override public void onSuccess(JSONObject result) {
                    authRepository.saveSession(result);
                    showAccount();
                    Snackbar.make(contentContainer, "Bem-vindo à EJM Santos!", Snackbar.LENGTH_SHORT).show();
                }

                @Override public void onError(String message) {
                    progress.setVisibility(View.GONE);
                    authButton.setEnabled(true);
                    Snackbar.make(contentContainer, message, Snackbar.LENGTH_LONG).show();
                }
            };

            if (registerMode[0]) ApiClient.register(name, email, password, callback);
            else ApiClient.login(email, password, callback);
        });
    }

    private void loadAccountData(View screen) {
        ProgressBar progress = screen.findViewById(R.id.accountDataProgress);
        progress.setVisibility(View.VISIBLE);
        String token = authRepository.getToken();

        ApiClient.getAddresses(token, new ApiClient.Callback<>() {
            @Override public void onSuccess(JSONObject result) {
                renderAddresses(screen, result.optJSONArray("addresses"));
                progress.setVisibility(View.GONE);
            }

            @Override public void onError(String message) {
                progress.setVisibility(View.GONE);
                Snackbar.make(contentContainer, message, Snackbar.LENGTH_LONG).show();
            }
        });

        ApiClient.getOrders(token, new ApiClient.Callback<>() {
            @Override public void onSuccess(JSONObject result) {
                renderOrders(screen, result.optJSONArray("orders"));
                progress.setVisibility(View.GONE);
            }

            @Override public void onError(String message) {
                progress.setVisibility(View.GONE);
                Snackbar.make(contentContainer, message, Snackbar.LENGTH_LONG).show();
            }
        });
    }

    private void renderAddresses(View screen, JSONArray addresses) {
        LinearLayout container = screen.findViewById(R.id.addressContainer);
        container.removeAllViews();
        if (addresses == null || addresses.length() == 0) {
            addEmptyMessage(container, "Nenhum endereço salvo.");
            return;
        }

        for (int i = 0; i < addresses.length(); i++) {
            JSONObject address = addresses.optJSONObject(i);
            if (address == null) continue;
            View item = LayoutInflater.from(this).inflate(R.layout.item_address, container, false);
            boolean isDefault = address.optBoolean("is_default");
            int addressId = address.optInt("id");
            ((TextView) item.findViewById(R.id.addressLabel)).setText(
                    address.optString("apelido") + (isDefault ? "  •  Padrão" : ""));
            ((TextView) item.findViewById(R.id.addressText)).setText(address.optString("endereco_completo"));

            MaterialButton action = item.findViewById(R.id.addressAction);
            action.setText(isDefault ? "Em uso" : "Usar");
            action.setEnabled(!isDefault);
            action.setOnClickListener(v -> ApiClient.setDefaultAddress(
                    authRepository.getToken(), addressId, refreshAccountCallback()));
            item.findViewById(R.id.addressDelete).setOnClickListener(v -> new AlertDialog.Builder(this)
                    .setTitle("Remover endereço?")
                    .setMessage(address.optString("apelido"))
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Remover", (dialog, which) -> ApiClient.deleteAddress(
                            authRepository.getToken(), addressId, refreshAccountCallback()))
                    .show());
            container.addView(item);
        }
    }

    private void renderOrders(View screen, JSONArray orders) {
        LinearLayout container = screen.findViewById(R.id.orderContainer);
        container.removeAllViews();
        if (orders == null || orders.length() == 0) {
            addEmptyMessage(container, "Você ainda não fez nenhum pedido.");
            return;
        }

        for (int i = 0; i < orders.length(); i++) {
            JSONObject order = orders.optJSONObject(i);
            if (order == null) continue;
            View item = LayoutInflater.from(this).inflate(R.layout.item_order, container, false);
            ((TextView) item.findViewById(R.id.orderNumber)).setText("Pedido #" + order.optInt("id"));
            ((TextView) item.findViewById(R.id.orderStatus)).setText(order.optString("status", "Pendente"));
            ((TextView) item.findViewById(R.id.orderTotal)).setText(
                    "Total: " + currency.format(order.optDouble("total", 0)));

            JSONArray orderItems = order.optJSONArray("items");
            StringBuilder names = new StringBuilder();
            if (orderItems != null) {
                for (int index = 0; index < orderItems.length(); index++) {
                    JSONObject product = orderItems.optJSONObject(index) == null
                            ? null : orderItems.optJSONObject(index).optJSONObject("produto");
                    if (product != null) {
                        if (names.length() > 0) names.append(", ");
                        names.append(product.optString("titulo"));
                    }
                }
            }
            ((TextView) item.findViewById(R.id.orderItems)).setText(
                    names.length() == 0 ? "Itens do pedido" : names.toString());
            container.addView(item);
        }
    }

    private void showAddressDialog(View accountScreen) {
        View form = LayoutInflater.from(this).inflate(R.layout.dialog_address, null, false);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Novo endereço")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar", null)
                .create();

        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            JSONObject address = new JSONObject();
            try {
                address.put("apelido", inputValue(form, R.id.addressNicknameInput));
                address.put("rua", inputValue(form, R.id.addressStreetInput));
                address.put("numero", inputValue(form, R.id.addressNumberInput));
                address.put("bairro", inputValue(form, R.id.addressDistrictInput));
                address.put("cidade", inputValue(form, R.id.addressCityInput));
                address.put("estado", inputValue(form, R.id.addressStateInput));
                address.put("cep", inputValue(form, R.id.addressZipInput));
                address.put("telefone", inputValue(form, R.id.addressPhoneInput));
            } catch (Exception ignoredJsonError) {}

            ApiClient.createAddress(authRepository.getToken(), address, new ApiClient.Callback<>() {
                @Override public void onSuccess(JSONObject result) {
                    dialog.dismiss();
                    loadAccountData(accountScreen);
                    Snackbar.make(contentContainer, "Endereço salvo", Snackbar.LENGTH_SHORT).show();
                }

                @Override public void onError(String message) {
                    Snackbar.make(form, message, Snackbar.LENGTH_LONG).show();
                }
            });
        }));
        dialog.show();
    }

    private ApiClient.Callback<JSONObject> refreshAccountCallback() {
        return new ApiClient.Callback<>() {
            @Override public void onSuccess(JSONObject result) { showAccount(); }
            @Override public void onError(String message) {
                Snackbar.make(contentContainer, message, Snackbar.LENGTH_LONG).show();
            }
        };
    }

    private String inputValue(View root, int id) {
        EditText input = root.findViewById(id);
        return input.getText() == null ? "" : input.getText().toString().trim();
    }

    private void addEmptyMessage(LinearLayout container, String message) {
        TextView empty = new TextView(this);
        empty.setText(message);
        empty.setTextColor(getColor(R.color.text_secondary));
        empty.setTextSize(15);
        empty.setPadding(0, dp(10), 0, dp(10));
        container.addView(empty);
    }

    private void updateCartBadge() {
        if (bottomNavigation == null) return;
        int count = cartRepository == null ? 0 : cartRepository.getItemCount();
        if (count > 0) {
            bottomNavigation.getOrCreateBadge(R.id.nav_cart).setNumber(count);
        } else {
            bottomNavigation.removeBadge(R.id.nav_cart);
        }
    }

    private void setToolbar(String title, String subtitle) {
        com.google.android.material.appbar.MaterialToolbar toolbar = findViewById(R.id.toolbar);
        toolbar.setTitle(title);
        toolbar.setSubtitle(subtitle);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
