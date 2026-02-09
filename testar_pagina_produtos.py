#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testa página de produtos localmente"""

import requests

base_url = "http://localhost:5000"

print("="*60)
print("🧪 TESTANDO PÁGINA DE PRODUTOS")
print("="*60)

try:
    # Testar página HTML
    print("\n1️⃣ GET /produtos (HTML)")
    response = requests.get(f"{base_url}/produtos")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ✅ Página carregada ({len(response.text)} bytes)")
        
        # Verificar se elementos essenciais estão presentes
        checks = {
            'produtos-grid': 'id="produtos-grid"' in response.text,
            'busca': 'id="busca"' in response.text,
            'carregarProdutos': 'function carregarProdutos' in response.text,
            'renderDesktop': 'function renderDesktop' in response.text,
            'renderMobile': 'function renderMobile' in response.text,
            'addToCart': 'function addToCart' in response.text,
        }
        
        print("\n   Elementos encontrados:")
        for elemento, encontrado in checks.items():
            status = "✅" if encontrado else "❌"
            print(f"   {status} {elemento}")
    else:
        print(f"   ❌ Erro: {response.status_code}")
    
    # Testar API
    print("\n2️⃣ GET /api/products/search")
    response = requests.get(f"{base_url}/api/products/search")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        produtos = response.json()
        print(f"   ✅ {len(produtos)} produtos disponíveis")
    else:
        print(f"   ❌ Erro na API")
    
except requests.exceptions.ConnectionError:
    print(f"\n❌ Servidor não está rodando!")
    print(f"   Execute: python application.py")
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("\n" + "="*60)
