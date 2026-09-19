# ============================================
# security.py — Middleware de Segurança HTTPS e Headers
# ============================================

from flask import request, redirect, url_for, make_response
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware:
    """
    Middleware para forçar HTTPS em produção.
    Detecta proxies reversos (Nginx, Apache, Render, Heroku, etc.)
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar middleware com aplicação Flask"""
        self.enabled = app.config.get('FORCE_HTTPS', False)
        self.proxy_fix = app.config.get('TRUST_PROXY_HEADERS', True)
        
        if self.enabled:
            app.before_request(self.redirect_to_https)
            logger.info("✅ HTTPS Force habilitado (produção)")
        else:
            logger.info("🔓 HTTPS Force desabilitado (desenvolvimento)")
    
    def is_secure(self, request):
        """Verifica se a requisição é HTTPS considerando proxies"""
        # Verificar header X-Forwarded-Proto (comum em proxies reversos)
        if self.proxy_fix:
            forwarded_proto = request.headers.get('X-Forwarded-Proto', '')
            if forwarded_proto == 'https':
                return True
            
            # Verificar X-Forwarded-Ssl (Nginx)
            if request.headers.get('X-Forwarded-Ssl') == 'on':
                return True
            
            # Verificar Front-End-Https (IIS)
            if request.headers.get('Front-End-Https') == 'on':
                return True
        
        # Verificar se é HTTPS direto
        return request.is_secure
    
    def redirect_to_https(self):
        """Redireciona requisições HTTP para HTTPS"""
        if not self.enabled:
            return None
        
        # Ignorar requisições OPTIONS (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Ignorar health checks e webhooks
        exempt_paths = ['/health', '/webhook/', '/api/webhook/']
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
        
        # Se já for HTTPS, não fazer nada
        if self.is_secure(request):
            return None
        
        # Redirecionar para HTTPS
        url = request.url.replace('http://', 'https://', 1)
        logger.warning(f"⚠️ Redirecionando HTTP -> HTTPS: {request.url} -> {url}")
        return redirect(url, code=301)


def get_security_headers(app_config, script_nonce=None):
    """
    Retorna headers de segurança otimizados baseados no ambiente.
    
    Returns:
        dict: Dicionário com headers de segurança
    """
    is_production = app_config.get('ENV') == 'production'
    
    headers = {
        # Prevenir MIME sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Proteção contra clickjacking
        'X-Frame-Options': 'SAMEORIGIN',
        
        # Proteção XSS (legado, mas ainda útil)
        'X-XSS-Protection': '1; mode=block',
        
        # Controle de referrer
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Permissões de APIs do browser
        'Permissions-Policy': (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(self), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        ),
    }
    
    # HSTS apenas em produção HTTPS
    if is_production:
        headers['Strict-Transport-Security'] = (
            'max-age=31536000; '  # 1 ano
            'includeSubDomains; '
            'preload'
        )
    
    # Content Security Policy
    csp = get_content_security_policy(app_config, script_nonce)
    headers['Content-Security-Policy'] = csp
    
    return headers


def get_content_security_policy(app_config, script_nonce=None):
    """
    Gera Content Security Policy otimizado para a aplicação.
    
    Returns:
        str: String com diretivas CSP
    """
    is_development = app_config.get('ENV') == 'development'
    
    # Base CSP
    csp_directives = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            'https://js.stripe.com',
            'https://cdn.jsdelivr.net',
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # Necessário para estilos inline
        ],
        'img-src': [
            "'self'",
            'data:',
            'https:',
        ],
        'font-src': [
            "'self'",
            'data:',
        ],
        'connect-src': [
            "'self'",
            'https://api.stripe.com',
        ],
        'frame-src': [
            'https://js.stripe.com',
            'https://hooks.stripe.com',
        ],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
        'frame-ancestors': ["'self'"],
    }

    if script_nonce:
        csp_directives['script-src'].append(f"'nonce-{script_nonce}'")
    
    # Em desenvolvimento, permitir inline scripts e eval
    if is_development:
        csp_directives['script-src'].extend(["'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'"])
        logger.info("🔓 CSP relaxado para desenvolvimento (unsafe-inline permitido)")
    
    # Converter para string
    csp_parts = []
    for directive, sources in csp_directives.items():
        sources_str = ' '.join(sources)
        csp_parts.append(f"{directive} {sources_str}")
    
    return '; '.join(csp_parts) + ';'


def apply_security_headers(response, app_config, script_nonce=None):
    """
    Aplica headers de segurança à resposta.
    
    Args:
        response: Objeto Response do Flask
        app_config: Configuração da aplicação
    
    Returns:
        Response com headers de segurança
    """
    headers = get_security_headers(app_config, script_nonce)
    
    for header, value in headers.items():
        response.headers[header] = value
    
    # Cache control em desenvolvimento (facilita debug) ou rotas sensíveis
    is_development = app_config.get('ENV') == 'development'
    is_sensitive_route = request.endpoint in ['auth.login', 'auth.register', 'admin.login']
    
    if is_development or is_sensitive_route:
        response.headers['Cache-Control'] = (
            'no-store, '
            'no-cache, '
            'must-revalidate, '
            'max-age=0'
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response


def csrf_exempt_routes():
    """
    Lista de rotas que devem ser isentas de CSRF.
    Geralmente webhooks de serviços externos.
    
    Returns:
        list: Lista de prefixos de rotas isentas
    """
    return [
        '/webhook/stripe',
        '/api/webhook/',
        '/health',
    ]


def require_https(f):
    """
    Decorator para forçar HTTPS em rotas específicas.
    
    Usage:
        @app.route('/checkout')
        @require_https
        def checkout():
            return render_template('checkout.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        # Apenas em produção
        if current_app.config.get('ENV') != 'production':
            return f(*args, **kwargs)
        
        # Verificar HTTPS (considerando proxies)
        forwarded_proto = request.headers.get('X-Forwarded-Proto', '')
        is_secure = request.is_secure or forwarded_proto == 'https'
        
        if not is_secure:
            url = request.url.replace('http://', 'https://', 1)
            logger.warning(f"⚠️ Rota protegida acessada via HTTP: {request.endpoint}")
            return redirect(url, code=301)
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_client_ip():
    """
    Obtém o IP real do cliente considerando proxies reversos.
    
    Returns:
        str: Endereço IP do cliente
    """
    # Verificar headers de proxy (em ordem de prioridade)
    if request.headers.get('CF-Connecting-IP'):
        # Cloudflare
        return request.headers.get('CF-Connecting-IP')
    
    if request.headers.get('X-Real-IP'):
        # Nginx
        return request.headers.get('X-Real-IP')
    
    if request.headers.get('X-Forwarded-For'):
        # Proxy padrão - pegar o primeiro IP
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # Fallback para IP remoto direto
    return request.remote_addr


def validate_csrf_token_for_ajax():
    """
    Valida token CSRF para requisições AJAX.
    Procura o token em headers customizados.
    
    Returns:
        bool: True se token válido ou não necessário
    """
    from flask import current_app
    
    # Se CSRF está desabilitado, permitir
    if not current_app.config.get('WTF_CSRF_ENABLED', True):
        return True
    
    # Requisições GET/HEAD/OPTIONS não precisam de CSRF
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        return True
    
    # Verificar se a rota está isenta
    exempt_routes = csrf_exempt_routes()
    if any(request.path.startswith(route) for route in exempt_routes):
        return True
    
    # Para requisições AJAX, procurar token nos headers
    if request.is_json:
        csrf_token = (
            request.headers.get('X-CSRFToken') or
            request.headers.get('X-CSRF-Token')
        )
        if csrf_token:
            # Flask-WTF vai validar automaticamente
            return True
    
    return True
