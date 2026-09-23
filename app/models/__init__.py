# ============================================
# models/__init__.py — Modelos do Banco de Dados
# ============================================

from .user import create_user_model
from .product import create_product_model
from .order import create_order_model
from .review import create_review_model
from .cart import create_cart_model
from .address import create_address_model
from .payment_method import create_payment_method_model
from .logistics import create_logistics_models

# O objeto db é injetado por application.py ao inicializar os modelos.
User = None
Product = None
Order = None
OrderItem = None
Review = None
CartItem = None
Address = None
PaymentMethod = None
Supplier = None
Brand = None
FulfillmentOrigin = None
ProductInventory = None
DeliverySettings = None

def init_models(db):
    """Inicializa todos os models com a instância do db"""
    global User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod
    global Supplier, Brand, FulfillmentOrigin, ProductInventory, DeliverySettings
    
    User = create_user_model(db)
    Product = create_product_model(db)
    Order, OrderItem = create_order_model(db)
    Review = create_review_model(db)
    CartItem = create_cart_model(db)
    Address = create_address_model(db)
    PaymentMethod = create_payment_method_model(db)
    (
        Supplier,
        Brand,
        FulfillmentOrigin,
        ProductInventory,
        DeliverySettings,
    ) = create_logistics_models(db)
    
    return User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod

__all__ = [
    'User',
    'Product',
    'Order',
    'OrderItem',
    'Review',
    'CartItem',
    'Address',
    'PaymentMethod',
    'Supplier',
    'Brand',
    'FulfillmentOrigin',
    'ProductInventory',
    'DeliverySettings',
    'init_models'
]
