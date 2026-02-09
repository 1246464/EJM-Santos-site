#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica produtos no banco"""

import sqlite3
import os

db_path = os.path.join('instance', 'ejm_dev.db')

print("="*60)
print("📦 VERIFICANDO PRODUTOS")
print("="*60)

if not os.path.exists(db_path):
    print(f"\n❌ Banco de dados não encontrado: {db_path}")
    print("Execute: python inicializar_db.py")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a tabela product existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if not cursor.fetchone():
        print("❌ Tabela 'product' não existe no banco de dados!")
    else:
        # Contar produtos
        cursor.execute("SELECT COUNT(*) FROM product")
        total = cursor.fetchone()[0]
        print(f"\n✅ Total de produtos no banco: {total}\n")
        
        # Listar produtos
        cursor.execute("SELECT id, titulo, preco, estoque, imagem FROM product")
        produtos = cursor.fetchall()
        
        if produtos:
            for p in produtos:
                pid, titulo, preco, estoque, imagem = p
                print(f"{pid}. {titulo}")
                print(f"   Preço: R$ {preco:.2f}")
                print(f"   Estoque: {estoque}")
                print(f"   Imagem: {imagem}")
                print()
        else:
            print("\n❌ Nenhum produto cadastrado!")
            print("Execute: python inicializar_db.py")
    
    conn.close()

print("="*60)
