#!/usr/bin/env python3
# ============================================
# add_delivery_columns.py — Adicionar colunas de entrega
# ============================================

"""
Script para adicionar colunas de taxa de entrega na tabela Order
Executa: python add_delivery_columns.py
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from application import app, db

def add_delivery_columns():
    """Adiciona colunas de entrega à tabela Order"""
    
    with app.app_context():
        try:
            # Usar SQL direto para adicionar colunas (mais seguro que recrear tabela)
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS subtotal FLOAT DEFAULT 0
                """))
                
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS delivery_fee FLOAT DEFAULT 0
                """))
                
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS delivery_distance_km FLOAT
                """))
                
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMP
                """))
                
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS delivery_scheduled_at TIMESTAMP
                """))
                
                conn.execute(db.text("""
                    ALTER TABLE "order" 
                    ADD COLUMN IF NOT EXISTS delivery_notes TEXT
                """))
                
                conn.commit()
            
            print("✅ Colunas de entrega adicionadas com sucesso!")
            
            # Atualizar pedidos existentes: subtotal = total, delivery_fee = 0
            from app.models import Order
            pedidos = Order.query.all()
            
            for pedido in pedidos:
                if pedido.subtotal == 0:
                    pedido.subtotal = pedido.total
                    pedido.delivery_fee = 0
            
            db.session.commit()
            print(f"✅ {len(pedidos)} pedidos atualizados!")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar colunas: {str(e)}")
            db.session.rollback()
            
            # Se SQLite não suportar ALTER COLUMN, recriar tabela
            if "sqlite" in str(db.engine.url).lower():
                print("⚠️ SQLite detectado. As colunas serão adicionadas automaticamente na próxima inicialização.")
                print("Execute: python inicializar_db.py")
            
            sys.exit(1)


if __name__ == '__main__':
    print("🚀 Adicionando colunas de entrega...")
    add_delivery_columns()
