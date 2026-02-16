#!/usr/bin/env python3
# ============================================
# migrate_database.py — Migração do Banco de Dados
# ============================================

"""
Script para adicionar colunas de entrega no banco de dados de produção.
Pode ser executado no console do Render ou localmente.

No Render: python migrate_database.py
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from application import app, db

def migrate_database():
    """Adiciona colunas de entrega à tabela Order se não existirem"""
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            
            # Verificar se a tabela order existe
            if not inspector.has_table('order'):
                print("❌ Tabela 'order' não encontrada!")
                print("Execute: python inicializar_db.py")
                return False
            
            # Pegar colunas existentes
            existing_columns = [col['name'] for col in inspector.get_columns('order')]
            print(f"📋 Colunas existentes: {', '.join(existing_columns)}")
            
            # Colunas que precisam ser adicionadas
            new_columns = {
                'subtotal': 'FLOAT DEFAULT 0',
                'delivery_fee': 'FLOAT DEFAULT 0',
                'delivery_distance_km': 'FLOAT',
                'delivery_date': 'TIMESTAMP',
                'delivery_scheduled_at': 'TIMESTAMP',
                'delivery_notes': 'TEXT'
            }
            
            columns_added = []
            
            # Adicionar colunas que não existem
            with db.engine.connect() as conn:
                for column_name, column_type in new_columns.items():
                    if column_name not in existing_columns:
                        try:
                            # PostgreSQL
                            conn.execute(db.text(f"""
                                ALTER TABLE "order" 
                                ADD COLUMN {column_name} {column_type}
                            """))
                            conn.commit()
                            columns_added.append(column_name)
                            print(f"✅ Coluna '{column_name}' adicionada")
                        except Exception as e:
                            print(f"⚠️ Erro ao adicionar coluna '{column_name}': {str(e)}")
                    else:
                        print(f"ℹ️ Coluna '{column_name}' já existe")
            
            if columns_added:
                print(f"\n✅ {len(columns_added)} novas colunas adicionadas com sucesso!")
                
                # Atualizar pedidos existentes
                from app.models import Order
                pedidos = Order.query.all()
                
                updates = 0
                for pedido in pedidos:
                    if not pedido.subtotal or pedido.subtotal == 0:
                        pedido.subtotal = pedido.total
                        pedido.delivery_fee = 0
                        updates += 1
                
                if updates > 0:
                    db.session.commit()
                    print(f"✅ {updates} pedidos atualizados (subtotal = total)")
            else:
                print("\n✅ Banco de dados já está atualizado!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante migração: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


if __name__ == '__main__':
    print("=" * 60)
    print("🔄 Migração do Banco de Dados - EJM Santos")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Migração concluída com sucesso!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Migração falhou. Verifique os erros acima.")
        print("=" * 60)
        sys.exit(1)
