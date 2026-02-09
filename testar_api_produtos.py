#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testa a API de produtos"""

import requests
import json

base_url = "http://localhost:5000"

print("="*60)
print("🧪 TESTANDO API DE PRODUTOS")
print("="*60)

# Testar API de busca
print("\n1️⃣ GET /api/products/search")
response = requests.get(f"{base_url}/api/products/search")
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    produtos = response.json()
    print(f"   ✅ {len(produtos)} produtos retornados")
    
    if produtos:
        print("\n   Primeiros 3 produtos:")
        for p in produtos[:3]:
            print(f"   • {p['titulo']} - R$ {p['preco']:.2f}")
            print(f"     Imagem: {p['imagem']}")
    else:
        print("   ⚠️  Array vazio retornado")
else:
    print(f"   ❌ Erro: {response.text}")

# Testar  API simples
print("\n2️⃣ GET /api/products")
response = requests.get(f"{base_url}/api/products")
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    produtos = response.json()
    print(f"   ✅ {len(produtos)} produtos retornados")
else:
    print(f"   ❌ Erro")

print("\n" + "="*60)
