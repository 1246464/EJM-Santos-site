# ============================================
# config.py — Configurações Seguras por Ambiente
# ============================================

import os
import secrets
from pathlib import Path


class Config:
    """Configuração base - comum a todos os ambientes"""
    
    # Diretórios
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / "instance"
    LOGS_DIR = BASE_DIR / "logs"
    UPLOAD_FOLDER = BASE_DIR / "static" / "imagens"
    
    # Segurança
    SECRET_KEY = os.getenv("EJM_SECRET")
    if not SECRET_KEY:
        # Em desenvolvimento, gerar chave temporária
        # Em produção, DEVE ser configurada como variável de ambiente
        import sys
        if os.getenv("FLASK_ENV") == "production":
            print("❌ ERRO: EJM_SECRET não configurado em produção!")
            print("Configure no Render: Dashboard > Environment > Add Secret File")
            print("Nome: EJM_SECRET")
            print(f"Valor: {secrets.token_hex(32)}")
            sys.exit(1)
        else:
            SECRET_KEY = secrets.token_hex(32)
            print(f"⚠️  Usando SECRET_KEY temporária (desenvolvimento)")
            print(f"   Para produção, defina EJM_SECRET no .env")
    
    # Banco de dados
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload de arquivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "EJM Santos - Mel Natural")
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    
    # URLs
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")
    
    # HTTPS e Proxy
    FORCE_HTTPS = False  # Será True em production
    TRUST_PROXY_HEADERS = True  # Confiar em X-Forwarded-Proto, X-Real-IP, etc.
    PREFERRED_URL_SCHEME = 'http'  # Será 'https' em production
    
    # Sessão (padrões - serão sobrescritos por ambiente)
    SESSION_COOKIE_SECURE = False  # Será True apenas em production
    SESSION_COOKIE_HTTPONLY = True  # Não acessível via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção CSRF
    SESSION_COOKIE_NAME = 'ejm_session'  # Nome customizado
    PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24 horas
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token não expira (para checkout longo)
    WTF_CSRF_SSL_STRICT = False  # Permite desenvolvimento local
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']  # Headers aceitos para AJAX
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']  # Métodos protegidos
    WTF_CSRF_FIELD_NAME = 'csrf_token'  # Nome do campo no formulário
    WTF_CSRF_COOKIE_NAME = 'csrf_token'  # Nome do cookie
    WTF_CSRF_COOKIE_HTTPONLY = False  # Precisa ser acessível para AJAX
    WTF_CSRF_COOKIE_SECURE = False  # Será True em production
    WTF_CSRF_COOKIE_SAMESITE = 'Lax'  # Proteção adicional
    
    # Backups
    BACKUP_ENABLED = True  # Habilitar sistema de backups
    BACKUP_DIR = BASE_DIR / "backups"  # Diretório de backups
    BACKUP_KEEP_COUNT = 10  # Manter últimos N backups
    BACKUP_KEEP_DAYS = 30  # Manter backups dos últimos N dias
    BACKUP_INCLUDE_DB = True  # Incluir banco de dados
    BACKUP_INCLUDE_IMAGES = True  # Incluir imagens
    BACKUP_INCLUDE_LOGS = False  # Incluir logs (desabilitado por padrão)
    BACKUP_AUTO_CLEANUP = True  # Limpeza automática de backups antigos
    
    # Rate Limiting (padrão)
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento"""
    
    DEBUG = True
    TESTING = False
    
    # Banco local
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Config.INSTANCE_DIR / 'ejm_dev.db'}"
    SQLALCHEMY_ECHO = True  # Log de queries SQL
    
    # HTTPS desabilitado em desenvolvimento
    FORCE_HTTPS = False
    PREFERRED_URL_SCHEME = 'http'
    
    # Sessão menos restritiva para desenvolvimento
    SESSION_COOKIE_SECURE = False  # HTTP permitido
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_COOKIE_SECURE = False
    
    # CSRF habilitado mas com configuração flexível para HTTP
    WTF_CSRF_ENABLED = True
    
    # Rate limiting mais permissivo
    RATELIMIT_ENABLED = False  # Desabilitar em dev para testes


class TestingConfig(Config):
    """Configuração de testes"""
    
    DEBUG = False
    TESTING = True
    
    # Banco em memória
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # HTTPS desabilitado em testes
    FORCE_HTTPS = False
    PREFERRED_URL_SCHEME = 'http'
    
    # Desabilitar proteções para testes
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    
    # Email mock
    EMAIL_USER = "test@example.com"
    EMAIL_PASSWORD = "test"


class ProductionConfig(Config):
    """Configuração de produção"""
    
    DEBUG = False
    TESTING = False
    
    # Banco de produção (pode ser PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Config.INSTANCE_DIR / 'ejm.db'}"
    )
    
    # HTTPS obrigatório
    FORCE_HTTPS = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Segurança máxima de cookies
    SESSION_COOKIE_SECURE = True  # HTTPS obrigatório
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_COOKIE_SECURE = True  # Cookie CSRF também via HTTPS
    
    # Rate limiting rígido
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "memory://")
    
    # Validações de produção
    @classmethod
    def validate(cls):
        """Valida configurações críticas de produção"""
        errors = []
        
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY muito fraca (mín. 32 chars)")
        
        if not cls.STRIPE_SECRET_KEY:
            errors.append("STRIPE_SECRET_KEY não configurada")
        
        if cls.PUBLIC_BASE_URL.startswith("http://"):
            errors.append("PUBLIC_BASE_URL deve usar HTTPS em produção")
        
        if errors:
            raise ValueError(f"❌ Erros de configuração:\n" + "\n".join(f"  - {e}" for e in errors))


# Mapa de ambientes
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config(env=None):
    """Retorna a configuração baseada no ambiente"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'production')
    
    config_class = config_map.get(env, ProductionConfig)
    
    # Validar produção
    if config_class == ProductionConfig:
        config_class.validate()
    
    return config_class
