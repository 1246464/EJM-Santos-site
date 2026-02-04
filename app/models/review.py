# ============================================
# models/review.py — Modelo de Avaliação
# ============================================

from datetime import datetime

def create_review_model(db):
    """Factory para criar o modelo Review com a instância db correta."""
    
    class Review(db.Model):
        """Modelo de avaliação de produto"""
        __tablename__ = 'review'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
        comentario = db.Column(db.Text)
        nota = db.Column(db.Integer, nullable=False)  # 1 a 5
        created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        
        def __repr__(self):
            return f'<Review {self.id}: Product {self.product_id} - {self.nota}★>'
        
        def to_dict(self):
            """Converte para dicionário"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'product_id': self.product_id,
                'comentario': self.comentario,
                'nota': self.nota,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    return Review
