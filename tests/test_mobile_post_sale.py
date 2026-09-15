"""Testes do acompanhamento e recompra no aplicativo móvel."""

import os
import unittest

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("EJM_SECRET", "test_secret_key_with_at_least_32_characters")

from application import Order, OrderItem, Product, User, app, db


class MobilePostSaleTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

        registration = self.client.post("/api/mobile/register", json={
            "nome": "Cliente Pós-venda",
            "email": "posvenda@example.com",
            "senha": "SenhaPosVenda123",
        })
        self.assertEqual(registration.status_code, 201)
        self.headers = {
            "Authorization": f"Bearer {registration.get_json()['token']}"
        }

        with app.app_context():
            user = User.query.filter_by(email="posvenda@example.com").one()
            product = Product(
                titulo="Mel florada silvestre",
                descricao="Pote de 500 g",
                preco=30.0,
                estoque=1,
                imagem="mel.jpg",
            )
            db.session.add(product)
            db.session.flush()
            order = Order(
                user_id=user.id,
                total=65.0,
                subtotal=60.0,
                delivery_fee=5.0,
                status="Saiu para Entrega",
                endereco_rua="Rua das Flores",
                endereco_numero="10",
                endereco_bairro="Centro",
                endereco_cidade="Santos",
            )
            db.session.add(order)
            db.session.flush()
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantidade=2,
                preco_unitario=20.0,
            ))
            db.session.commit()
            self.order_id = order.id
            self.product_id = product.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_order_history_contains_normalized_tracking(self):
        response = self.client.get("/api/mobile/orders", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        order = response.get_json()["orders"][0]
        self.assertEqual(order["tracking"]["current_step"], 2)
        self.assertEqual(order["tracking"]["state"], "active")
        self.assertEqual(order["tracking"]["steps"][2], "Saiu para entrega")

    def test_reorder_uses_current_price_and_caps_quantity_to_stock(self):
        response = self.client.post(
            f"/api/mobile/orders/{self.order_id}/reorder",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["items"][0]["quantity"], 1)
        self.assertEqual(payload["items"][0]["requested_quantity"], 2)
        self.assertEqual(payload["items"][0]["product"]["preco"], 30.0)
        self.assertEqual(len(payload["unavailable"]), 1)

    def test_reorder_does_not_expose_another_customers_order(self):
        with app.app_context():
            another_user = User(
                nome="Outro cliente",
                email="outro@example.com",
                senha_hash="hash-de-teste",
            )
            db.session.add(another_user)
            db.session.flush()
            another_order = Order(user_id=another_user.id, total=10.0, subtotal=10.0)
            db.session.add(another_order)
            db.session.commit()
            another_order_id = another_order.id

        response = self.client.post(
            f"/api/mobile/orders/{another_order_id}/reorder",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
