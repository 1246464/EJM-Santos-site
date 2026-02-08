#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Endpoint de diagnóstico do sistema
Acesse /diagnostico para ver o status
"""

from flask import Blueprint, jsonify
import os
from pathlib import Path

diagnostico_bp = Blueprint('diagnostico', __name__)

# Estas variáveis serão injetadas pelo app.py
db = None
User = None
Product = None
app_config = None

def init_diagnostico(database, user_model, product_model, config):
    """Inicializa o blueprint com dependências"""
    global db, User, Product, app_config
    db = database
    User = user_model
    Product = product_model
    app_config = config


@diagnostico_bp.route("/diagnostico")
def diagnostico():
    """Endpoint de diagnóstico do sistema"""
    
    resultado = {
        "sistema": "EJM Santos",
        "status": "OK",
        "checks": {}
    }
    
    # 1. Verificar variáveis de ambiente
    resultado["checks"]["env"] = {
        "FLASK_ENV": os.getenv("FLASK_ENV", "não configurado"),
        "EJM_SECRET": "✅ configurado" if os.getenv("EJM_SECRET") else "❌ faltando",
        "DATABASE_URL": "✅ configurado" if os.getenv("DATABASE_URL") else "⚠️  usando SQLite local",
    }
    
    # 2. Verificar banco de dados
    try:
        # Tentar criar tabelas se não existirem
        db.create_all()
        
        # Contar usuários
        user_count = User.query.count()
        admin_exists = User.query.filter_by(is_admin=True).first() is not None
        
        # Contar produtos
        product_count = Product.query.count()
        
        resultado["checks"]["database"] = {
            "status": "✅ conectado",
            "usuarios": user_count,
            "admin_cadastrado": "✅ sim" if admin_exists else "❌ não",
            "produtos": product_count
        }
        
        if not admin_exists:
            resultado["status"] = "ATENÇÃO"
            resultado["checks"]["database"]["acao_necessaria"] = "Execute: python garantir_admin.py"
            
    except Exception as e:
        resultado["status"] = "ERRO"
        resultado["checks"]["database"] = {
            "status": "❌ erro",
            "erro": str(e)
        }
    
    # 3. Verificar diretórios
    try:
        instance_dir = Path(app_config.INSTANCE_DIR)
        static_dir = Path(app_config.UPLOAD_FOLDER)
        
        resultado["checks"]["diretorios"] = {
            "instance": "✅ existe" if instance_dir.exists() else "❌ faltando",
            "static_imagens": "✅ existe" if static_dir.exists() else "❌ faltando"
        }
    except Exception as e:
        resultado["checks"]["diretorios"] = {
            "status": "❌ erro",
            "erro": str(e)
        }
    
    # 4. Verificar configurações críticas
    resultado["checks"]["config"] = {
        "SECRET_KEY": "✅ configurada" if app_config.SECRET_KEY else "❌ faltando",
        "CSRF": "✅ habilitado" if app_config.WTF_CSRF_ENABLED else "⚠️  desabilitado",
        "SESSION_SECURE": "✅ sim" if app_config.SESSION_COOKIE_SECURE else "⚠️  não (dev only)"
    }
    
    # Determinar status final
    if resultado["status"] != "ERRO":
        if any("❌" in str(v) for v in resultado["checks"].values()):
            resultado["status"] = "ATENÇÃO"
    
    return jsonify(resultado)


@diagnostico_bp.route("/diagnostico/usuarios")
def diagnostico_usuarios():
    """Lista usuários sem informações sensíveis"""
    try:
        users = User.query.all()
        return jsonify({
            "total": len(users),
            "usuarios": [
                {
                    "id": u.id,
                    "email": u.email,
                    "nome": u.nome,
                    "admin": u.is_admin,
                    "criado_em": u.created_at.isoformat() if u.created_at else None
                }
                for u in users
            ]
        })
    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500
