# ============================================
# app_new.py — EJM SANTOS - Versão Refatorada
# Loja de Mel Natural 🍯
# ============================================

import os
from pathlib import Path
from dotenv import load_dotenv
import stripe
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Carregar variáveis de ambiente
load_dotenv()
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# ============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "ejm.db")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("EJM_SECRET", "chave_fallback")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# ============================================
# CONFIGURAR LOGGING E ERROR HANDLERS
# ============================================

from app.utils.logger import setup_logger
from app.utils.error_handlers import register_error_handlers

logger = setup_logger(app)
logger.info("="*50)
logger.info("🍯 Iniciando EJM Santos - Loja de Mel Natural")
logger.info("="*50)

register_error_handlers(app, logger)

# ============================================
# CONFIGURAR STRIPE
# ============================================

try:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    if not stripe.api_key:
        logger.warning("⚠️ STRIPE_SECRET_KEY não configurada")
    else:
        logger.info("✅ Stripe configurado com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao configurar Stripe: {e}")
    STRIPE_PUBLIC_KEY = None

# ============================================
# IMPORTAR MODELOS
# ============================================

# Importar todos os modelos ANTES de criar as tabelas
from app.models import User, Product, Order, OrderItem, Review, CartItem

# Configurar diretório de upload
UPLOAD_FOLDER = os.path.join(app.static_folder, "imagens")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ============================================
# IMPORTAR E CONFIGURAR HELPERS
# ============================================

from app.helpers import CartHelper, OrderHelper

# ============================================
# IMPORTAR SERVIÇO DE EMAIL
# ============================================

from email_service import email_service

# ============================================
# REGISTRAR BLUEPRINTS
# ============================================

from app.routes import (
    auth_bp, init_auth,
    admin_bp, init_admin,
    products_bp, init_products,
    payment_bp, init_payment
)

# Inicializar blueprints com suas dependências
models_dict = {
    'User': User,
    'Product': Product,
    'Order': Order,
    'OrderItem': OrderItem,
    'Review': Review,
    'CartItem': CartItem
}

# Auth Blueprint
init_auth(db, User, app.config, email_service, logger)
app.register_blueprint(auth_bp)
logger.info("✅ Blueprint de autenticação registrado")

# Admin Blueprint
init_admin(db, models_dict, logger, email_service, UPLOAD_FOLDER)
app.register_blueprint(admin_bp)
logger.info("✅ Blueprint de admin registrado")

# Products Blueprint
init_products(db, models_dict, logger)
app.register_blueprint(products_bp)
logger.info("✅ Blueprint de produtos registrado")

# Payment Blueprint
init_payment(db, models_dict, logger, email_service, CartHelper, OrderHelper, STRIPE_PUBLIC_KEY)
app.register_blueprint(payment_bp)
logger.info("✅ Blueprint de pagamento registrado")

# ============================================
# CACHE CONTROL
# ============================================

@app.after_request
def add_header(response):
    """Evita cache de páginas pós-login"""
    response.headers["Cache-Control"] = "no-store"
    return response

# ============================================
# EXECUÇÃO
# ============================================

if __name__ == "__main__":
    # Criar diretórios necessários
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
        logger.info("✅ Banco de dados inicializado")
    
    logger.info("🚀 Servidor iniciando em http://0.0.0.0:5000")
    logger.info("="*50)
    
    app.run(host="0.0.0.0", port=5000, debug=True)
