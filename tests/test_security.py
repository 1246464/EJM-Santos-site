#!/usr/bin/env python3
# ============================================
# test_security.py — Testes de Segurança HTTPS + CSRF
# ============================================

import os
import sys
from pathlib import Path

# Definir variável EJM_SECRET antes de importar módulos
# (necessário para carregar config.py)
if 'EJM_SECRET' not in os.environ:
    os.environ['EJM_SECRET'] = 'test_secret_key_for_security_testing_only_32chars_minimum'

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

def test_imports():
    """Verifica se todos os módulos de segurança podem ser importados"""
    print("🧪 Testando imports...")
    
    try:
        from app.utils.security import (
            HTTPSRedirectMiddleware,
            get_security_headers,
            get_content_security_policy,
            apply_security_headers,
            csrf_exempt_routes,
            require_https,
            get_client_ip,
            validate_csrf_token_for_ajax
        )
        print("  ✅ Todos os imports OK")
        return True
    except ImportError as e:
        print(f"  ❌ Erro de import: {e}")
        return False


def test_config_https():
    """Verifica configurações HTTPS"""
    print("\n🧪 Testando configurações HTTPS...")
    
    from config import DevelopmentConfig, ProductionConfig
    
    # Development
    assert DevelopmentConfig.FORCE_HTTPS == False, "Dev deve ter HTTPS desabilitado"
    assert DevelopmentConfig.PREFERRED_URL_SCHEME == 'http', "Dev deve usar HTTP"
    assert DevelopmentConfig.SESSION_COOKIE_SECURE == False, "Dev deve permitir HTTP cookies"
    print("  ✅ Configuração Development OK")
    
    # Production
    assert ProductionConfig.FORCE_HTTPS == True, "Prod deve ter HTTPS habilitado"
    assert ProductionConfig.PREFERRED_URL_SCHEME == 'https', "Prod deve usar HTTPS"
    assert ProductionConfig.SESSION_COOKIE_SECURE == True, "Prod deve ter cookies seguros"
    print("  ✅ Configuração Production OK")
    
    return True


def test_config_csrf():
    """Verifica configurações CSRF"""
    print("\n🧪 Testando configurações CSRF...")
    
    from config import Config, DevelopmentConfig, ProductionConfig
    
    # Base config
    assert Config.WTF_CSRF_ENABLED == True, "CSRF deve estar habilitado por padrão"
    assert 'X-CSRFToken' in Config.WTF_CSRF_HEADERS, "Deve aceitar X-CSRFToken header"
    assert Config.WTF_CSRF_TIME_LIMIT == None, "Token não deve expirar"
    print("  ✅ Configuração base CSRF OK")
    
    # Development
    assert DevelopmentConfig.WTF_CSRF_ENABLED == True, "Dev deve manter CSRF habilitado"
    print("  ✅ Configuração Development CSRF OK")
    
    # Production
    assert ProductionConfig.WTF_CSRF_SSL_STRICT == True, "Prod deve ter CSRF SSL strict"
    assert ProductionConfig.WTF_CSRF_COOKIE_SECURE == True, "Prod deve ter CSRF cookie seguro"
    print("  ✅ Configuração Production CSRF OK")
    
    return True


def test_security_headers():
    """Verifica geração de headers de segurança"""
    print("\n🧪 Testando headers de segurança...")
    
    from app.utils.security import get_security_headers
    from config import ProductionConfig, DevelopmentConfig
    
    # Testar produção
    prod_config = {'ENV': 'production'}
    headers = get_security_headers(prod_config)
    
    # Verificar headers essenciais
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy',
        'Permissions-Policy',
        'Content-Security-Policy',
        'Strict-Transport-Security',  # Apenas em production
    ]
    
    for header in required_headers:
        assert header in headers, f"Header {header} não encontrado"
        print(f"  ✅ {header}: {headers[header][:50]}...")
    
    # Testar desenvolvimento (sem HSTS)
    dev_config = {'ENV': 'development'}
    dev_headers = get_security_headers(dev_config)
    assert 'Strict-Transport-Security' not in dev_headers, "HSTS não deve estar em development"
    print("  ✅ HSTS corretamente ausente em development")
    
    return True


def test_csp():
    """Verifica Content Security Policy"""
    print("\n🧪 Testando CSP...")
    
    from app.utils.security import get_content_security_policy
    from config import ProductionConfig
    
    csp = get_content_security_policy(ProductionConfig.__dict__)
    
    # Verificar diretivas essenciais
    assert "default-src 'self'" in csp, "CSP deve ter default-src 'self'"
    assert "https://js.stripe.com" in csp, "CSP deve permitir Stripe"
    assert "object-src 'none'" in csp, "CSP deve bloquear objects"
    
    print(f"  ✅ CSP gerado ({len(csp)} chars)")
    print(f"  📋 {csp[:100]}...")
    
    return True


def test_middleware():
    """Verifica middleware HTTPS"""
    print("\n🧪 Testando middleware HTTPS...")
    
    from flask import Flask
    from app.utils.security import HTTPSRedirectMiddleware
    from config import ProductionConfig
    
    app = Flask(__name__)
    app.config.from_object(ProductionConfig)
    
    # Inicializar middleware
    middleware = HTTPSRedirectMiddleware(app)
    
    assert middleware.enabled == True, "Middleware deve estar habilitado"
    assert middleware.proxy_fix == True, "Proxy fix deve estar habilitado"
    
    print("  ✅ Middleware inicializado corretamente")
    
    return True


def test_csrf_exempt_routes():
    """Verifica rotas isentas de CSRF"""
    print("\n🧪 Testando rotas isentas de CSRF...")
    
    from app.utils.security import csrf_exempt_routes
    
    exempt = csrf_exempt_routes()
    
    # Verificar rotas essenciais
    assert '/webhook/stripe' in exempt, "Webhook Stripe deve ser isento"
    assert '/health' in exempt, "Health check deve ser isento"
    
    print(f"  ✅ {len(exempt)} rotas isentas encontradas")
    for route in exempt:
        print(f"    - {route}")
    
    return True


def test_app_integration():
    """Verifica integração com application.py"""
    print("\n🧪 Testando integração com aplicação...")
    
    # Configurar ambiente de teste
    os.environ['FLASK_ENV'] = 'development'  # Usar development para não validar Stripe
    
    try:
        from config import get_config
        
        # Testar desenvolvimento
        dev_config = get_config('development')
        assert dev_config.FORCE_HTTPS == False, "Dev deve ter HTTPS desabilitado"
        assert dev_config.WTF_CSRF_ENABLED == True, "Dev deve manter CSRF habilitado"
        print("  ✅ Configuração de desenvolvimento OK")
        
        # Testar que production validação existe (sem executar)
        from config import ProductionConfig
        assert hasattr(ProductionConfig, 'validate'), "Production deve ter método validate"
        print("  ✅ Método de validação existe em ProductionConfig")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao carregar app: {e}")
        return False


def test_csrf_meta_tag():
    """Verifica se meta tag CSRF está no template base"""
    print("\n🧪 Testando meta tag CSRF no template...")
    
    template_path = ROOT_DIR / 'templates' / 'base.html'
    
    if not template_path.exists():
        print("  ⚠️ Template base.html não encontrado")
        return False
    
    content = template_path.read_text(encoding='utf-8')
    
    if 'name="csrf-token"' in content and '{{ csrf_token() }}' in content:
        print("  ✅ Meta tag CSRF encontrada no base.html")
        return True
    else:
        print("  ❌ Meta tag CSRF não encontrada no base.html")
        return False


def test_javascript_csrf():
    """Verifica se JavaScript tem funções CSRF"""
    print("\n🧪 Testando helpers CSRF no JavaScript...")
    
    js_path = ROOT_DIR / 'static' / 'js' / 'main.js'
    
    if not js_path.exists():
        print("  ⚠️ main.js não encontrado")
        return False
    
    content = js_path.read_text(encoding='utf-8')
    
    required_functions = ['getCSRFToken', 'csrfFetch']
    missing = []
    
    for func in required_functions:
        if func in content:
            print(f"  ✅ Função {func}() encontrada")
        else:
            print(f"  ❌ Função {func}() não encontrada")
            missing.append(func)
    
    return len(missing) == 0


def run_all_tests():
    """Executa todos os testes"""
    print("="*60)
    print("🔐 TESTES DE SEGURANÇA - EJM SANTOS")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Config HTTPS", test_config_https),
        ("Config CSRF", test_config_csrf),
        ("Security Headers", test_security_headers),
        ("Content Security Policy", test_csp),
        ("Middleware HTTPS", test_middleware),
        ("Rotas Isentas CSRF", test_csrf_exempt_routes),
        ("Integração App", test_app_integration),
        ("Meta Tag CSRF", test_csrf_meta_tag),
        ("JavaScript CSRF", test_javascript_csrf),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ ERRO: {e}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("="*60)
    print(f"Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes de segurança passaram!")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique as configurações.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
