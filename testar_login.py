#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar login"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

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
print("🔐 TESTE DE LOGIN")
print("="*60)

email_teste = "admin@ejmsantos.com"
senha_teste = "admin123"

with app.app_context():
    try:
        print(f"\n🔍 Buscando usuário: {email_teste}")
        user = User.query.filter_by(email=email_teste).first()
        
        if user:
            print(f"   ✅ Usuário encontrado: {user.nome} (ID: {user.id})")
            print(f"   Admin: {'Sim' if user.is_admin else 'Não'}")
            
            # Testar senha
            print(f"\n🔑 Testando senha...")
            if check_password_hash(user.senha_hash, senha_teste):
                print("   ✅ Senha correta!")
            else:
                print("   ❌ Senha incorreta!")
        else:
            print(f"   ❌ Usuário não encontrado!")
            
            # Listar todos os usuários
            print(f"\n📋 Usuários no banco:")
            users = User.query.all()
            for u in users:
                print(f"   • {u.email} - {u.nome}")
                
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
