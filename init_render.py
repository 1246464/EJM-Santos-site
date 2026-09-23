#!/usr/bin/env python
"""Prepara o banco usado pelo Render antes de iniciar uma nova versão."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash


load_dotenv()

base_dir = Path(__file__).resolve().parent
instance_dir = base_dir / "instance"
instance_dir.mkdir(parents=True, exist_ok=True)

database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if not database_url:
    database_url = f"sqlite:///{instance_dir / 'ejm.db'}"

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
db = SQLAlchemy(app)

from app.models import init_models


User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

ORDER_COLUMNS = {
    "subtotal": "FLOAT DEFAULT 0",
    "delivery_fee": "FLOAT DEFAULT 0",
    "delivery_distance_km": "FLOAT",
    "delivery_date": "TIMESTAMP",
    "delivery_scheduled_at": "TIMESTAMP",
    "delivery_notes": "TEXT",
    "client_reference": "VARCHAR(64)",
    "payment_method": "VARCHAR(30) DEFAULT 'cash_on_delivery'",
    "payment_status": "VARCHAR(30) DEFAULT 'pending'",
    "external_payment_id": "VARCHAR(100)",
    "inventory_released": "BOOLEAN DEFAULT FALSE",
    "endereco_estado": "VARCHAR(2)",
    "endereco_cep": "VARCHAR(10)",
}

USER_COLUMNS = {
    "mobile_token_version": "INTEGER DEFAULT 0 NOT NULL",
    "is_active": "BOOLEAN DEFAULT TRUE NOT NULL",
    "deleted_at": "TIMESTAMP",
    "password_reset_hash": "VARCHAR(256)",
    "password_reset_expires_at": "TIMESTAMP",
    "password_reset_attempts": "INTEGER DEFAULT 0 NOT NULL",
}

PRODUCT_COLUMNS = {
    "categoria": "VARCHAR(40) DEFAULT 'mel' NOT NULL",
    "origem": "VARCHAR(80)",
    "beneficios": "VARCHAR(255)",
    "sem_adicao_acucar": "BOOLEAN DEFAULT FALSE NOT NULL",
    "destaque": "BOOLEAN DEFAULT FALSE NOT NULL",
    "supplier_id": "INTEGER",
    "brand_id": "INTEGER",
    "fulfillment_origin_id": "INTEGER",
    "weight_kg": "FLOAT",
    "width_cm": "FLOAT",
    "height_cm": "FLOAT",
    "length_cm": "FLOAT",
}


def ensure_columns(table_name, required_columns):
    """Adiciona uma coluna por transação para permitir reexecução após falhas."""
    current = {column["name"] for column in inspect(db.engine).get_columns(table_name)}
    for name, definition in required_columns.items():
        if name in current:
            continue
        with db.engine.begin() as connection:
            connection.execute(text(
                f'ALTER TABLE "{table_name}" ADD COLUMN "{name}" {definition}'
            ))
        print(f"  + {table_name}.{name}")
        current.add(name)


def configure_admin():
    """Cria o primeiro administrador somente com credenciais explícitas."""
    admin_email = os.getenv("EJM_ADMIN_EMAIL")
    admin_password = os.getenv("EJM_ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print("Administrador não alterado: credenciais não informadas.")
        return
    if len(admin_password) < 12:
        raise ValueError("EJM_ADMIN_PASSWORD deve ter pelo menos 12 caracteres")

    normalized_email = admin_email.strip().lower()
    admin = User.query.filter_by(email=normalized_email).first()
    if admin:
        admin.senha_hash = generate_password_hash(admin_password)
        admin.is_admin = True
        admin.is_active = True
    elif not User.query.filter_by(is_admin=True).first():
        db.session.add(User(
            nome="Administrador",
            email=normalized_email,
            senha_hash=generate_password_hash(admin_password),
            is_admin=True,
            is_active=True,
        ))
    else:
        print("Administrador não alterado: já existe outra conta administrativa.")
        return
    db.session.commit()
    print("Administrador configurado por variáveis de ambiente.")


with app.app_context():
    print("Preparando banco de dados da EJM Santos...")
    db.create_all()
    tables = set(inspect(db.engine).get_table_names())
    if "order" in tables:
        ensure_columns("order", ORDER_COLUMNS)
    if "user" in tables:
        ensure_columns("user", USER_COLUMNS)
    if "product" in tables:
        ensure_columns("product", PRODUCT_COLUMNS)

    with db.engine.begin() as connection:
        connection.execute(text(
            'UPDATE "order" SET subtotal = total, delivery_fee = 0 '
            'WHERE subtotal IS NULL OR subtotal = 0'
        ))
        connection.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_order_client_reference_unique '
            'ON "order" (client_reference) WHERE client_reference IS NOT NULL'
        ))
        connection.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_order_external_payment_id_unique '
            'ON "order" (external_payment_id) WHERE external_payment_id IS NOT NULL'
        ))

    configure_admin()
    print(
        "Banco pronto: "
        f"{User.query.count()} usuário(s), {Product.query.count()} produto(s)."
    )
