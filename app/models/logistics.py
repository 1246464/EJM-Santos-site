from datetime import datetime


def create_logistics_models(db):
    """Modelos da operação com parceiros e múltiplas origens de estoque."""

    class Supplier(db.Model):
        __tablename__ = "supplier"

        id = db.Column(db.Integer, primary_key=True)
        trade_name = db.Column(db.String(120), nullable=False, index=True)
        legal_name = db.Column(db.String(160))
        document = db.Column(db.String(24), unique=True)
        email = db.Column(db.String(150))
        phone = db.Column(db.String(24))
        direct_shipping = db.Column(db.Boolean, default=False, nullable=False)
        preparation_days = db.Column(db.Integer, default=1, nullable=False)
        active = db.Column(db.Boolean, default=True, nullable=False, index=True)
        notes = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        def __repr__(self):
            return f"<Supplier {self.id}: {self.trade_name}>"

        def to_dict(self):
            return {
                "id": self.id,
                "trade_name": self.trade_name,
                "legal_name": self.legal_name,
                "document": self.document,
                "email": self.email,
                "phone": self.phone,
                "direct_shipping": self.direct_shipping,
                "preparation_days": self.preparation_days,
                "active": self.active,
            }

    class Brand(db.Model):
        __tablename__ = "brand"
        __table_args__ = (
            db.UniqueConstraint("supplier_id", "name", name="uq_brand_supplier_name"),
        )

        id = db.Column(db.Integer, primary_key=True)
        supplier_id = db.Column(
            db.Integer, db.ForeignKey("supplier.id"), nullable=True, index=True
        )
        name = db.Column(db.String(120), nullable=False, index=True)
        active = db.Column(db.Boolean, default=True, nullable=False, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        supplier = db.relationship(
            "Supplier",
            backref=db.backref("brands", lazy=True, order_by="Brand.name"),
        )

        def __repr__(self):
            return f"<Brand {self.id}: {self.name}>"

        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "supplier_id": self.supplier_id,
                "supplier_name": self.supplier.trade_name if self.supplier else None,
                "active": self.active,
            }

    class FulfillmentOrigin(db.Model):
        __tablename__ = "fulfillment_origin"

        id = db.Column(db.Integer, primary_key=True)
        supplier_id = db.Column(
            db.Integer, db.ForeignKey("supplier.id"), nullable=True, index=True
        )
        name = db.Column(db.String(120), nullable=False)
        origin_type = db.Column(db.String(20), default="supplier", nullable=False)
        postal_code = db.Column(db.String(10))
        street = db.Column(db.String(200))
        number = db.Column(db.String(20))
        complement = db.Column(db.String(100))
        district = db.Column(db.String(100))
        city = db.Column(db.String(100))
        state = db.Column(db.String(2))
        latitude = db.Column(db.Float)
        longitude = db.Column(db.Float)
        direct_dispatch = db.Column(db.Boolean, default=False, nullable=False)
        carrier_pickup = db.Column(db.Boolean, default=True, nullable=False)
        preparation_days = db.Column(db.Integer, default=1, nullable=False)
        active = db.Column(db.Boolean, default=True, nullable=False, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        supplier = db.relationship(
            "Supplier",
            backref=db.backref("fulfillment_origins", lazy=True),
        )

        @property
        def address_complete(self):
            first_line = ", ".join(
                part for part in (self.street, self.number) if part
            )
            parts = [
                first_line,
                self.complement,
                self.district,
                self.city,
                self.state,
                self.postal_code,
            ]
            return " - ".join(part for part in parts if part)

        @property
        def is_geocoded(self):
            return self.latitude is not None and self.longitude is not None

        def __repr__(self):
            return f"<FulfillmentOrigin {self.id}: {self.name}>"

        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "origin_type": self.origin_type,
                "supplier_id": self.supplier_id,
                "supplier_name": self.supplier.trade_name if self.supplier else None,
                "postal_code": self.postal_code,
                "city": self.city,
                "state": self.state,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "direct_dispatch": self.direct_dispatch,
                "carrier_pickup": self.carrier_pickup,
                "preparation_days": self.preparation_days,
                "active": self.active,
            }

    class ProductInventory(db.Model):
        __tablename__ = "product_inventory"
        __table_args__ = (
            db.UniqueConstraint("product_id", "origin_id", name="uq_product_origin"),
        )

        id = db.Column(db.Integer, primary_key=True)
        product_id = db.Column(
            db.Integer, db.ForeignKey("product.id"), nullable=False, index=True
        )
        origin_id = db.Column(
            db.Integer,
            db.ForeignKey("fulfillment_origin.id"),
            nullable=False,
            index=True,
        )
        quantity = db.Column(db.Integer, default=0, nullable=False)
        reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
        active = db.Column(db.Boolean, default=True, nullable=False)
        updated_at = db.Column(
            db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
        )

        product = db.relationship(
            "Product",
            backref=db.backref(
                "inventories", lazy=True, cascade="all, delete-orphan"
            ),
        )
        origin = db.relationship(
            "FulfillmentOrigin", backref=db.backref("inventories", lazy=True)
        )

        @property
        def available_quantity(self):
            return max((self.quantity or 0) - (self.reserved_quantity or 0), 0)

    class DeliverySettings(db.Model):
        __tablename__ = "delivery_settings"

        id = db.Column(db.Integer, primary_key=True)
        base_origin_id = db.Column(
            db.Integer, db.ForeignKey("fulfillment_origin.id"), nullable=True
        )
        motorcycle_enabled = db.Column(db.Boolean, default=True, nullable=False)
        vehicle_name = db.Column(db.String(80), default="Suzuki 125", nullable=False)
        max_roundtrip_km = db.Column(db.Float, default=40.0, nullable=False)
        max_package_weight_kg = db.Column(db.Float)
        fuel_efficiency_km_l = db.Column(db.Float)
        fuel_price_per_liter = db.Column(db.Float)
        maintenance_cost_per_km = db.Column(db.Float, default=0.0, nullable=False)
        hourly_rate = db.Column(db.Float, default=0.0, nullable=False)
        minimum_fee = db.Column(db.Float, default=0.0, nullable=False)
        route_buffer_percent = db.Column(db.Float, default=20.0, nullable=False)
        scheduled_delivery_enabled = db.Column(
            db.Boolean, default=True, nullable=False
        )
        same_day_cutoff = db.Column(db.String(5), default="14:00", nullable=False)
        updated_at = db.Column(
            db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
        )

        base_origin = db.relationship("FulfillmentOrigin")

        @classmethod
        def current(cls):
            return cls.query.order_by(cls.id.asc()).first()

    return Supplier, Brand, FulfillmentOrigin, ProductInventory, DeliverySettings
