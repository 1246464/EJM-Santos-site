# ============================================
# models/__init__.py — Modelos do Banco de Dados
# ============================================

from .user import create_user_model
from .product import create_product_model
from .order import create_order_model
from .review import create_review_model
from .cart import create_cart_model

# Importar db do app_new para criar os models
# Será sobrescrito quando importado de app_new
User = None
Product = None
Order = None
OrderItem = None
Review = None
CartItem = None

def init_models(db):
    """Inicializa todos os models com a instância do db"""
    global User, Product, Order, OrderItem, Review, CartItem
    
    User = create_user_model(db)
    Product = create_product_model(db)
    Order, OrderItem = create_order_model(db)
    Review = create_review_model(db)
    CartItem = create_cart_model(db)
    
    return User, Product, Order, OrderItem, Review, CartItem

__all__ = [
    'User',
    'Product',
    'Order',
    'OrderItem',
    'Review',
    'CartItem',
    'init_models'
]
