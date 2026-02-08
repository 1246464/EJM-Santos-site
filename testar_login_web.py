#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para simular login web completo"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simular request web
import requests

print("="*60)
print("🌐 TESTE DE LOGIN WEB")
print("="*60)

base_url = "http://localhost:5000"

try:
    # 1. Acesso inicial para pegar CSRF token
    print(f"\n1️⃣ Acessando página de login...")
    session = requests.Session()
    response = session.get(f"{base_url}/login")
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Erro ao acessar página")
        sys.exit(1)
    
    # Extrair CSRF token do HTML
    import re
    csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"   ✅ CSRF token obtido: {csrf_token[:20]}...")
    else:
        print(f"   ⚠️  CSRF token não encontrado")
        csrf_token = None
    
    # 2. Fazer login
    print(f"\n2️⃣ Enviando credenciais de login...")
    login_data = {
        "email": "admin@ejmsantos.com",
        "senha": "admin123",
        "csrf_token": csrf_token
    }
    
    response = session.post(f"{base_url}/login", data=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    if response.status_code == 200:
        if "erro" in response.text.lower() or "inválid" in response.text.lower():
            # Tentar extrair mensagem de erro
            error_match = re.search(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>([^<]+)</div>', response.text, re.IGNORECASE)
            if error_match:
                print(f"   ❌ Erro: {error_match.group(1).strip()}")
            else:
                print(f"   ❌ Login falhou (resposta contém erro)")
        else:
            print(f"   ✅ Login bem-sucedido!")
    else:
        print(f"   ⚠️  Redirecionamento: {response.history}")
    
    # 3. Verificar sessão
    print(f"\n3️⃣ Verificando sessão...")
    cookies = session.cookies.get_dict()
    if cookies:
        print(f"   Cookies: {list(cookies.keys())}")
    else:
        print(f"   ⚠️  Nenhum cookie de sessão")
    
    # 4. Tentar acessar perfil
    print(f"\n4️⃣ Testando acesso ao perfil...")
    response = session.get(f"{base_url}/perfil")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Perfil acessível")
    else:
        print(f"   ❌ Perfil não acessível")

except requests.exceptions.ConnectionError:
    print(f"\n❌ Servidor não está rodando em {base_url}")
    print(f"   Execute: python application.py")
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
