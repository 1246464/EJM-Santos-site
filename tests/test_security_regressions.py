"""Testes de regressão para controles de segurança críticos."""

import os
import unittest
from pathlib import Path

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import (
    DeliverySettings,
    FulfillmentOrigin,
    PaymentMethod,
    Product,
    ProductInventory,
    Supplier,
    User,
    app,
    db,
)


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

    def test_admin_can_configure_logistics_foundation(self):
        admin_id = self.create_user(is_admin=True)
        self.login_as(admin_id)

        self.assertEqual(self.client.get("/admin/logistica").status_code, 200)
        supplier_response = self.client.post("/admin/logistica/fornecedores", data={
            "trade_name": "Apiário Parceiro",
            "preparation_days": "1",
            "direct_shipping": "on",
        })
        self.assertEqual(supplier_response.status_code, 302)

        with app.app_context():
            supplier_id = Supplier.query.one().id
            product = Product(titulo="Mel local", preco=25, estoque=0)
            db.session.add(product)
            db.session.commit()
            product_id = product.id

        origin_response = self.client.post("/admin/logistica/origens", data={
            "name": "Estoque do parceiro",
            "origin_type": "supplier",
            "supplier_id": str(supplier_id),
            "city": "São Paulo",
            "state": "SP",
            "latitude": "-23.55",
            "longitude": "-46.63",
            "preparation_days": "1",
            "direct_dispatch": "on",
            "carrier_pickup": "on",
        })
        self.assertEqual(origin_response.status_code, 302)

        with app.app_context():
            origin_id = FulfillmentOrigin.query.one().id

        settings_response = self.client.post("/admin/logistica/configuracao", data={
            "base_origin_id": str(origin_id),
            "vehicle_name": "Suzuki 125",
            "max_roundtrip_km": "40",
            "fuel_efficiency_km_l": "35",
            "fuel_price_per_liter": "6.20",
            "maintenance_cost_per_km": "0.20",
            "hourly_rate": "18",
            "minimum_fee": "10",
            "route_buffer_percent": "20",
            "same_day_cutoff": "14:00",
            "motorcycle_enabled": "on",
            "scheduled_delivery_enabled": "on",
        })
        self.assertEqual(settings_response.status_code, 302)

        inventory_response = self.client.post("/admin/logistica/estoque", data={
            "product_id": str(product_id),
            "origin_id": str(origin_id),
            "quantity": "7",
        })
        self.assertEqual(inventory_response.status_code, 302)

        with app.app_context():
            self.assertEqual(DeliverySettings.current().max_roundtrip_km, 40)
            self.assertEqual(ProductInventory.query.one().quantity, 7)
            self.assertEqual(db.session.get(Product, product_id).estoque, 7)

    def test_raw_card_data_is_rejected(self):
        user_id = self.create_user(is_admin=False)
        self.login_as(user_id)
        response = self.client.post("/api/payment-methods", json={
            "apelido": "Teste",
            "numero": "4111111111111111",
            "validade": "12/30",
            "cvv": "123",
            "nome_titular": "Cliente Teste",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Stripe", response.get_json()["error"])
        with app.app_context():
            self.assertEqual(PaymentMethod.query.count(), 0)

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

        refreshed = self.client.post(
            "/api/mobile/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(refreshed.status_code, 200)
        refreshed_token = refreshed.get_json()["token"]

        logout = self.client.post(
            "/api/mobile/auth/logout",
            headers={"Authorization": f"Bearer {refreshed_token}"},
        )
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get(
            "/api/mobile/me",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code, 401)
        self.assertEqual(self.client.get(
            "/api/mobile/me",
            headers={"Authorization": f"Bearer {refreshed_token}"},
        ).status_code, 401)

    def test_mobile_health_verifies_database_schema(self):
        response = self.client.get("/api/mobile/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["database"], "ok")
        self.assertEqual(response.get_json()["version"], 2)

    def test_no_default_admin_password_in_provisioning_code(self):
        root = Path(__file__).resolve().parent.parent
        provisioning_files = [
            root / "application.py",
            root / "init_render.py",
            root / "garantir_admin.py",
            root / "resetar_senha_admin.py",
            root / "testar_login.py",
            root / "testar_login_web.py",
            root / "scripts" / "database" / "recriar_db.py",
        ]
        for path in provisioning_files:
            self.assertNotIn("admin123", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
