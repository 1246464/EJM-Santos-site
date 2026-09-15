#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Endpoint de diagnóstico do sistema
Acesse /diagnostico para ver o status
"""

from functools import wraps
from flask import Blueprint, jsonify, session
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


def admin_required(f):
    """Restringe diagnósticos a administradores autenticados."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"erro": "Autenticação necessária"}), 401

        user = db.session.get(User, user_id)
        if not user or not user.is_admin:
            return jsonify({"erro": "Acesso restrito a administradores"}), 403

        return f(*args, **kwargs)
    return decorated


@diagnostico_bp.route("/diagnostico")
@admin_required
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
            "erro": "Falha ao consultar o banco de dados"
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
            "erro": "Falha ao verificar os diretórios"
        }
    
    # 4. Verificar configurações críticas
    resultado["checks"]["config"] = {
        "SECRET_KEY": "✅ configurada" if app_config.get("SECRET_KEY") else "❌ faltando",
        "CSRF": "✅ habilitado" if app_config.get("WTF_CSRF_ENABLED") else "⚠️  desabilitado",
        "SESSION_SECURE": "✅ sim" if app_config.get("SESSION_COOKIE_SECURE") else "⚠️  não (dev only)"
    }
    
    # Determinar status final
    if resultado["status"] != "ERRO":
        if any("❌" in str(v) for v in resultado["checks"].values()):
            resultado["status"] = "ATENÇÃO"
    
    return jsonify(resultado)


@diagnostico_bp.route("/diagnostico/usuarios")
@admin_required
def diagnostico_usuarios():
    """Lista metadados de usuários para administradores."""
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
            "erro": "Falha ao consultar usuários"
        }), 500
