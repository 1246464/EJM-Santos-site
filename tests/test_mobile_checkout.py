"""Testes do checkout usado pelo aplicativo Android."""

import os
import unittest
from unittest.mock import patch

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Order, Product, app, db


class MobileCheckoutTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            product = Product(titulo="Mel silvestre 500g", preco=12.50, estoque=5)
            db.session.add(product)
            db.session.commit()
            self.product_id = product.id

        registration = self.client.post("/api/mobile/register", json={
            "nome": "Cliente Checkout",
            "email": "checkout@example.com",
            "senha": "SenhaCheckout123",
        })
        self.token = registration.get_json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        address = self.client.post(
            "/api/mobile/addresses",
            headers=self.headers,
            json={
                "apelido": "Casa",
                "rua": "Rua das Flores",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Santos",
                "estado": "SP",
                "cep": "11000-000",
                "telefone": "13999999999",
            },
        )
        self.address_id = address.get_json()["address"]["id"]
        self.items = [{
            "product_id": self.product_id,
            "quantity": 2,
            # Deve ser ignorado: o servidor é a fonte do preço.
            "unit_price": 0.01,
        }]

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_quote_uses_server_price_and_calculates_delivery(self, _calculate):
        response = self.client.post(
            "/api/mobile/checkout/quote",
            headers=self.headers,
            json={"address_id": self.address_id, "items": self.items},
        )

        self.assertEqual(response.status_code, 200)
        quote = response.get_json()
        self.assertEqual(quote["subtotal"], 25.0)
        self.assertEqual(quote["delivery_fee"], 7.5)
        self.assertEqual(quote["total"], 32.5)

    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_order_is_idempotent_and_reduces_stock_once(self, _calculate):
        payload = {
            "address_id": self.address_id,
            "items": self.items,
            "payment_method": "cash_on_delivery",
            "client_reference": "checkout-test-001",
        }
        first = self.client.post("/api/mobile/orders", headers=self.headers, json=payload)
        second = self.client.post("/api/mobile/orders", headers=self.headers, json=payload)

        self.assertEqual(first.status_code, 201)
        self.assertFalse(first.get_json()["duplicate"])
        self.assertEqual(first.get_json()["order"]["total"], 32.5)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.get_json()["duplicate"])
        self.assertEqual(
            first.get_json()["order"]["id"],
            second.get_json()["order"]["id"],
        )

        with app.app_context():
            self.assertEqual(db.session.get(Product, self.product_id).estoque, 3)
            self.assertEqual(Order.query.count(), 1)

    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_order_rejects_quantity_above_stock(self, _calculate):
        response = self.client.post(
            "/api/mobile/orders",
            headers=self.headers,
            json={
                "address_id": self.address_id,
                "items": [{"product_id": self.product_id, "quantity": 6}],
                "payment_method": "cash_on_delivery",
                "client_reference": "checkout-test-stock",
            },
        )

        self.assertEqual(response.status_code, 409)
        with app.app_context():
            self.assertEqual(db.session.get(Product, self.product_id).estoque, 5)
            self.assertEqual(Order.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
