#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar produtos em cada banco de dados"""

import sqlite3
from pathlib import Path

instance_dir = Path(__file__).resolve().parent / 'instance'

# Verificar ambos os bancos
bancos = ['ejm.db', 'ejm_dev.db']

for banco in bancos:
    db_path = instance_dir / banco
    print(f"\n{'='*60}")
    print(f"📊 BANCO: {banco}")
    print('='*60)
    
    if not db_path.exists():
        print(f"❌ Arquivo não existe")
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar produtos
        cursor.execute("SELECT COUNT(*) FROM product")
        total = cursor.fetchone()[0]
        print(f"Total de produtos: {total}")
        
        # Listar produtos
        cursor.execute("SELECT id, titulo, preco, estoque FROM product ORDER BY id")
        produtos = cursor.fetchall()
        
        if produtos:
            print("\nProdutos cadastrados:")
            for p in produtos:
                print(f"  {p[0]}. {p[1]} - R$ {p[2]:.2f} - Estoque: {p[3]}")
        else:
            print("  (Nenhum produto)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao ler banco: {e}")

print(f"\n{'='*60}")
print("💡 SOLUÇÃO:")
print("='*60")
print("O servidor está configurado para usar: ejm_dev.db")
print("Se você adicionou produtos no admin, eles foram para: ejm.db")
print("\nOpções:")
print("1. Use apenas ejm_dev.db (remova ejm.db)")
print("2. Adicione produtos novamente pelo admin com o servidor rodando")
print('='*60)
