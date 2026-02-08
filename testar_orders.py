#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar acesso a orders"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# Criar app Flask simples
instance_dir = Path(__file__).resolve().parent / 'instance'
app = Flask(__name__)
db_path = instance_dir / 'ejm_dev.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Importar modelos
from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

print("="*60)
print("🔍 TESTE DE ACESSO A ORDERS")
print("="*60)

with app.app_context():
    try:
        # Buscar admin
        print(f"\n1️⃣ Buscando usuário admin...")
        user = User.query.filter_by(email="admin@ejmsantos.com").first()
        print(f"   ✅ Usuário encontrado: {user.nome}")
        
        # Tentar acessar orders do usuário
        print(f"\n2️⃣ Tentando acessar orders do usuário...")
        orders = user.orders
        print(f"   ✅ Orders acessadas: {len(orders)} pedidos")
        
        # Listar todos os pedidos
        print(f"\n3️⃣ Buscando todos os pedidos no banco...")
        all_orders = Order.query.all()
        print(f"   ✅ Total de pedidos: {len(all_orders)}")
        
        for order in all_orders:
            print(f"   • Pedido #{order.id} - Status: {order.status}")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
