# ============================================
# models/cart.py — Modelo de Carrinho
# ============================================

def create_cart_model(db):
    """Factory para criar o modelo CartItem com a instância db correta."""
    
    class CartItem(db.Model):
        """Item do carrinho de compras"""
        __tablename__ = 'cart_item'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
        quantity = db.Column(db.Integer, default=1, nullable=False)
        
        def __repr__(self):
            return f'<CartItem {self.id}: User {self.user_id}, Product {self.product_id} x{self.quantity}>'
        
        def to_dict(self):
            """Converte para dicionário"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'product_id': self.product_id,
                'quantity': self.quantity
            }
    
    return CartItem
