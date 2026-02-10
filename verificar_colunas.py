"""Verificar colunas da tabela product no SQLite"""
import sqlite3
import os

db_path = os.path.join('instance', 'ejm_dev.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver estrutura da tabela
cursor.execute("PRAGMA table_info(product)")
colunas = cursor.fetchall()

print("="*60)
print("📋 ESTRUTURA DA TABELA PRODUCT")
print("="*60)
for col in colunas:
    print(f"{col[1]} ({col[2]})")

conn.close()
