# ============================================
# models/payment_method.py — Modelo de Método de Pagamento
# ============================================

from datetime import datetime


def create_payment_method_model(db):
    """
    Factory para criar o modelo PaymentMethod com a instância db correta.
    Armazena métodos de pagamento salvos (cartões via Stripe).
    """
    
    class PaymentMethod(db.Model):
        """Modelo de método de pagamento salvo (Stripe)"""
        __tablename__ = 'payment_method'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        
        # Apelido do cartão para facilitar identificação
        apelido = db.Column(db.String(50), nullable=False)  # Ex: "Cartão principal", "Nubank"
        
        # Dados do Stripe
        stripe_payment_method_id = db.Column(db.String(200), nullable=False, unique=True, index=True)
        # Armazena o ID retornado pelo Stripe (ex: pm_1A2B3C...)
        
        # Informações do cartão para exibição (últimos 4 dígitos, bandeira)
        # NÃO armazenamos número completo ou CVV por segurança!
        card_brand = db.Column(db.String(20))  # visa, mastercard, amex, etc
        card_last4 = db.Column(db.String(4))   # Últimos 4 dígitos
        card_exp_month = db.Column(db.Integer) # Mês de expiração (1-12)
        card_exp_year = db.Column(db.Integer)  # Ano de expiração (2024, 2025...)
        
        # Cartão padrão para checkout rápido
        is_default = db.Column(db.Boolean, default=False)
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<PaymentMethod {self.id}: {self.apelido} (*{self.card_last4}) - User {self.user_id}>'
        
        def to_dict(self):
            """Converte para dicionário (dados seguros para frontend)"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'apelido': self.apelido,
                'stripe_payment_method_id': self.stripe_payment_method_id,
                'card_brand': self.card_brand,
                'card_last4': self.card_last4,
                'card_exp_month': self.card_exp_month,
                'card_exp_year': self.card_exp_year,
                'is_default': self.is_default,
                'card_display': self.get_card_display(),
                'is_expired': self.is_expired(),
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        
        def get_card_display(self):
            """Retorna representação do cartão para exibição"""
            brand_emoji = {
                'visa': '💳',
                'mastercard': '💳',
                'amex': '💳',
                'elo': '💳',
                'discover': '💳'
            }
            emoji = brand_emoji.get(self.card_brand.lower() if self.card_brand else '', '💳')
            brand = self.card_brand.upper() if self.card_brand else 'CARD'
            return f"{emoji} {brand} •••• {self.card_last4}"
        
        def is_expired(self):
            """Verifica se o cartão está expirado"""
            if not self.card_exp_month or not self.card_exp_year:
                return False
            
            now = datetime.utcnow()
            # Cartão expira no último dia do mês
            if self.card_exp_year < now.year:
                return True
            if self.card_exp_year == now.year and self.card_exp_month < now.month:
                return True
            return False
    
    return PaymentMethod
