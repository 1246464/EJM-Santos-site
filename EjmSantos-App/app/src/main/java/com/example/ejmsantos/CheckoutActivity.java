package com.example.ejmsantos;

import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import com.example.ejmsantos.data.ApiClient;
import com.example.ejmsantos.data.AuthRepository;
import com.example.ejmsantos.data.CartRepository;
import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;
import com.stripe.android.PaymentConfiguration;
import com.stripe.android.paymentsheet.PaymentSheet;
import com.stripe.android.paymentsheet.PaymentSheetResult;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public class CheckoutActivity extends AppCompatActivity {
    private static final String STATE_CLIENT_REFERENCE = "client_reference";
    private static final String STATE_STRIPE_ORDER_ID = "stripe_order_id";
    private final NumberFormat currency = NumberFormat.getCurrencyInstance(new Locale("pt", "BR"));
    private String clientReference;

    private AuthRepository authRepository;
    private CartRepository cartRepository;
    private Spinner addressSpinner;
    private TextView addressEmpty;
    private TextView subtotalText;
    private TextView deliveryText;
    private TextView totalText;
    private ProgressBar progress;
    private MaterialButton placeOrderButton;
    private RadioButton cashPayment;
    private RadioButton stripePayment;
    private PaymentSheet paymentSheet;
    private JSONArray addresses = new JSONArray();
    private int selectedAddressId = -1;
    private int quoteGeneration = 0;
    private int pendingStripeOrderId = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_checkout);

        clientReference = savedInstanceState == null
                ? UUID.randomUUID().toString()
                : savedInstanceState.getString(STATE_CLIENT_REFERENCE, UUID.randomUUID().toString());
        pendingStripeOrderId = savedInstanceState == null
                ? 0 : savedInstanceState.getInt(STATE_STRIPE_ORDER_ID, 0);

        authRepository = new AuthRepository(this);
        cartRepository = new CartRepository(this);
        addressSpinner = findViewById(R.id.checkoutAddressSpinner);
        addressEmpty = findViewById(R.id.checkoutAddressEmpty);
        subtotalText = findViewById(R.id.checkoutSubtotal);
        deliveryText = findViewById(R.id.checkoutDelivery);
        totalText = findViewById(R.id.checkoutTotal);
        progress = findViewById(R.id.checkoutProgress);
        placeOrderButton = findViewById(R.id.placeOrderButton);
        cashPayment = findViewById(R.id.cashPayment);
        stripePayment = findViewById(R.id.stripePayment);
        paymentSheet = new PaymentSheet.Builder(this::onPaymentSheetResult).build(this);

        MaterialToolbar toolbar = findViewById(R.id.checkoutToolbar);
        toolbar.setNavigationOnClickListener(v -> finish());
        findViewById(R.id.checkoutBackToAccount).setOnClickListener(v -> {
            Toast.makeText(this, "Abra Conta e cadastre um endereço", Toast.LENGTH_LONG).show();
            finish();
        });
        placeOrderButton.setOnClickListener(v -> placeOrder());
        ((android.widget.RadioGroup) findViewById(R.id.paymentMethodGroup))
                .setOnCheckedChangeListener((group, checkedId) -> placeOrderButton.setText(
                        checkedId == R.id.stripePayment ? "Pagar com cartão" : "Confirmar pedido"));

        if (!authRepository.isLoggedIn() || cartRepository.getItems().isEmpty()) {
            finish();
            return;
        }
        loadAddresses();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        outState.putString(STATE_CLIENT_REFERENCE, clientReference);
        outState.putInt(STATE_STRIPE_ORDER_ID, pendingStripeOrderId);
        super.onSaveInstanceState(outState);
    }

    private void loadAddresses() {
        setLoading(true);
        ApiClient.getAddresses(authRepository.getToken(), new ApiClient.Callback<>() {
            @Override public void onSuccess(JSONObject result) {
                addresses = result.optJSONArray("addresses");
                if (addresses == null) addresses = new JSONArray();
                renderAddresses();
            }

            @Override public void onError(String message) {
                setLoading(false);
                Snackbar.make(findViewById(R.id.checkoutRoot), message, Snackbar.LENGTH_LONG).show();
            }
        });
    }

    private void renderAddresses() {
        if (addresses.length() == 0) {
            addressSpinner.setVisibility(View.GONE);
            addressEmpty.setVisibility(View.VISIBLE);
            findViewById(R.id.checkoutBackToAccount).setVisibility(View.VISIBLE);
            findViewById(R.id.checkoutSummaryCard).setVisibility(View.GONE);
            placeOrderButton.setEnabled(false);
            setLoading(false);
            return;
        }

        List<String> labels = new ArrayList<>();
        int defaultPosition = 0;
        for (int index = 0; index < addresses.length(); index++) {
            JSONObject address = addresses.optJSONObject(index);
            if (address == null) continue;
            labels.add(address.optString("apelido") + " — " + address.optString("endereco_completo"));
            if (address.optBoolean("is_default")) defaultPosition = index;
        }

        ArrayAdapter<String> adapter = new ArrayAdapter<>(
                this, android.R.layout.simple_spinner_item, labels);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        addressSpinner.setAdapter(adapter);
        addressSpinner.setSelection(defaultPosition);
        addressSpinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(android.widget.AdapterView<?> parent, View view,
                                                  int position, long id) {
                JSONObject address = addresses.optJSONObject(position);
                selectedAddressId = address == null ? -1 : address.optInt("id", -1);
                loadQuote();
            }

            @Override public void onNothingSelected(android.widget.AdapterView<?> parent) {
                selectedAddressId = -1;
                placeOrderButton.setEnabled(false);
            }
        });
        loadQuote();
    }

    private void loadQuote() {
        if (selectedAddressId <= 0) {
            JSONObject first = addresses.optJSONObject(0);
            selectedAddressId = first == null ? -1 : first.optInt("id", -1);
        }
        if (selectedAddressId <= 0) return;

        int generation = ++quoteGeneration;
        setLoading(true);
        ApiClient.getCheckoutQuote(
                authRepository.getToken(), selectedAddressId, cartRepository.toCheckoutJson(),
                new ApiClient.Callback<>() {
                    @Override public void onSuccess(JSONObject quote) {
                        if (generation != quoteGeneration) return;
                        subtotalText.setText(currency.format(quote.optDouble("subtotal")));
                        deliveryText.setText(String.format(
                                Locale.getDefault(), "%s (%.1f km)",
                                currency.format(quote.optDouble("delivery_fee")),
                                quote.optDouble("delivery_distance_km")));
                        totalText.setText(currency.format(quote.optDouble("total")));
                        JSONArray methods = quote.optJSONArray("payment_methods");
                        boolean stripeEnabled = false;
                        if (methods != null) {
                            for (int index = 0; index < methods.length(); index++) {
                                if ("stripe".equals(methods.optString(index))) {
                                    stripeEnabled = true;
                                    break;
                                }
                            }
                        }
                        stripePayment.setVisibility(stripeEnabled ? View.VISIBLE : View.GONE);
                        if (!stripeEnabled) cashPayment.setChecked(true);
                        findViewById(R.id.checkoutSummaryCard).setVisibility(View.VISIBLE);
                        setLoading(false);
                    }

                    @Override public void onError(String message) {
                        if (generation != quoteGeneration) return;
                        setLoading(false);
                        placeOrderButton.setEnabled(false);
                        Snackbar.make(findViewById(R.id.checkoutRoot), message, Snackbar.LENGTH_LONG).show();
                    }
                });
    }

    private void placeOrder() {
        if (selectedAddressId <= 0) return;
        if (stripePayment.isChecked()) {
            startStripePayment();
            return;
        }
        setLoading(true);
        ApiClient.createOrder(
                authRepository.getToken(), selectedAddressId, cartRepository.toCheckoutJson(),
                clientReference, new ApiClient.Callback<>() {
                    @Override public void onSuccess(JSONObject result) {
                        JSONObject order = result.optJSONObject("order");
                        int orderId = order == null ? 0 : order.optInt("id");
                        setLoading(false);
                        finishOrder(orderId,
                                "Pedido confirmado. O pagamento será feito no recebimento.");
                    }

                    @Override public void onError(String message) {
                        setLoading(false);
                        Snackbar.make(findViewById(R.id.checkoutRoot), message, Snackbar.LENGTH_LONG).show();
                    }
                });
    }

    private void startStripePayment() {
        setLoading(true);
        ApiClient.createStripePaymentIntent(
                authRepository.getToken(), selectedAddressId, cartRepository.toCheckoutJson(),
                clientReference, new ApiClient.Callback<>() {
                    @Override public void onSuccess(JSONObject result) {
                        String publishableKey = result.optString("publishable_key");
                        String clientSecret = result.optString("client_secret");
                        JSONObject order = result.optJSONObject("order");
                        pendingStripeOrderId = order == null ? 0 : order.optInt("id");
                        if (publishableKey.isBlank() || clientSecret.isBlank()) {
                            setLoading(false);
                            Snackbar.make(findViewById(R.id.checkoutRoot),
                                    "O Stripe retornou uma configuração incompleta",
                                    Snackbar.LENGTH_LONG).show();
                            return;
                        }

                        PaymentConfiguration.init(getApplicationContext(), publishableKey);
                        setLoading(false);
                        paymentSheet.presentWithPaymentIntent(
                                clientSecret,
                                new PaymentSheet.Configuration.Builder("EJM Santos").build());
                    }

                    @Override public void onError(String message) {
                        setLoading(false);
                        Snackbar.make(findViewById(R.id.checkoutRoot), message, Snackbar.LENGTH_LONG).show();
                    }
                });
    }

    private void onPaymentSheetResult(PaymentSheetResult result) {
        if (result instanceof PaymentSheetResult.Completed) {
            finishOrder(pendingStripeOrderId,
                    "Pagamento enviado. A confirmação segura será atualizada pelo Stripe.");
        } else if (result instanceof PaymentSheetResult.Failed) {
            Throwable error = ((PaymentSheetResult.Failed) result).getError();
            Snackbar.make(findViewById(R.id.checkoutRoot),
                    error.getLocalizedMessage() == null
                            ? "Não foi possível concluir o pagamento"
                            : error.getLocalizedMessage(),
                    Snackbar.LENGTH_LONG).show();
        }
    }

    private void finishOrder(int orderId, String message) {
        cartRepository.clear();
        new AlertDialog.Builder(this)
                .setTitle("Pedido recebido 🍯")
                .setMessage("Pedido #" + orderId + "\n\n" + message)
                .setCancelable(false)
                .setPositiveButton("Continuar", (dialog, which) -> finish())
                .show();
    }

    private void setLoading(boolean loading) {
        progress.setVisibility(loading ? View.VISIBLE : View.GONE);
        addressSpinner.setEnabled(!loading);
        placeOrderButton.setEnabled(!loading && selectedAddressId > 0);
    }
}
