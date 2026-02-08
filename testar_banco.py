#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar conexão com o banco de dados"""

import sqlite3
import os
from pathlib import Path

db_path = Path('instance') / 'ejm_dev.db'

print("="*60)
print("🔍 TESTE DE BANCO DE DADOS")
print("="*60)

# Verificar se arquivo existe
if not db_path.exists():
    print(f"\n❌ Banco de dados não encontrado: {db_path}")
    print("Execute: python inicializar_db.py")
else:
    print(f"\n✅ Banco encontrado: {db_path}")
    print(f"   Tamanho: {db_path.stat().st_size} bytes")
    
    # Verificar permissões
    if os.access(db_path, os.R_OK):
        print("   ✅ Permissão de leitura: OK")
    else:
        print("   ❌ Permissão de leitura: NEGADA")
    
    if os.access(db_path, os.W_OK):
        print("   ✅ Permissão de escrita: OK")
    else:
        print("   ❌ Permissão de escrita: NEGADA")
    
    # Tentar conectar
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        
        print(f"\n📊 Tabelas encontradas: {len(tabelas)}")
        for t in tabelas:
            cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
            count = cursor.fetchone()[0]
            print(f"   • {t[0]}: {count} registros")
        
        conn.close()
        print("\n✅ Conexão com banco de dados funcionando!")
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")

print("="*60)
