"""Testes de regressão para controles de segurança críticos."""

import os
import unittest
from pathlib import Path

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Product, User, app, db


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def create_user(self, *, is_admin):
        with app.app_context():
            user = User(
                nome="Admin" if is_admin else "Cliente",
                email="admin@example.com" if is_admin else "cliente@example.com",
                senha_hash="hash-apenas-para-teste",
                is_admin=is_admin,
            )
            db.session.add(user)
            db.session.commit()
            return user.id

    def login_as(self, user_id):
        with self.client.session_transaction() as flask_session:
            flask_session["user_id"] = user_id

    def test_diagnostics_require_authentication_and_admin_role(self):
        self.assertEqual(self.client.get("/diagnostico").status_code, 401)
        self.assertEqual(self.client.get("/diagnostico/usuarios").status_code, 401)

        self.login_as(self.create_user(is_admin=False))
        self.assertEqual(self.client.get("/diagnostico").status_code, 403)

        self.login_as(self.create_user(is_admin=True))
        self.assertEqual(self.client.get("/diagnostico").status_code, 200)
        self.assertEqual(self.client.get("/diagnostico/usuarios").status_code, 200)

    def test_product_deletion_rejects_get_and_accepts_admin_post(self):
        admin_id = self.create_user(is_admin=True)
        with app.app_context():
            product = Product(titulo="Produto teste", preco=10.0, estoque=1)
            db.session.add(product)
            db.session.commit()
            product_id = product.id

        self.login_as(admin_id)
        self.assertEqual(self.client.get(f"/admin/remover/{product_id}").status_code, 405)
        self.assertEqual(self.client.post(f"/admin/remover/{product_id}").status_code, 302)

        with app.app_context():
            self.assertIsNone(db.session.get(Product, product_id))

    def test_mobile_registration_login_and_bearer_auth(self):
        registration = self.client.post("/api/mobile/register", json={
            "nome": "Cliente Mobile",
            "email": "mobile@example.com",
            "senha": "SenhaMobile123",
        })
        self.assertEqual(registration.status_code, 201)
        token = registration.get_json()["token"]

        profile = self.client.get(
            "/api/mobile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.get_json()["user"]["email"], "mobile@example.com")

        login = self.client.post("/api/mobile/login", json={
            "email": "mobile@example.com",
            "senha": "SenhaMobile123",
        })
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.get_json())

        self.assertEqual(self.client.get("/api/mobile/me").status_code, 401)

        address = self.client.post(
            "/api/mobile/addresses",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "apelido": "Casa", "rua": "Rua das Flores", "numero": "10",
                "bairro": "Centro", "cidade": "Santos", "estado": "SP",
                "cep": "11000-000", "telefone": "13999999999",
            },
        )
        self.assertEqual(address.status_code, 201)
        self.assertTrue(address.get_json()["address"]["is_default"])

        addresses = self.client.get(
            "/api/mobile/addresses",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(len(addresses.get_json()["addresses"]), 1)

    def test_no_default_admin_password_in_provisioning_code(self):
        root = Path(__file__).resolve().parent.parent
        provisioning_files = [
            root / "application.py",
            root / "garantir_admin.py",
            root / "scripts" / "database" / "recriar_db.py",
        ]
        for path in provisioning_files:
            self.assertNotIn("admin123", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
