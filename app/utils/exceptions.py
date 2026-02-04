# ============================================
# exceptions.py — Exceções Customizadas
# ============================================

class EJMBaseException(Exception):
    """Exceção base para todas as exceções customizadas da aplicação"""
    status_code = 500
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(EJMBaseException):
    """Erro de validação de dados"""
    status_code = 400


class AuthenticationError(EJMBaseException):
    """Erro de autenticação"""
    status_code = 401


class AuthorizationError(EJMBaseException):
    """Erro de autorização (sem permissão)"""
    status_code = 403


class NotFoundError(EJMBaseException):
    """Recurso não encontrado"""
    status_code = 404


class DatabaseError(EJMBaseException):
    """Erro relacionado ao banco de dados"""
    status_code = 500


class EmailError(EJMBaseException):
    """Erro ao enviar email"""
    status_code = 500


class PaymentError(EJMBaseException):
    """Erro relacionado a pagamento"""
    status_code = 500


class StockError(EJMBaseException):
    """Erro relacionado a estoque"""
    status_code = 400


class FileUploadError(EJMBaseException):
    """Erro no upload de arquivo"""
    status_code = 400
