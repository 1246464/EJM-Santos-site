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
        raise ValueError("❌ EJM_SECRET não configurado! Gere uma chave segura com: python -c 'import secrets; print(secrets.token_hex(32))'")
    
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
    
    # Sessão
    SESSION_COOKIE_SECURE = True  # Apenas HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Não acessível via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção CSRF
    PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24 horas
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token não expira (para checkout longo)
    WTF_CSRF_SSL_STRICT = False  # Permite desenvolvimento local
    
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
    
    # Sessão menos restritiva para desenvolvimento
    SESSION_COOKIE_SECURE = False  # HTTP permitido
    WTF_CSRF_SSL_STRICT = False
    
    # Rate limiting mais permissivo
    RATELIMIT_ENABLED = False  # Desabilitar em dev para testes


class TestingConfig(Config):
    """Configuração de testes"""
    
    DEBUG = False
    TESTING = True
    
    # Banco em memória
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
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
    
    # Segurança máxima
    SESSION_COOKIE_SECURE = True  # HTTPS obrigatório
    WTF_CSRF_SSL_STRICT = True
    
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
