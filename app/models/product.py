# ============================================
# models/product.py — Modelo de Produto
# ============================================

from datetime import datetime

def create_product_model(db):
    """Factory para criar o modelo Product com a instância db correta."""
    
    class Product(db.Model):
        """Modelo de produto"""
        __tablename__ = 'product'
        
        id = db.Column(db.Integer, primary_key=True)
        titulo = db.Column(db.String(120), nullable=False)
        descricao = db.Column(db.Text)
        preco = db.Column(db.Float, nullable=False)
        imagem = db.Column(db.String(256))
        estoque = db.Column(db.Integer, default=0, nullable=False)
        categoria = db.Column(db.String(40), default="mel", nullable=False)
        origem = db.Column(db.String(80))
        beneficios = db.Column(db.String(255))
        sem_adicao_acucar = db.Column(db.Boolean, default=False, nullable=False)
        destaque = db.Column(db.Boolean, default=False, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relacionamentos
        order_items = db.relationship('OrderItem', backref='product', lazy=True)
        reviews = db.relationship('Review', backref='product', lazy=True)
        cart_items = db.relationship('CartItem', backref='product', lazy=True)
        
        def __repr__(self):
            return f'<Product {self.id}: {self.titulo}>'
        
        def to_dict(self, include_reviews=False):
            """Converte para dicionário"""
            data = {
                'id': self.id,
                'titulo': self.titulo,
                'descricao': self.descricao,
                'preco': self.preco,
                'imagem': self.imagem,
                'estoque': self.estoque,
                'categoria': self.categoria,
                'origem': self.origem,
                'beneficios': self.beneficios,
                'sem_adicao_acucar': self.sem_adicao_acucar,
                'destaque': self.destaque,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
            
            if include_reviews:
                data['reviews'] = [r.to_dict() for r in self.reviews]
            
            return data
    
    return Product
