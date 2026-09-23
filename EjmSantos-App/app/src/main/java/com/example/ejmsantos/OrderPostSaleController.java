package com.example.ejmsantos;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import com.example.ejmsantos.data.ApiClient;
import com.example.ejmsantos.data.AuthRepository;
import com.example.ejmsantos.data.CartRepository;
import com.example.ejmsantos.model.Product;
import com.google.android.material.snackbar.Snackbar;

import org.json.JSONArray;
import org.json.JSONObject;

/** Ações de acompanhamento, atendimento e recompra do histórico de pedidos. */
public final class OrderPostSaleController {
    private final AppCompatActivity activity;
    private final View snackbarAnchor;
    private final AuthRepository authRepository;
    private final CartRepository cartRepository;
    private final Runnable openCart;

    public OrderPostSaleController(AppCompatActivity activity, View snackbarAnchor,
                                   AuthRepository authRepository,
                                   CartRepository cartRepository, Runnable openCart) {
        this.activity = activity;
        this.snackbarAnchor = snackbarAnchor;
        this.authRepository = authRepository;
        this.cartRepository = cartRepository;
        this.openCart = openCart;
    }

    public void showTracking(JSONObject order) {
        View content = LayoutInflater.from(activity)
                .inflate(R.layout.dialog_order_tracking, null, false);
        String status = order.optString("status", "Pendente");
        JSONObject tracking = order.optJSONObject("tracking");
        int currentStep = tracking == null ? 0 : tracking.optInt("current_step", 0);
        String state = tracking == null ? "active" : tracking.optString("state", "active");
        String message = tracking == null
                ? "Acompanhe aqui as atualizações do seu pedido."
                : tracking.optString("message");

        TextView statusView = content.findViewById(R.id.trackingStatus);
        statusView.setText(status);
        if ("canceled".equals(state) || "attention".equals(state)) {
            statusView.setTextColor(ContextCompat.getColor(activity, R.color.error));
        }
        ((TextView) content.findViewById(R.id.trackingMessage)).setText(message);
        renderSteps(content.findViewById(R.id.trackingStepsContainer), tracking,
                currentStep, state);
        renderShippingPackages(content, order.optJSONArray("shipping_groups"));
        ((TextView) content.findViewById(R.id.trackingDeliveryAddress))
                .setText(deliveryText(order.optJSONObject("endereco")));

        new AlertDialog.Builder(activity)
                .setTitle("Pedido #" + order.optInt("id"))
                .setView(content)
                .setPositiveButton("Fechar", null)
                .show();
    }

    private void renderShippingPackages(View content, JSONArray groups) {
        if (groups == null || groups.length() == 0) return;
        content.findViewById(R.id.trackingPackagesTitle).setVisibility(View.VISIBLE);
        LinearLayout container = content.findViewById(R.id.trackingPackagesContainer);
        container.setVisibility(View.VISIBLE);
        for (int index = 0; index < groups.length(); index++) {
            JSONObject group = groups.optJSONObject(index);
            if (group == null) continue;
            TextView row = new TextView(activity);
            String sender = group.optString("sender", "Loja");
            String dispatch = "supplier_direct".equals(group.optString("dispatch_type"))
                    ? "envio direto" : "envio pela loja";
            row.setText("Pacote " + (index + 1) + " • " + sender + "\n" + dispatch);
            row.setTextColor(ContextCompat.getColor(activity, R.color.text_primary));
            row.setTextSize(14);
            row.setPadding(0, dp(7), 0, dp(7));
            container.addView(row);
        }
    }

    private void renderSteps(LinearLayout container, JSONObject tracking,
                             int currentStep, String state) {
        JSONArray steps = tracking == null ? null : tracking.optJSONArray("steps");
        String[] fallback = {
                "Pedido recebido", "Em preparação", "Saiu para entrega", "Entregue"
        };
        int count = steps == null ? fallback.length : steps.length();
        boolean interrupted = "canceled".equals(state) || "attention".equals(state);

        for (int i = 0; i < count; i++) {
            String label = steps == null ? fallback[i] : steps.optString(i, fallback[i]);
            TextView row = new TextView(activity);
            boolean reached = !interrupted && i <= currentStep;
            String marker;
            if (interrupted && i == currentStep) marker = "×  ";
            else if (i < currentStep || "complete".equals(state) && i == currentStep) marker = "✓  ";
            else if (i == currentStep) marker = "●  ";
            else marker = "○  ";
            row.setText(marker + label);
            row.setTextSize(16);
            row.setPadding(0, dp(7), 0, dp(7));
            row.setTextColor(ContextCompat.getColor(activity,
                    interrupted && i == currentStep ? R.color.error
                            : reached ? R.color.honey_dark : R.color.text_secondary));
            if (i == currentStep) row.setTypeface(null, Typeface.BOLD);
            container.addView(row);
        }
    }

    public void reorder(int orderId) {
        Snackbar.make(snackbarAnchor, "Verificando preço e estoque atuais…",
                Snackbar.LENGTH_SHORT).show();
        ApiClient.prepareReorder(authRepository.getToken(), orderId,
                new ApiClient.Callback<JSONObject>() {
                    @Override public void onSuccess(JSONObject result) {
                        JSONArray items = result.optJSONArray("items");
                        int addedUnits = 0;
                        if (items != null) {
                            for (int i = 0; i < items.length(); i++) {
                                JSONObject item = items.optJSONObject(i);
                                if (item == null || item.optJSONObject("product") == null) continue;
                                try {
                                    Product product = Product.fromJson(item.getJSONObject("product"));
                                    addedUnits += cartRepository.addQuantity(
                                            product, item.optInt("quantity", 1));
                                } catch (Exception ignoredInvalidProduct) {
                                    // Um item inválido não deve impedir os demais de serem adicionados.
                                }
                            }
                        }

                        int unavailable = result.optJSONArray("unavailable") == null
                                ? 0 : result.optJSONArray("unavailable").length();
                        if (addedUnits == 0) {
                            Snackbar.make(snackbarAnchor, result.optString("message",
                                    "Nenhum item disponível"), Snackbar.LENGTH_LONG).show();
                            return;
                        }
                        String message = addedUnits + " unidade(s) adicionada(s) ao carrinho";
                        if (unavailable > 0) message += ". Alguns itens foram ajustados pelo estoque";
                        openCart.run();
                        Snackbar.make(snackbarAnchor, message, Snackbar.LENGTH_LONG).show();
                    }

                    @Override public void onError(String message) {
                        Snackbar.make(snackbarAnchor, message, Snackbar.LENGTH_LONG).show();
                    }
                });
    }

    public void contactSupport(int orderId) {
        String message = "Olá, preciso de ajuda com o pedido #" + orderId + ".";
        String phone = BuildConfig.SUPPORT_WHATSAPP.replaceAll("\\D", "");
        Uri destination;
        if (!phone.isBlank()) {
            destination = Uri.parse("https://wa.me/" + phone + "?text=" + Uri.encode(message));
        } else {
            destination = Uri.parse("mailto:" + BuildConfig.SUPPORT_EMAIL
                    + "?subject=" + Uri.encode("Atendimento do pedido #" + orderId)
                    + "&body=" + Uri.encode(message));
        }

        try {
            activity.startActivity(new Intent(Intent.ACTION_VIEW, destination));
        } catch (ActivityNotFoundException error) {
            Snackbar.make(snackbarAnchor,
                    "Nenhum aplicativo de atendimento disponível neste aparelho",
                    Snackbar.LENGTH_LONG).show();
        }
    }

    private String deliveryText(JSONObject address) {
        if (address == null) return "Endereço de entrega não informado";
        StringBuilder text = new StringBuilder("Entrega: ")
                .append(address.optString("rua"));
        if (!address.optString("numero").isBlank()) {
            text.append(", ").append(address.optString("numero"));
        }
        if (!address.optString("bairro").isBlank()) {
            text.append(" — ").append(address.optString("bairro"));
        }
        if (!address.optString("cidade").isBlank()) {
            text.append(", ").append(address.optString("cidade"));
        }
        return text.toString();
    }

    private int dp(int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
