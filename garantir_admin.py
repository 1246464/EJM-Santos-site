#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para garantir que o usuário admin existe no banco de dados"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

load_dotenv()

# Criar app Flask
instance_dir = Path(__file__).resolve().parent / 'instance'
instance_dir.mkdir(exist_ok=True)

app = Flask(__name__)
db_path = instance_dir / 'ejm_dev.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Importar modelos
from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

print("="*60)
print("👤 GARANTIR USUÁRIO ADMIN")
print("="*60)

with app.app_context():
    try:
        # Criar todas as tabelas se não existirem
        db.create_all()
        print("✅ Tabelas verificadas/criadas")
        
        # Verificar se admin existe
        admin_email = "admin@ejmsantos.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"\n✅ Admin já existe:")
            print(f"   • Email: {admin.email}")
            print(f"   • Nome: {admin.nome}")
            print(f"   • ID: {admin.id}")
            print(f"   • Admin: {admin.is_admin}")
        else:
            print(f"\n⚠️  Admin não encontrado, criando...")
            
            # Criar admin
            admin = User(
                nome="Admin EJM",
                email=admin_email,
                senha_hash=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            
            print(f"✅ Admin criado com sucesso!")
            print(f"   • Email: {admin_email}")
            print(f"   • Senha: admin123")
            print(f"   • ID: {admin.id}")
        
        # Listar todos os usuários
        print(f"\n📋 Usuários no banco:")
        users = User.query.all()
        for u in users:
            print(f"   • {u.email} - {u.nome} {'(ADMIN)' if u.is_admin else ''}")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
