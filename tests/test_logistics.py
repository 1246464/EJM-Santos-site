import unittest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


class LogisticsModelTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        self.db = SQLAlchemy(self.app)
        from app.models import init_models

        self.legacy_models = init_models(self.db)
        from app import models

        self.models = models
        self.context = self.app.app_context()
        self.context.push()
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.context.pop()

    def test_existing_init_contract_is_preserved(self):
        self.assertEqual(len(self.legacy_models), 8)

    def test_supplier_origin_and_inventory_are_linked_to_product(self):
        supplier = self.models.Supplier(
            trade_name="Apiário Parceiro",
            direct_shipping=True,
            preparation_days=1,
        )
        self.db.session.add(supplier)
        self.db.session.flush()
        brand = self.models.Brand(name="Mel da Serra", supplier_id=supplier.id)
        origin = self.models.FulfillmentOrigin(
            name="Estoque do parceiro",
            supplier_id=supplier.id,
            city="São Paulo",
            state="SP",
            direct_dispatch=True,
        )
        self.db.session.add_all([brand, origin])
        self.db.session.flush()
        product = self.models.Product(
            titulo="Mel silvestre",
            preco=30,
            estoque=8,
            supplier_id=supplier.id,
            brand_id=brand.id,
            fulfillment_origin_id=origin.id,
            weight_kg=0.5,
        )
        self.db.session.add(product)
        self.db.session.flush()
        inventory = self.models.ProductInventory(
            product_id=product.id,
            origin_id=origin.id,
            quantity=8,
            reserved_quantity=2,
        )
        self.db.session.add(inventory)
        self.db.session.commit()

        self.assertEqual(product.supplier.trade_name, "Apiário Parceiro")
        self.assertEqual(product.brand.name, "Mel da Serra")
        self.assertEqual(product.fulfillment_origin.name, "Estoque do parceiro")
        self.assertEqual(inventory.available_quantity, 6)
        self.assertEqual(product.to_dict()["brand_name"], "Mel da Serra")

    def test_motorcycle_cost_uses_complete_route_and_capacity(self):
        from app.services.shipping import (
            motorcycle_quote_breakdown,
            motorcycle_route_is_eligible,
        )

        settings = self.models.DeliverySettings(
            motorcycle_enabled=True,
            max_roundtrip_km=40,
            fuel_efficiency_km_l=40,
            fuel_price_per_liter=6,
            maintenance_cost_per_km=0.20,
            hourly_rate=18,
            minimum_fee=10,
        )
        self.assertTrue(motorcycle_route_is_eligible(36, 2, settings))
        self.assertFalse(motorcycle_route_is_eligible(41, 2, settings))
        quote = motorcycle_quote_breakdown(40, 60, settings)
        self.assertEqual(quote["operational_cost"], 32.0)
        self.assertEqual(quote["suggested_customer_fee"], 32.0)


if __name__ == "__main__":
    unittest.main()
