# ============================================
# error_handlers.py — Handlers de Erro Globais
# ============================================

from flask import jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import HTTPException
import traceback


def register_error_handlers(app, logger):
    """Registra todos os handlers de erro na aplicação"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Requisição inválida"""
        logger.warning(f"Bad Request (400): {error} - URL: {request.url}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Requisição inválida",
                "message": str(error.description) if hasattr(error, 'description') else str(error)
            }), 400
        
        return render_template("erro.html", 
                             mensagem="Requisição inválida",
                             detalhes=str(error.description) if hasattr(error, 'description') else None), 400
    
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Não autenticado"""
        logger.warning(f"Unauthorized (401): {error} - URL: {request.url} - IP: {request.remote_addr}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Não autenticado",
                "message": "Você precisa fazer login para acessar este recurso"
            }), 401
        
        return render_template("erro.html", 
                             mensagem="Acesso não autorizado",
                             detalhes="Você precisa fazer login para acessar esta página"), 401
    
    
    @app.errorhandler(403)
    def forbidden(error):
        """Sem permissão"""
        logger.warning(f"Forbidden (403): {error} - URL: {request.url} - User: {request.headers.get('User-Agent')}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Acesso negado",
                "message": "Você não tem permissão para acessar este recurso"
            }), 403
        
        return render_template("erro.html", 
                             mensagem="Acesso negado",
                             detalhes="Você não tem permissão para acessar esta página"), 403
    
    
    @app.errorhandler(404)
    def not_found(error):
        """Página não encontrada"""
        logger.info(f"Not Found (404): {request.url}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Não encontrado",
                "message": "O recurso solicitado não foi encontrado"
            }), 404
        
        return render_template("erro.html", 
                             mensagem="Página não encontrada",
                             detalhes="A página que você está procurando não existe"), 404
    
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Método HTTP não permitido"""
        logger.warning(f"Method Not Allowed (405): {request.method} {request.url}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Método não permitido",
                "message": f"O método {request.method} não é permitido para esta URL"
            }), 405
        
        return render_template("erro.html", 
                             mensagem="Método não permitido",
                             detalhes=f"O método {request.method} não é permitido para esta página"), 405
    
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Arquivo muito grande"""
        logger.warning(f"Request Entity Too Large (413): {request.url}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Arquivo muito grande",
                "message": "O arquivo enviado excede o tamanho máximo permitido"
            }), 413
        
        return render_template("erro.html", 
                             mensagem="Arquivo muito grande",
                             detalhes="O arquivo enviado excede o tamanho máximo permitido"), 413
    
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Erro interno do servidor"""
        logger.error(f"Internal Server Error (500): {error}", exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Erro interno do servidor",
                "message": "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."
            }), 500
        
        return render_template("erro.html", 
                             mensagem="Erro interno do servidor",
                             detalhes="Ocorreu um erro inesperado. Nossa equipe foi notificada."), 500
    
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Erro de integridade do banco de dados (duplicação, constraint)"""
        logger.error(f"IntegrityError: {error}", exc_info=True)
        
        # Tentar fazer rollback
        try:
            from flask import current_app
            db = current_app.extensions['sqlalchemy'].db
            db.session.rollback()
        except:
            pass
        
        message = "Erro ao processar dados: violação de integridade"
        if 'UNIQUE constraint failed' in str(error):
            message = "Este registro já existe no sistema"
        elif 'FOREIGN KEY constraint failed' in str(error):
            message = "Erro de referência: registro relacionado não encontrado"
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Erro de integridade",
                "message": message
            }), 400
        
        return render_template("erro.html", 
                             mensagem="Erro ao processar dados",
                             detalhes=message), 400
    
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Erro genérico do SQLAlchemy"""
        logger.error(f"SQLAlchemyError: {error}", exc_info=True)
        
        # Tentar fazer rollback
        try:
            from flask import current_app
            db = current_app.extensions['sqlalchemy'].db
            db.session.rollback()
        except:
            pass
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Erro no banco de dados",
                "message": "Ocorreu um erro ao acessar o banco de dados"
            }), 500
        
        return render_template("erro.html", 
                             mensagem="Erro no banco de dados",
                             detalhes="Ocorreu um erro ao processar sua solicitação"), 500
    
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handler genérico para exceções HTTP do Werkzeug"""
        logger.warning(f"HTTPException ({error.code}): {error.description} - URL: {request.url}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": error.name,
                "message": error.description
            }), error.code
        
        return render_template("erro.html", 
                             mensagem=error.name,
                             detalhes=error.description), error.code
    
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handler genérico para qualquer exceção não tratada"""
        logger.error(f"Unhandled Exception: {error}", exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Tentar fazer rollback no banco
        try:
            from flask import current_app
            db = current_app.extensions['sqlalchemy'].db
            db.session.rollback()
        except:
            pass
        
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Erro inesperado",
                "message": "Ocorreu um erro inesperado. Por favor, tente novamente."
            }), 500
        
        return render_template("erro.html", 
                             mensagem="Erro inesperado",
                             detalhes="Ocorreu um erro inesperado. Nossa equipe foi notificada."), 500
    
    
    # Handler para exceções customizadas
    try:
        from .exceptions import EJMBaseException
    except ImportError:
        from app.utils.exceptions import EJMBaseException
    
    @app.errorhandler(EJMBaseException)
    def handle_custom_exception(error):
        """Handler para exceções customizadas da aplicação"""
        logger.error(f"{error.__class__.__name__}: {error.message}")
        
        if request.path.startswith('/api/'):
            return jsonify(error.to_dict()), error.status_code
        
        return render_template("erro.html", 
                             mensagem=error.message,
                             detalhes=None), error.status_code
    
    
    logger.info("✅ Error handlers registrados com sucesso")
