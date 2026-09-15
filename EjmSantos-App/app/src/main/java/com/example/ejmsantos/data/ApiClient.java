package com.example.ejmsantos.data;

import android.os.Handler;
import android.os.Looper;

import com.example.ejmsantos.BuildConfig;
import com.example.ejmsantos.model.Product;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class ApiClient {
    public interface Callback<T> {
        void onSuccess(T result);
        void onError(String message);
    }

    private interface Parser<T> {
        T parse(String body) throws Exception;
    }

    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(3);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private ApiClient() {}

    public static void getProducts(Callback<List<Product>> callback) {
        request("GET", "api/products", null, null, body -> {
            JSONArray array = new JSONArray(body);
            List<Product> products = new ArrayList<>();
            for (int i = 0; i < array.length(); i++) {
                products.add(Product.fromJson(array.getJSONObject(i)));
            }
            return products;
        }, callback);
    }

    public static void login(String email, String password, Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("email", email);
            body.put("senha", password);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/login", body, null, JSONObject::new, callback);
    }

    public static void register(String name, String email, String password,
                                Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("nome", name);
            body.put("email", email);
            body.put("senha", password);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/register", body, null, JSONObject::new, callback);
    }

    public static void getAddresses(String token, Callback<JSONObject> callback) {
        request("GET", "api/mobile/addresses", null, token, JSONObject::new, callback);
    }

    public static void createAddress(String token, JSONObject address, Callback<JSONObject> callback) {
        request("POST", "api/mobile/addresses", address, token, JSONObject::new, callback);
    }

    public static void setDefaultAddress(String token, int addressId, Callback<JSONObject> callback) {
        request("POST", "api/mobile/addresses/" + addressId + "/default",
                new JSONObject(), token, JSONObject::new, callback);
    }

    public static void deleteAddress(String token, int addressId, Callback<JSONObject> callback) {
        request("DELETE", "api/mobile/addresses/" + addressId,
                null, token, JSONObject::new, callback);
    }

    public static void getOrders(String token, Callback<JSONObject> callback) {
        request("GET", "api/mobile/orders", null, token, JSONObject::new, callback);
    }

    public static void prepareReorder(String token, int orderId, Callback<JSONObject> callback) {
        request("POST", "api/mobile/orders/" + orderId + "/reorder",
                new JSONObject(), token, JSONObject::new, callback);
    }

    public static void logout(String token, Callback<JSONObject> callback) {
        request("POST", "api/mobile/auth/logout", new JSONObject(),
                token, JSONObject::new, callback);
    }

    public static void refreshSession(String token, Callback<JSONObject> callback) {
        request("POST", "api/mobile/auth/refresh", new JSONObject(),
                token, JSONObject::new, callback);
    }

    public static void requestPasswordReset(String email, Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try { body.put("email", email); } catch (Exception ignored) {}
        request("POST", "api/mobile/auth/password/reset/request",
                body, null, JSONObject::new, callback);
    }

    public static void confirmPasswordReset(String email, String code, String newPassword,
                                            Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("email", email);
            body.put("code", code);
            body.put("new_password", newPassword);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/auth/password/reset/confirm",
                body, null, JSONObject::new, callback);
    }

    public static void changePassword(String token, String currentPassword, String newPassword,
                                      Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("current_password", currentPassword);
            body.put("new_password", newPassword);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/auth/password/change",
                body, token, JSONObject::new, callback);
    }

    public static void deleteAccount(String token, String password, String confirmation,
                                     Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("password", password);
            body.put("confirmation", confirmation);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/account/delete",
                body, token, JSONObject::new, callback);
    }

    public static void getCheckoutQuote(String token, int addressId, JSONArray items,
                                        Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("address_id", addressId);
            body.put("items", items);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/checkout/quote", body, token, JSONObject::new, callback);
    }

    public static void createOrder(String token, int addressId, JSONArray items,
                                   String clientReference, Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("address_id", addressId);
            body.put("items", items);
            body.put("payment_method", "cash_on_delivery");
            body.put("client_reference", clientReference);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/orders", body, token, JSONObject::new, callback);
    }

    public static void createStripePaymentIntent(String token, int addressId, JSONArray items,
                                                 String clientReference,
                                                 Callback<JSONObject> callback) {
        JSONObject body = new JSONObject();
        try {
            body.put("address_id", addressId);
            body.put("items", items);
            body.put("client_reference", clientReference);
        } catch (Exception ignored) {}
        request("POST", "api/mobile/payments/stripe/intent",
                body, token, JSONObject::new, callback);
    }

    private static <T> void request(String method, String path, JSONObject jsonBody,
                                    String token, Parser<T> parser, Callback<T> callback) {
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(BuildConfig.API_BASE_URL + path).openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(12_000);
                connection.setReadTimeout(15_000);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("X-App-Client", "EjmSantos-Android/1");
                if (token != null && !token.isBlank()) {
                    connection.setRequestProperty("Authorization", "Bearer " + token);
                }

                if (jsonBody != null) {
                    connection.setDoOutput(true);
                    connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                    byte[] payload = jsonBody.toString().getBytes(StandardCharsets.UTF_8);
                    try (OutputStream output = connection.getOutputStream()) {
                        output.write(payload);
                    }
                }

                int status = connection.getResponseCode();
                InputStream stream = status >= 200 && status < 300
                        ? connection.getInputStream() : connection.getErrorStream();
                String responseBody = readBody(stream);

                if (status >= 200 && status < 300) {
                    T parsed = parser.parse(responseBody);
                    MAIN.post(() -> callback.onSuccess(parsed));
                } else {
                    String message = extractMessage(responseBody, "O servidor respondeu com erro " + status);
                    MAIN.post(() -> callback.onError(message));
                }
            } catch (Exception exception) {
                MAIN.post(() -> callback.onError("Sem conexão com a loja. Verifique sua internet."));
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }

    private static String readBody(InputStream stream) throws Exception {
        if (stream == null) return "";
        StringBuilder result = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) result.append(line);
        }
        return result.toString();
    }

    private static String extractMessage(String body, String fallback) {
        try {
            JSONObject json = new JSONObject(body);
            return json.optString("message", json.optString("error", fallback));
        } catch (Exception ignored) {
            return fallback;
        }
    }
}
