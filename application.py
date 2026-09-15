# ============================================
# application.py — EJM SANTOS - Aplicação Flask
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

# Garantir que SECRET_KEY está configurada
if not app.config.get('SECRET_KEY'):
    import secrets
    if env == 'production':
        print("⚠️  SECRET_KEY não configurada em produção!")
        print("⚠️  Gerando SECRET_KEY temporária - CONFIGURE EJM_SECRET para persistir sessões!")
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    else:
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        print("🔑 SECRET_KEY temporária gerada (desenvolvimento)")

# Sobrescrever configurações de cookies em development para permitir HTTP
if env == 'development':
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    print("🔓 Cookies de sessão configurados para HTTP (desenvolvimento)")

# Inicializar extensões de segurança
db = SQLAlchemy(app)

# Inicializar a extensão sempre. A opção WTF_CSRF_ENABLED controla apenas a
# validação, preservando csrf_token() nos templates durante testes.
csrf = CSRFProtect(app)
app.config.setdefault('WTF_CSRF_COOKIE_HTTPONLY', False)
app.config.setdefault('WTF_CSRF_COOKIE_SAMESITE', 'Lax')
    
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

# ============================================
# CRIAR TABELAS AUTOMATICAMENTE
# ============================================

# Criar tabelas no banco de dados (funciona com SQLite e PostgreSQL)
# IMPORTANTE: Isso deve executar sempre, mesmo quando importado pelo gunicorn
with app.app_context():
    try:
        # Verificar se tabela user existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'user' not in existing_tables:
            logger.info("🏗️ Criando tabelas no banco de dados...")
            db.create_all()
            logger.info("✅ Tabelas criadas com sucesso")
        else:
            logger.info("ℹ️ Tabelas já existem no banco de dados")

    except Exception as e:
        logger.error(f"❌ Erro ao verificar/criar tabelas: {e}")
    
    # ============================================
    # MIGRAÇÃO AUTOMÁTICA - Adicionar colunas de entrega
    # ============================================
    try:
        logger.info("🔄 Verificando migrações necessárias...")
        
        if 'order' in existing_tables:
            existing_columns = [col['name'] for col in inspector.get_columns('order')]
            
            # Colunas que precisam existir
            required_columns = {
                'subtotal': 'FLOAT DEFAULT 0',
                'delivery_fee': 'FLOAT DEFAULT 0',
                'delivery_distance_km': 'FLOAT',
                'delivery_date': 'TIMESTAMP',
                'delivery_scheduled_at': 'TIMESTAMP',
                'delivery_notes': 'TEXT',
                'client_reference': 'VARCHAR(64)',
                'payment_method': "VARCHAR(30) DEFAULT 'cash_on_delivery'",
                'payment_status': "VARCHAR(30) DEFAULT 'pending'",
                'external_payment_id': 'VARCHAR(100)',
                'inventory_released': 'BOOLEAN DEFAULT FALSE',
                'endereco_estado': 'VARCHAR(2)',
                'endereco_cep': 'VARCHAR(10)'
            }
            
            columns_to_add = [col for col in required_columns if col not in existing_columns]
            
            if columns_to_add:
                logger.info(f"📝 Adicionando {len(columns_to_add)} colunas em 'order': {', '.join(columns_to_add)}")
                
                with db.engine.connect() as conn:
                    for col_name in columns_to_add:
                        col_type = required_columns[col_name]
                        try:
                            conn.execute(db.text(f'ALTER TABLE "order" ADD COLUMN {col_name} {col_type}'))
                            conn.commit()
                            logger.info(f"✅ Coluna '{col_name}' adicionada")
                        except Exception as e:
                            logger.warning(f"⚠️ Coluna '{col_name}': {str(e)[:60]}")
                
                # Atualizar pedidos antigos
                try:
                    result = db.session.execute(db.text(
                        'UPDATE "order" SET subtotal = total, delivery_fee = 0 WHERE subtotal IS NULL OR subtotal = 0'
                    ))
                    db.session.commit()
                    logger.info(f"✅ Pedidos antigos atualizados (subtotal=total)")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao atualizar pedidos: {str(e)[:60]}")
            else:
                logger.info("✅ Todas as colunas do pedido já existem")

            # Índice único para o identificador idempotente enviado pelo app.
            # WHERE permite vários pedidos antigos com valor nulo.
            try:
                with db.engine.begin() as conn:
                    conn.execute(db.text(
                        'CREATE UNIQUE INDEX IF NOT EXISTS '
                        'ix_order_client_reference_unique ON "order" (client_reference) '
                        'WHERE client_reference IS NOT NULL'
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Índice de idempotência: {str(e)[:60]}")

            try:
                with db.engine.begin() as conn:
                    conn.execute(db.text(
                        'CREATE UNIQUE INDEX IF NOT EXISTS '
                        'ix_order_external_payment_id_unique ON "order" (external_payment_id) '
                        'WHERE external_payment_id IS NOT NULL'
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Índice de pagamento externo: {str(e)[:60]}")
        else:
            logger.info("ℹ️ Tabela 'order' ainda não existe")
            
    except Exception as e:
        logger.warning(f"⚠️ Erro na migração (não crítico): {str(e)[:100]}")
        # Não falhar a inicialização por causa da migração

    # Versão de sessão móvel para permitir revogação no logout.
    try:
        if 'user' in existing_tables:
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            user_required_columns = {
                'mobile_token_version': 'INTEGER DEFAULT 0 NOT NULL',
                'is_active': 'BOOLEAN DEFAULT TRUE NOT NULL',
                'deleted_at': 'TIMESTAMP',
                'password_reset_hash': 'VARCHAR(256)',
                'password_reset_expires_at': 'TIMESTAMP',
                'password_reset_attempts': 'INTEGER DEFAULT 0 NOT NULL',
            }
            missing_user_columns = [
                name for name in user_required_columns if name not in user_columns
            ]
            if missing_user_columns:
                with db.engine.begin() as conn:
                    for name in missing_user_columns:
                        conn.execute(db.text(
                            f'ALTER TABLE "user" ADD COLUMN {name} '
                            f'{user_required_columns[name]}'
                        ))
                logger.info("✅ Colunas de segurança da conta móvel adicionadas")
    except Exception as e:
        logger.warning(f"⚠️ Migração de sessão móvel: {str(e)[:100]}")

    # Só consulte o modelo User depois que todas as suas colunas existirem.
    # Isso é essencial em bancos criados por versões anteriores do aplicativo.
    try:
        from werkzeug.security import generate_password_hash

        admin_exists = User.query.filter_by(is_admin=True).first() is not None
        admin_email = os.getenv('EJM_ADMIN_EMAIL')
        admin_password = os.getenv('EJM_ADMIN_PASSWORD')

        if not admin_exists and admin_email and admin_password:
            if len(admin_password) < 12:
                raise ValueError("EJM_ADMIN_PASSWORD deve ter pelo menos 12 caracteres")

            normalized_email = admin_email.strip().lower()
            admin = User.query.filter_by(email=normalized_email).first()
            if admin:
                admin.senha_hash = generate_password_hash(admin_password)
                admin.is_admin = True
                admin.is_active = True
            else:
                admin = User(
                    nome='Administrador',
                    email=normalized_email,
                    senha_hash=generate_password_hash(admin_password),
                    is_admin=True,
                    is_active=True,
                )
                db.session.add(admin)
            db.session.commit()
            logger.info("✅ Usuário administrador inicial configurado")
        elif not admin_exists:
            logger.warning(
                "⚠️ Nenhum administrador cadastrado. Execute garantir_admin.py "
                "ou configure EJM_ADMIN_EMAIL e EJM_ADMIN_PASSWORD no primeiro deploy."
            )
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao configurar admin após as migrações: {e}")

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
    payment_bp, init_payment,
    mobile_bp, init_mobile
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

# API do aplicativo usa JWT Bearer, não cookies de sessão; por isso não está
# sujeita a CSRF de navegador.
init_mobile(db, models_dict, app.config, logger, email_service)
app.register_blueprint(mobile_bp)
csrf.exempt(mobile_bp)
# Limites específicos para reduzir força bruta e criação automatizada de contas.
# A aplicação dos decorators ocorre após o registro para evitar dependência
# circular entre o blueprint móvel e esta instância do Limiter.
app.view_functions['mobile.login'] = limiter.limit("5 per minute")(app.view_functions['mobile.login'])
app.view_functions['mobile.register'] = limiter.limit("3 per hour")(app.view_functions['mobile.register'])
app.view_functions['mobile.refresh_token'] = limiter.limit("30 per hour")(
    app.view_functions['mobile.refresh_token']
)
app.view_functions['mobile.request_password_reset'] = limiter.limit("3 per hour")(
    app.view_functions['mobile.request_password_reset']
)
app.view_functions['mobile.confirm_password_reset'] = limiter.limit("10 per hour")(
    app.view_functions['mobile.confirm_password_reset']
)
app.view_functions['mobile.change_password'] = limiter.limit("5 per hour")(
    app.view_functions['mobile.change_password']
)
app.view_functions['mobile.delete_account'] = limiter.limit("3 per hour")(
    app.view_functions['mobile.delete_account']
)
# O Stripe já autentica o webhook por assinatura e pode reenviar eventos; não
# deixe o limite global impedir confirmações legítimas de pagamento.
limiter.exempt(app.view_functions['mobile.stripe_webhook'])
limiter.exempt(app.view_functions['mobile.health'])
logger.info("✅ Blueprint do aplicativo móvel registrado")

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
