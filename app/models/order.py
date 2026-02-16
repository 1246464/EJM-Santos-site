# ============================================
# models/order.py — Modelos de Pedido
# ============================================

from datetime import datetime

def create_order_model(db):
    """Factory para criar os modelos Order e OrderItem com a instância db correta."""
    
    class Order(db.Model):
        """Modelo de pedido"""
        __tablename__ = 'order'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        total = db.Column(db.Float, nullable=False)
        status = db.Column(db.String(50), default="Pendente", index=True)
        # Status: Pendente, Pago, Agendado, Saiu para Entrega, Entregue, Cancelado
        
        # Valores de entrega
        subtotal = db.Column(db.Float, nullable=False, default=0)  # Total dos produtos
        delivery_fee = db.Column(db.Float, default=0)  # Taxa de entrega
        delivery_distance_km = db.Column(db.Float)  # Distância em km
        
        # Endereço de entrega (entrega local)
        endereco_rua = db.Column(db.String(200))
        endereco_numero = db.Column(db.String(20))
        endereco_complemento = db.Column(db.String(100))
        endereco_bairro = db.Column(db.String(100))
        endereco_cidade = db.Column(db.String(100))
        telefone = db.Column(db.String(20))
        
        # Agendamento de entrega
        delivery_date = db.Column(db.DateTime)  # Data/hora agendada para entrega
        delivery_scheduled_at = db.Column(db.DateTime)  # Quando foi agendado
        delivery_notes = db.Column(db.Text)  # Observações sobre a entrega
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        
        # Relacionamento
        items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
        
        def __repr__(self):
            return f'<Order {self.id}: {self.status}>'
        
        def to_dict(self, include_items=False):
            """Converte para dicionário"""
            data = {
                'id': self.id,
                'user_id': self.user_id,
                'total': self.total,
                'subtotal': self.subtotal,
                'delivery_fee': self.delivery_fee,
                'delivery_distance_km': self.delivery_distance_km,
                'status': self.status,
                'endereco': {
                    'rua': self.endereco_rua,
                    'numero': self.endereco_numero,
                    'complemento': self.endereco_complemento,
                    'bairro': self.endereco_bairro,
                    'cidade': self.endereco_cidade,
                    'telefone': self.telefone
                },
                'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
                'delivery_scheduled_at': self.delivery_scheduled_at.isoformat() if self.delivery_scheduled_at else None,
                'delivery_notes': self.delivery_notes,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
            
            if include_items:
                data['items'] = [item.to_dict() for item in self.items]
            
            return data
    
    
    class OrderItem(db.Model):
        """Item de um pedido"""
        __tablename__ = 'order_item'
        
        id = db.Column(db.Integer, primary_key=True)
        order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
        quantidade = db.Column(db.Integer, nullable=False)
        preco_unitario = db.Column(db.Float, nullable=False)
        
        def __repr__(self):
            return f'<OrderItem {self.id}: Order {self.order_id}, Product {self.product_id}>'
        
        def to_dict(self):
            """Converte para dicionário"""
            return {
                'id': self.id,
                'order_id': self.order_id,
                'product_id': self.product_id,
                'quantidade': self.quantidade,
                'preco_unitario': self.preco_unitario,
                'subtotal': self.quantidade * self.preco_unitario
            }
    
    return Order, OrderItem
