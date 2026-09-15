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
from config import get_config

load_dotenv()

# Usar o mesmo banco configurado para o ambiente selecionado.
app = Flask(__name__)
app.config.from_object(get_config(os.getenv("FLASK_ENV", "development")))
db = SQLAlchemy(app)

# Importar modelos
from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

print("="*60)
print("👤 GARANTIR USUÁRIO ADMIN")
print("="*60)

admin_email = os.getenv("EJM_ADMIN_EMAIL")
admin_password = os.getenv("EJM_ADMIN_PASSWORD")

if not admin_email or "@" not in admin_email:
    raise SystemExit("❌ Defina EJM_ADMIN_EMAIL com um email válido")
if not admin_password or len(admin_password) < 12:
    raise SystemExit("❌ Defina EJM_ADMIN_PASSWORD com pelo menos 12 caracteres")

admin_email = admin_email.strip().lower()

with app.app_context():
    try:
        # Criar todas as tabelas se não existirem
        db.create_all()
        print("✅ Tabelas verificadas/criadas")
        
        # Verificar se admin existe
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            admin.senha_hash = generate_password_hash(admin_password)
            admin.is_admin = True
            print(f"\n✅ Admin atualizado:")
            print(f"   • Email: {admin.email}")
            print(f"   • Nome: {admin.nome}")
            print(f"   • ID: {admin.id}")
        else:
            print(f"\n⚠️  Admin não encontrado, criando...")
            
            # Criar admin
            admin = User(
                nome="Admin EJM",
                email=admin_email,
                senha_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            print("✅ Admin criado com sucesso!")
            print(f"   • Email: {admin_email}")

        db.session.commit()
        
        # Listar todos os usuários
        print(f"\n📋 Usuários no banco:")
        users = User.query.all()
        for u in users:
            print(f"   • {u.email} - {u.nome} {'(ADMIN)' if u.is_admin else ''}")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)

print("\n" + "="*60)
