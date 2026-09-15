"""Testes dos fluxos de segurança e privacidade da conta móvel."""

import os
import unittest
from unittest.mock import patch

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Address, Order, User, app, db


class MobileAccountTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

        registration = self.client.post("/api/mobile/register", json={
            "nome": "Cliente Conta",
            "email": "conta@example.com",
            "senha": "SenhaInicial123",
        })
        self.assertEqual(registration.status_code, 201)
        self.token = registration.get_json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("app.routes.mobile.secrets.randbelow", return_value=123456)
    def test_password_reset_is_private_and_revokes_old_session(self, _randbelow):
        request_reset = self.client.post(
            "/api/mobile/auth/password/reset/request",
            json={"email": "conta@example.com"},
        )
        unknown_email = self.client.post(
            "/api/mobile/auth/password/reset/request",
            json={"email": "nao-existe@example.com"},
        )

        self.assertEqual(request_reset.status_code, 202)
        self.assertEqual(unknown_email.status_code, 202)
        self.assertEqual(request_reset.get_json(), unknown_email.get_json())

        with app.app_context():
            user = User.query.filter_by(email="conta@example.com").one()
            self.assertIsNotNone(user.password_reset_hash)
            self.assertNotIn("123456", user.password_reset_hash)

        confirmation = self.client.post(
            "/api/mobile/auth/password/reset/confirm",
            json={
                "email": "conta@example.com",
                "code": "123456",
                "new_password": "SenhaRecuperada456",
            },
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(
            self.client.get("/api/mobile/me", headers=self.headers).status_code,
            401,
        )
        self.assertEqual(self.client.post("/api/mobile/login", json={
            "email": "conta@example.com",
            "senha": "SenhaInicial123",
        }).status_code, 401)
        self.assertEqual(self.client.post("/api/mobile/login", json={
            "email": "conta@example.com",
            "senha": "SenhaRecuperada456",
        }).status_code, 200)

    def test_change_password_returns_new_session_and_invalidates_old_one(self):
        changed = self.client.post(
            "/api/mobile/auth/password/change",
            headers=self.headers,
            json={
                "current_password": "SenhaInicial123",
                "new_password": "SenhaAlterada789",
            },
        )
        self.assertEqual(changed.status_code, 200)
        new_token = changed.get_json()["token"]

        self.assertEqual(
            self.client.get("/api/mobile/me", headers=self.headers).status_code,
            401,
        )
        self.assertEqual(self.client.get(
            "/api/mobile/me",
            headers={"Authorization": f"Bearer {new_token}"},
        ).status_code, 200)

    def test_delete_account_anonymizes_user_and_preserves_order(self):
        address = self.client.post(
            "/api/mobile/addresses",
            headers=self.headers,
            json={
                "apelido": "Casa", "rua": "Rua das Abelhas", "numero": "10",
                "bairro": "Centro", "cidade": "Santos", "estado": "SP",
                "cep": "11000-000", "telefone": "13999999999",
            },
        )
        self.assertEqual(address.status_code, 201)

        with app.app_context():
            user = User.query.filter_by(email="conta@example.com").one()
            user_id = user.id
            order = Order(
                user_id=user_id,
                total=45.0,
                subtotal=40.0,
                delivery_fee=5.0,
                endereco_rua="Rua preservada no pedido",
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        deleted = self.client.post(
            "/api/mobile/account/delete",
            headers=self.headers,
            json={"password": "SenhaInicial123", "confirmation": "EXCLUIR"},
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            self.client.get("/api/mobile/me", headers=self.headers).status_code,
            401,
        )

        with app.app_context():
            user = db.session.get(User, user_id)
            self.assertFalse(user.is_active)
            self.assertEqual(user.nome, "Conta excluída")
            self.assertTrue(user.email.endswith("@deleted.invalid"))
            self.assertIsNotNone(user.deleted_at)
            self.assertEqual(Address.query.filter_by(user_id=user_id).count(), 0)
            self.assertIsNotNone(db.session.get(Order, order_id))

        self.assertEqual(self.client.post("/api/mobile/login", json={
            "email": "conta@example.com",
            "senha": "SenhaInicial123",
        }).status_code, 401)


if __name__ == "__main__":
    unittest.main()
