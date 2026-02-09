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

# Verificar ambiente
flask_env = os.getenv("FLASK_ENV", "production")
print(f"📌 Ambiente: {flask_env}")

# Criar diretório instance com permissões corretas
instance_dir = Path(__file__).resolve().parent / 'instance'
try:
    instance_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    print(f"✅ Diretório instance criado: {instance_dir}")
    print(f"   Permissões: {oct(instance_dir.stat().st_mode)[-3:]}")
    print(f"   Existe: {instance_dir.exists()}")
    print(f"   É diretório: {instance_dir.is_dir()}")
    print(f"   Pode escrever: {os.access(instance_dir, os.W_OK)}")
except Exception as e:
    print(f"❌ Erro ao criar diretório instance: {e}")
    import traceback
    traceback.print_exc()

app = Flask(__name__)

# Usar DATABASE_URL do Render ou SQLite local
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Render PostgreSQL
    print(f"🐘 DATABASE_URL detectada, usando PostgreSQL")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✅ PostgreSQL configurado")
else:
    # SQLite local - verificar se diretório é gravável
    db_path = instance_dir / 'ejm_dev.db'
    print(f"💾 Usando SQLite: {db_path}")
    print(f"   Diretório pai existe: {db_path.parent.exists()}")
    print(f"   Diretório pai gravável: {os.access(db_path.parent, os.W_OK)}")
    
    # Tentar criar arquivo vazio para testar permissões
    try:
        test_file = instance_dir / 'test_write.tmp'
        test_file.touch()
        test_file.unlink()
        print(f"✅ Teste de escrita: OK")
    except Exception as e:
        print(f"❌ Teste de escrita FALHOU: {e}")
        print(f"⚠️  ATENÇÃO: SQLite pode não funcionar no Render!")
        print(f"💡 Configure DATABASE_URL para usar PostgreSQL")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"✅ SQLite configurado")

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
                sen final
        print("\n" + "="*60)
        print("✅ INICIALIZAÇÃO COMPLETA!")
        print(f"   • Banco: {'PostgreSQL' if database_url else 'SQLite'}")
        print(f"   • Tabelas: OK")
        print(f"   • Admin: {admin.email} / admin123")
        print(f"   • Produtos: {product_count}")
        
        if not database_url:
            print(f"\n⚠️  AVISO: Usando SQLite (efêmero no Render)")
            print(f"   Banco será apagado a cada deploy!")
            print(f"   Configure DATABASE_URL para PostgreSQL persistente")
        } / admin123")
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
