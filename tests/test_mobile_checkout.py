"""Testes do checkout usado pelo aplicativo Android."""

import os
import unittest
from unittest.mock import patch

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Order, Product, app, db


class MobileCheckoutTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            STRIPE_PUBLIC_KEY="pk_test_mobile",
            STRIPE_SECRET_KEY="sk_test_mobile",
            STRIPE_WEBHOOK_SECRET="whsec_test_mobile",
        )
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

    @patch("app.routes.mobile.stripe.PaymentIntent.create")
    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_stripe_intent_reserves_stock_and_uses_server_total(self, _calculate, create_intent):
        create_intent.return_value = {
            "id": "pi_mobile_test",
            "client_secret": "pi_mobile_test_secret",
        }
        response = self.client.post(
            "/api/mobile/payments/stripe/intent",
            headers=self.headers,
            json={
                "address_id": self.address_id,
                "items": self.items,
                "client_reference": "stripe-test-001",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["publishable_key"], "pk_test_mobile")
        self.assertEqual(response.get_json()["client_secret"], "pi_mobile_test_secret")
        create_intent.assert_called_once()
        self.assertEqual(create_intent.call_args.kwargs["amount"], 3250)
        self.assertEqual(create_intent.call_args.kwargs["currency"], "brl")

        with app.app_context():
            order = Order.query.one()
            self.assertEqual(order.payment_method, "stripe")
            self.assertEqual(order.payment_status, "requires_payment")
            self.assertEqual(order.status, "Aguardando pagamento")
            self.assertEqual(db.session.get(Product, self.product_id).estoque, 3)

        switched = self.client.post(
            "/api/mobile/orders",
            headers=self.headers,
            json={
                "address_id": self.address_id,
                "items": self.items,
                "payment_method": "cash_on_delivery",
                "client_reference": "stripe-test-001",
            },
        )
        self.assertEqual(switched.status_code, 409)

    @patch("app.routes.mobile.stripe.Webhook.construct_event")
    @patch("app.routes.mobile.stripe.PaymentIntent.create")
    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_stripe_webhook_marks_order_paid(self, _calculate, create_intent, construct_event):
        create_intent.return_value = {
            "id": "pi_mobile_paid",
            "client_secret": "pi_mobile_paid_secret",
        }
        created = self.client.post(
            "/api/mobile/payments/stripe/intent",
            headers=self.headers,
            json={
                "address_id": self.address_id,
                "items": self.items,
                "client_reference": "stripe-test-paid",
            },
        )
        order_id = created.get_json()["order"]["id"]
        construct_event.return_value = {
            "type": "payment_intent.succeeded",
            "data": {"object": {
                "id": "pi_mobile_paid",
                "amount_received": 3250,
                "currency": "brl",
            }},
        }

        webhook = self.client.post(
            "/api/mobile/payments/stripe/webhook",
            data=b"raw-event",
            headers={"Stripe-Signature": "valid-test-signature"},
        )

        self.assertEqual(webhook.status_code, 200)
        construct_event.assert_called_once()
        with app.app_context():
            order = db.session.get(Order, order_id)
            self.assertEqual(order.payment_status, "paid")
            self.assertEqual(order.status, "Pago")
            self.assertFalse(order.inventory_released)

        # Webhooks podem chegar fora de ordem; um evento antigo não pode
        # rebaixar nem cancelar um pedido já pago.
        construct_event.return_value = {
            "type": "payment_intent.canceled",
            "data": {"object": {"id": "pi_mobile_paid"}},
        }
        delayed = self.client.post(
            "/api/mobile/payments/stripe/webhook",
            data=b"delayed-event",
            headers={"Stripe-Signature": "valid-test-signature"},
        )
        self.assertEqual(delayed.status_code, 200)
        with app.app_context():
            order = db.session.get(Order, order_id)
            self.assertEqual(order.payment_status, "paid")
            self.assertEqual(order.status, "Pago")
            self.assertEqual(db.session.get(Product, self.product_id).estoque, 3)

    @patch("app.routes.mobile.stripe.Webhook.construct_event")
    @patch("app.routes.mobile.stripe.PaymentIntent.create")
    @patch("app.utils.distance.calculate_delivery_fee", return_value=(5.0, 7.5))
    def test_canceled_stripe_payment_releases_inventory_only_once(
            self, _calculate, create_intent, construct_event):
        create_intent.return_value = {
            "id": "pi_mobile_canceled",
            "client_secret": "pi_mobile_canceled_secret",
        }
        self.client.post(
            "/api/mobile/payments/stripe/intent",
            headers=self.headers,
            json={
                "address_id": self.address_id,
                "items": self.items,
                "client_reference": "stripe-test-canceled",
            },
        )
        construct_event.return_value = {
            "type": "payment_intent.canceled",
            "data": {"object": {"id": "pi_mobile_canceled"}},
        }

        for _ in range(2):
            response = self.client.post(
                "/api/mobile/payments/stripe/webhook",
                data=b"raw-event",
                headers={"Stripe-Signature": "valid-test-signature"},
            )
            self.assertEqual(response.status_code, 200)

        with app.app_context():
            order = Order.query.one()
            self.assertEqual(order.payment_status, "canceled")
            self.assertTrue(order.inventory_released)
            self.assertEqual(db.session.get(Product, self.product_id).estoque, 5)


if __name__ == "__main__":
    unittest.main()
