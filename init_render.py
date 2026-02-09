#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de inicialização automática para Render
Executa automaticamente na primeira vez que o app sobe
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

load_dotenv()

print("="*60)
print("🚀 INICIALIZAÇÃO AUTOMÁTICA - RENDER")
print("="*60)

# Verificar se é primeiro deploy
if os.getenv("FLASK_ENV") != "production":
    print("⚠️  Não é produção, pulando inicialização automática")
    sys.exit(0)

# Criar app Flask
instance_dir = Path(__file__).resolve().parent / 'instance'
instance_dir.mkdir(exist_ok=True)

app = Flask(__name__)

# Usar DATABASE_URL do Render ou SQLite local
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Render PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✅ Usando PostgreSQL do Render")
else:
    # SQLite local
    db_path = instance_dir / 'ejm_dev.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"✅ Usando SQLite local: {db_path}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Importar modelos
from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

with app.app_context():
    try:
        # 1. Criar todas as tabelas
        print("\n📦 Criando tabelas no banco...")
        db.create_all()
        print("✅ Tabelas criadas/verificadas")
        
        # 2. Verificar/criar usuário admin
        admin_email = "admin@ejmsantos.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print(f"\n👤 Criando usuário admin...")
            admin = User(
                nome="Admin EJM",
                email=admin_email,
                senha_hash=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin criado: {admin_email} / admin123")
        else:
            print(f"\n✅ Admin já existe: {admin.email}")
        
        # 3. Verificar produtos (opcional - criar samples para dev)
        product_count = Product.query.count()
        print(f"\n📦 Produtos no banco: {product_count}")
        
        if product_count == 0 and os.getenv("FLASK_ENV") == "development":
            print("⚠️  Banco vazio - execute inicializar_db.py para adicionar produtos")
        
        # 4. Resumo
        print("\n" + "="*60)
        print("✅ INICIALIZAÇÃO COMPLETA!")
        print(f"   • Tabelas: OK")
        print(f"   • Admin: {admin.email}")
        print(f"   • Produtos: {product_count}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
