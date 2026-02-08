#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para resetar senha do admin"""

import os
import sys
from pathlib import Path
from getpass import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

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
print("🔐 RESETAR SENHA DO ADMIN")
print("="*60)

with app.app_context():
    # Buscar admin
    admin = User.query.filter_by(is_admin=True).first()
    
    if not admin:
        print("\n❌ Nenhum usuário admin encontrado!")
        print("Execute o script para criar um novo admin.")
        sys.exit(1)
    
    print(f"\n✅ Admin encontrado:")
    print(f"   Nome: {admin.nome}")
    print(f"   Email: {admin.email}")
    
    print("\n" + "-"*60)
    print("Digite a nova senha (ou pressione Enter para usar 'admin123'):")
    nova_senha = input("Nova senha: ").strip()
    
    if not nova_senha:
        nova_senha = "admin123"
        print("   → Usando senha padrão: admin123")
    
    # Atualizar senha
    admin.senha_hash = generate_password_hash(nova_senha)
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ SENHA ATUALIZADA COM SUCESSO!")
    print("="*60)
    print("\n📋 CREDENCIAIS DE LOGIN:")
    print(f"   Email: {admin.email}")
    print(f"   Senha: {nova_senha}")
    print("\n🌐 Acesse: http://localhost:5000/admin")
    print("="*60)
