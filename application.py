# ============================================
# app_new.py — EJM SANTOS - Versão Refatorada
# Loja de Mel Natural 🍯
# ============================================

import os
from pathlib import Path
from dotenv import load_dotenv
import stripe
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Carregar variáveis de ambiente
load_dotenv()
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# ============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================

from config import get_config

# Determinar ambiente
env = os.getenv('FLASK_ENV', 'production')
config_class = get_config(env)

# Criar aplicação
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(config_class)

# Sobrescrever configurações de cookies em development para permitir HTTP
if env == 'development':
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    print("🔓 Cookies de sessão configurados para HTTP (desenvolvimento)")

# Inicializar extensões de segurança
db = SQLAlchemy(app)

# Inicializar CSRF apenas se habilitado na configuração
if app.config.get('WTF_CSRF_ENABLED', True):
    csrf = CSRFProtect(app)
    # Configurar cookie CSRF
    app.config.setdefault('WTF_CSRF_COOKIE_HTTPONLY', False)
    app.config.setdefault('WTF_CSRF_COOKIE_SAMESITE', 'Lax')
else:
    csrf = None
    
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['RATELIMIT_STORAGE_URL']
)

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

# Handler de erro CSRF (apenas se CSRF estiver habilitado)
if app.config.get('WTF_CSRF_ENABLED', True):
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.error(f"❌ CSRF Error: {e.description} - IP: {request.remote_addr if request else 'unknown'}")
        if request.path.startswith('/api/'):
            return {'error': 'CSRF token missing or invalid'}, 400
        return render_template('login.html', erro='Erro de segurança. Recarregue a página e tente novamente.'), 400

# ============================================
# CONFIGURAR STRIPE
# ============================================

try:
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    STRIPE_PUBLIC_KEY = app.config['STRIPE_PUBLIC_KEY']
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

# Importar e inicializar todos os modelos ANTES de criar as tabelas
from app.models import init_models

User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

# Configurar diretório de upload
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
from app.routes.profile import profile_bp, init_profile
from app.routes.diagnostico import diagnostico_bp, init_diagnostico

# Inicializar blueprints com suas dependências
models_dict = {
    'User': User,
    'Product': Product,
    'Order': Order,
    'OrderItem': OrderItem,
    'Review': Review,
    'CartItem': CartItem,
    'Address': Address,
    'PaymentMethod': PaymentMethod
}

# Auth Blueprint
init_auth(db, User, app.config, email_service, logger, limiter)
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

# Profile Blueprint
init_profile(db, models_dict, logger)
app.register_blueprint(profile_bp)
logger.info("✅ Blueprint de perfil registrado")

# Diagnostico Blueprint
init_diagnostico(db, User, Product, app.config)
app.register_blueprint(diagnostico_bp)
logger.info("✅ Blueprint de diagnóstico registrado")

# ============================================
# HEADERS DE SEGURANÇA
# ============================================

from app.utils.security import apply_security_headers

@app.after_request
def security_headers(response):
    """Adiciona headers de segurança otimizados"""
    return apply_security_headers(response, app.config)

# ============================================
# EXECUÇÃO
# ============================================

if __name__ == "__main__":
    # Criar diretórios necessários
    os.makedirs(app.config['INSTANCE_DIR'], exist_ok=True)
    os.makedirs(app.config['LOGS_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
        logger.info("✅ Banco de dados inicializado")
    
    # Info de ambiente
    logger.info(f"🌍 Ambiente: {env}")
    logger.info(f"🔒 CSRF: {'Ativo' if app.config['WTF_CSRF_ENABLED'] else 'Inativo'}")
    logger.info(f"🔐 HTTPS Force: {'Ativo' if app.config.get('FORCE_HTTPS', False) else 'Inativo'}")
    logger.info(f"⚡ Rate Limiting: {'Ativo' if app.config.get('RATELIMIT_ENABLED', True) else 'Inativo'}")
    
    # URL de acesso
    protocol = 'https' if app.config.get('FORCE_HTTPS', False) else 'http'
    logger.info(f"🚀 Servidor iniciando em {protocol}://0.0.0.0:5000")
    logger.info("="*50)
    
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])
