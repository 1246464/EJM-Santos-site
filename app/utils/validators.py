# ============================================
# validators.py — Validações de Dados
# ============================================

import re
from typing import Dict, Any, List, Tuple


class ValidationError(Exception):
    """Exceção personalizada para erros de validação"""
    pass


class Validator:
    """Classe para validações de dados"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Valida formato de email.
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not email:
            return False, "Email é obrigatório"
        
        if len(email) > 150:
            return False, "Email muito longo (máximo 150 caracteres)"
        
        # Regex simples para validação de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        return True, ""
    
    @staticmethod
    def validate_password(senha: str) -> Tuple[bool, str]:
        """
        Valida senha.
        
        Requisitos:
        - Mínimo 6 caracteres
        - Máximo 50 caracteres
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not senha:
            return False, "Senha é obrigatória"
        
        if len(senha) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        
        if len(senha) > 50:
            return False, "Senha muito longa (máximo 50 caracteres)"
        
        return True, ""
    
    @staticmethod
    def validate_name(nome: str) -> Tuple[bool, str]:
        """
        Valida nome.
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not nome:
            return False, "Nome é obrigatório"
        
        if len(nome) < 3:
            return False, "Nome deve ter pelo menos 3 caracteres"
        
        if len(nome) > 120:
            return False, "Nome muito longo (máximo 120 caracteres)"
        
        # Apenas letras, espaços e alguns caracteres especiais
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\'-]+$', nome):
            return False, "Nome contém caracteres inválidos"
        
        return True, ""
    
    @staticmethod
    def validate_price(preco: Any) -> Tuple[bool, str]:
        """
        Valida preço.
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        try:
            preco_float = float(preco)
        except (ValueError, TypeError):
            return False, "Preço deve ser um número válido"
        
        if preco_float < 0:
            return False, "Preço não pode ser negativo"
        
        if preco_float > 999999.99:
            return False, "Preço muito alto (máximo R$ 999.999,99)"
        
        return True, ""
    
    @staticmethod
    def validate_quantity(quantidade: Any) -> Tuple[bool, str]:
        """
        Valida quantidade.
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        try:
            qtd_int = int(quantidade)
        except (ValueError, TypeError):
            return False, "Quantidade deve ser um número inteiro"
        
        if qtd_int < 1:
            return False, "Quantidade deve ser pelo menos 1"
        
        if qtd_int > 9999:
            return False, "Quantidade muito alta (máximo 9999)"
        
        return True, ""
    
    @staticmethod
    def validate_product_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados completos de um produto.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        errors = []
        
        # Validar título
        titulo = data.get('titulo', '')
        if not titulo or len(titulo.strip()) < 3:
            errors.append("Título deve ter pelo menos 3 caracteres")
        elif len(titulo) > 120:
            errors.append("Título muito longo (máximo 120 caracteres)")
        
        # Validar descrição
        descricao = data.get('descricao', '')
        if descricao and len(descricao) > 5000:
            errors.append("Descrição muito longa (máximo 5000 caracteres)")
        
        # Validar preço
        is_valid, msg = Validator.validate_price(data.get('preco'))
        if not is_valid:
            errors.append(msg)
        
        # Validar estoque
        estoque = data.get('estoque')
        if estoque is not None:
            try:
                estoque_int = int(estoque)
                if estoque_int < 0:
                    errors.append("Estoque não pode ser negativo")
            except (ValueError, TypeError):
                errors.append("Estoque deve ser um número inteiro")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de cadastro de usuário.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        errors = []
        
        # Validar nome
        is_valid, msg = Validator.validate_name(data.get('nome', ''))
        if not is_valid:
            errors.append(msg)
        
        # Validar email
        is_valid, msg = Validator.validate_email(data.get('email', ''))
        if not is_valid:
            errors.append(msg)
        
        # Validar senha
        is_valid, msg = Validator.validate_password(data.get('senha', ''))
        if not is_valid:
            errors.append(msg)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_address(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de endereço.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        errors = []
        
        required_fields = {
            'endereco_rua': 'Rua',
            'endereco_numero': 'Número',
            'endereco_bairro': 'Bairro',
            'endereco_cidade': 'Cidade'
        }
        
        for field, label in required_fields.items():
            if not data.get(field):
                errors.append(f"{label} é obrigatório")
        
        # Validar CEP se fornecido
        cep = data.get('cep', '')
        if cep:
            cep_limpo = re.sub(r'\D', '', cep)
            if len(cep_limpo) != 8:
                errors.append("CEP deve ter 8 dígitos")
        
        # Validar telefone
        telefone = data.get('telefone', '')
        if telefone:
            telefone_limpo = re.sub(r'\D', '', telefone)
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
                errors.append("Telefone inválido (deve ter 10 ou 11 dígitos)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_string(texto: str, max_length: int = None) -> str:
        """
        Remove caracteres perigosos e limita tamanho.
        
        Args:
            texto: String a ser sanitizada
            max_length: Tamanho máximo (opcional)
        
        Returns:
            String sanitizada
        """
        if not texto:
            return ""
        
        # Remove espaços extras
        texto = texto.strip()
        
        # Limita tamanho se especificado
        if max_length and len(texto) > max_length:
            texto = texto[:max_length]
        
        return texto
