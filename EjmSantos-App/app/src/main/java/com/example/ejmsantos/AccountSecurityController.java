package com.example.ejmsantos;

import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import com.example.ejmsantos.data.ApiClient;
import com.example.ejmsantos.data.AuthRepository;
import com.google.android.material.snackbar.Snackbar;

import org.json.JSONObject;

import java.util.Locale;

/** Controla os diálogos de segurança sem aumentar ainda mais a MainActivity. */
public final class AccountSecurityController {
    private final AppCompatActivity activity;
    private final View snackbarAnchor;
    private final AuthRepository authRepository;
    private final Runnable refreshAccount;

    public AccountSecurityController(AppCompatActivity activity, View snackbarAnchor,
                                     AuthRepository authRepository, Runnable refreshAccount) {
        this.activity = activity;
        this.snackbarAnchor = snackbarAnchor;
        this.authRepository = authRepository;
        this.refreshAccount = refreshAccount;
    }

    public void showPasswordReset() {
        View form = LayoutInflater.from(activity).inflate(R.layout.dialog_reset_request, null, false);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("Recuperar senha")
                .setMessage("Enviaremos um código de seis dígitos para o email cadastrado.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Enviar código", null)
                .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String email = value(form, R.id.resetEmailInput).toLowerCase(Locale.ROOT);
                    if (!email.contains("@")) {
                        Snackbar.make(form, "Digite um email válido", Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                    ApiClient.requestPasswordReset(email, new ApiClient.Callback<>() {
                        @Override public void onSuccess(JSONObject result) {
                            dialog.dismiss();
                            showPasswordResetConfirmation(email);
                        }

                        @Override public void onError(String message) {
                            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                            Snackbar.make(form, message, Snackbar.LENGTH_LONG).show();
                        }
                    });
                }));
        dialog.show();
    }

    private void showPasswordResetConfirmation(String email) {
        View form = LayoutInflater.from(activity).inflate(R.layout.dialog_reset_confirm, null, false);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("Informe o código")
                .setMessage("Código enviado para " + email + ". Ele expira em 15 minutos.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Atualizar senha", null)
                .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String code = value(form, R.id.resetCodeInput);
                    String password = rawValue(form, R.id.resetNewPasswordInput);
                    if (code.length() != 6 || password.length() < 8) {
                        Snackbar.make(form, "Confira o código e a nova senha", Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                    ApiClient.confirmPasswordReset(email, code, password, new ApiClient.Callback<>() {
                        @Override public void onSuccess(JSONObject result) {
                            dialog.dismiss();
                            Snackbar.make(snackbarAnchor,
                                    "Senha atualizada. Entre com a nova senha.",
                                    Snackbar.LENGTH_LONG).show();
                        }

                        @Override public void onError(String message) {
                            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                            Snackbar.make(form, message, Snackbar.LENGTH_LONG).show();
                        }
                    });
                }));
        dialog.show();
    }

    public void showChangePassword() {
        View form = LayoutInflater.from(activity).inflate(R.layout.dialog_change_password, null, false);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("Alterar senha")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Alterar", null)
                .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String current = rawValue(form, R.id.currentPasswordInput);
                    String replacement = rawValue(form, R.id.newPasswordInput);
                    if (current.isBlank() || replacement.length() < 8) {
                        Snackbar.make(form, "Preencha as duas senhas corretamente", Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                    ApiClient.changePassword(authRepository.getToken(), current, replacement,
                            new ApiClient.Callback<>() {
                                @Override public void onSuccess(JSONObject result) {
                                    if (!authRepository.saveSession(result)) {
                                        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                                        Snackbar.make(form, "Não foi possível salvar a nova sessão",
                                                Snackbar.LENGTH_LONG).show();
                                        return;
                                    }
                                    dialog.dismiss();
                                    refreshAccount.run();
                                    Snackbar.make(snackbarAnchor, "Senha alterada com sucesso",
                                            Snackbar.LENGTH_LONG).show();
                                }

                                @Override public void onError(String message) {
                                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                                    Snackbar.make(form, message, Snackbar.LENGTH_LONG).show();
                                }
                            });
                }));
        dialog.show();
    }

    public void showDeleteAccount() {
        View form = LayoutInflater.from(activity).inflate(R.layout.dialog_delete_account, null, false);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("Excluir sua conta?")
                .setMessage("Esta ação remove seus dados de acesso, endereços e avaliações. "
                        + "Registros necessários dos pedidos serão preservados.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Excluir conta", null)
                .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String password = rawValue(form, R.id.deletePasswordInput);
                    String confirmation = value(form, R.id.deleteConfirmationInput);
                    if (password.isBlank() || !"EXCLUIR".equalsIgnoreCase(confirmation)) {
                        Snackbar.make(form, "Digite sua senha e a palavra EXCLUIR",
                                Snackbar.LENGTH_LONG).show();
                        return;
                    }
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                    ApiClient.deleteAccount(authRepository.getToken(), password, confirmation,
                            new ApiClient.Callback<>() {
                                @Override public void onSuccess(JSONObject result) {
                                    authRepository.logout();
                                    dialog.dismiss();
                                    refreshAccount.run();
                                    Snackbar.make(snackbarAnchor, "Conta excluída",
                                            Snackbar.LENGTH_LONG).show();
                                }

                                @Override public void onError(String message) {
                                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                                    Snackbar.make(form, message, Snackbar.LENGTH_LONG).show();
                                }
                            });
                }));
        dialog.show();
    }

    private String value(View root, int id) {
        return rawValue(root, id).trim();
    }

    private String rawValue(View root, int id) {
        EditText input = root.findViewById(id);
        return input.getText() == null ? "" : input.getText().toString();
    }
}
