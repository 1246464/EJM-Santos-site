# ============================================
# logger.py — Sistema de Logging Centralizado
# ============================================

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(app):
    """
    Configura sistema de logging para a aplicação.
    
    Níveis de log:
    - DEBUG: Informações detalhadas para diagnóstico
    - INFO: Confirmação de que as coisas estão funcionando
    - WARNING: Indicação de algo inesperado, mas a aplicação continua
    - ERROR: Erro mais grave, alguma funcionalidade não funcionou
    - CRITICAL: Erro muito grave, aplicação pode parar
    """
    
    # Criar diretório de logs se não existir
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Determinar nível de log baseado em ambiente
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Formato do log
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo (rotativo - máx 10MB, mantém 10 backups)
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'ejm-santos.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Handler para erros separado
    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'ejm-santos-errors.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Handler para console (apenas em desenvolvimento)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
    
    # Adicionar handlers ao logger da aplicação
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(log_level)
    
    # Log inicial
    app.logger.info('=' * 80)
    app.logger.info(f'🍯 EJM Santos iniciado - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    if app.testing:
        environment_name = "Testes"
    elif app.debug:
        environment_name = "Desenvolvimento"
    else:
        environment_name = "Produção"
    app.logger.info(f'Ambiente: {environment_name}')
    app.logger.info('=' * 80)
    
    return app.logger


def log_request(logger, request, response_status=None):
    """Helper para logar requisições HTTP"""
    logger.info(
        f'{request.method} {request.path} - '
        f'IP: {request.remote_addr} - '
        f'Status: {response_status or "N/A"}'
    )


def log_user_action(logger, user_id, action, details=""):
    """Helper para logar ações de usuários"""
    logger.info(f'User {user_id} - {action} - {details}')


def log_error(logger, error, context=""):
    """Helper para logar erros com contexto"""
    logger.error(f'{context} - Erro: {str(error)}', exc_info=True)
