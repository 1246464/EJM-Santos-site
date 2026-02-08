#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar e criar usuário admin"""

import sqlite3
from pathlib import Path

db_path = Path('instance') / 'ejm_dev.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar usuários existentes
cursor.execute("SELECT id, nome, email, is_admin FROM user")
usuarios = cursor.fetchall()

print("="*60)
print("👥 USUÁRIOS NO BANCO ejm_dev.db")
print("="*60)

if usuarios:
    print(f"\nTotal de usuários: {len(usuarios)}\n")
    for u in usuarios:
        admin_badge = "🔑 ADMIN" if u[3] else "👤 Cliente"
        print(f"  {admin_badge} | ID: {u[0]} | {u[1]} | {u[2]}")
else:
    print("\n❌ Nenhum usuário encontrado!")

# Verificar se tem admin
cursor.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1")
tem_admin = cursor.fetchone()[0] > 0

print("\n" + "="*60)
if tem_admin:
    print("✅ Já existe pelo menos um usuário admin")
else:
    print("❌ Nenhum usuário admin encontrado!")
    print("\n💡 Execute o script 'criar_admin.py' para criar um admin")

print("="*60)

conn.close()
