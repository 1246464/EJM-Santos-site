# ============================================
# models/user.py — Modelo de Usuário
# ============================================

from datetime import datetime


def create_user_model(db):
    """
    Factory para criar o modelo User com a instância db correta.
    Para uso direto, importe de __init__.py
    """
    
    class User(db.Model):
        """Modelo de usuário do sistema"""
        __tablename__ = 'user'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(120), nullable=False)
        email = db.Column(db.String(150), unique=True, nullable=False, index=True)
        senha_hash = db.Column(db.String(256), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        # Incrementado no logout móvel para invalidar tokens emitidos antes dele.
        mobile_token_version = db.Column(db.Integer, default=0, nullable=False)
        is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
        deleted_at = db.Column(db.DateTime)
        password_reset_hash = db.Column(db.String(256))
        password_reset_expires_at = db.Column(db.DateTime)
        password_reset_attempts = db.Column(db.Integer, default=0, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relacionamentos
        orders = db.relationship('Order', backref='user', lazy=True)
        reviews = db.relationship('Review', backref='user', lazy=True)
        cart_items = db.relationship('CartItem', backref='user', lazy=True)
        addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
        payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True, cascade='all, delete-orphan')
        
        def __repr__(self):
            return f'<User {self.id}: {self.email}>'
        
        def to_dict(self):
            """Converte para dicionário (sem senha)"""
            return {
                'id': self.id,
                'nome': self.nome,
                'email': self.email,
                'is_admin': self.is_admin,
                'is_active': self.is_active,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    return User
