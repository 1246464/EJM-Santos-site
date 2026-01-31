# ============================================
# __init__.py — Inicialização dos routes
# ============================================

from .auth import auth_bp, init_auth
from .admin import admin_bp, init_admin
from .products import products_bp, init_products

__all__ = [
    'auth_bp',
    'init_auth',
    'admin_bp',
    'init_admin',
    'products_bp',
    'init_products'
]
