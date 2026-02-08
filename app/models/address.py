# ============================================
# models/address.py — Modelo de Endereço
# ============================================

from datetime import datetime


def create_address_model(db):
    """
    Factory para criar o modelo Address com a instância db correta.
    Permite que usuários salvem múltiplos endereços.
    """
    
    class Address(db.Model):
        """Modelo de endereço salvo do usuário"""
        __tablename__ = 'address'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        
        # Apelido do endereço para facilitar identificação
        apelido = db.Column(db.String(50), nullable=False)  # Ex: "Casa", "Trabalho", "Casa da mãe"
        
        # Dados do endereço
        rua = db.Column(db.String(200), nullable=False)
        numero = db.Column(db.String(20), nullable=False)
        complemento = db.Column(db.String(100))
        bairro = db.Column(db.String(100), nullable=False)
        cidade = db.Column(db.String(100), nullable=False)
        estado = db.Column(db.String(2))  # UF: SP, RJ, etc
        cep = db.Column(db.String(10))
        
        # Telefone de contato para entrega
        telefone = db.Column(db.String(20), nullable=False)
        
        # Endereço padrão para checkout rápido
        is_default = db.Column(db.Boolean, default=False)
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<Address {self.id}: {self.apelido} - User {self.user_id}>'
        
        def to_dict(self):
            """Converte para dicionário"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'apelido': self.apelido,
                'rua': self.rua,
                'numero': self.numero,
                'complemento': self.complemento,
                'bairro': self.bairro,
                'cidade': self.cidade,
                'estado': self.estado,
                'cep': self.cep,
                'telefone': self.telefone,
                'is_default': self.is_default,
                'endereco_completo': self.get_endereco_completo(),
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        
        def get_endereco_completo(self):
            """Retorna endereço formatado para exibição"""
            partes = [
                f"{self.rua}, {self.numero}",
                self.complemento if self.complemento else None,
                self.bairro,
                self.cidade,
                self.estado if self.estado else None,
                self.cep if self.cep else None
            ]
            return " - ".join([p for p in partes if p])
        
        def get_endereco_resumido(self):
            """Retorna endereço resumido (uma linha)"""
            return f"{self.rua}, {self.numero} - {self.bairro}, {self.cidade}"
    
    return Address
