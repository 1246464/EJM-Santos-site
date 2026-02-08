#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================
migrate_addresses_payments.py — Migração de Banco
============================================

Adiciona as tabelas 'address' e 'payment_method' ao banco de dados existente.

Uso:
    python scripts/database/migrate_addresses_payments.py
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app_new import app, db
from app.models import Address, PaymentMethod

def migrate_database():
    """Adiciona as tabelas de endereços e métodos de pagamento"""
    print("🔄 Iniciando migração do banco de dados...\n")
    
    with app.app_context():
        try:
            # Verificar se as tabelas já existem
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📊 Tabelas existentes: {', '.join(existing_tables)}\n")
            
            # Criar apenas as novas tabelas
            tables_to_create = []
            
            if 'address' not in existing_tables:
                tables_to_create.append('address')
                print("✅ Tabela 'address' será criada")
            else:
                print("⚠️  Tabela 'address' já existe")
            
            if 'payment_method' not in existing_tables:
                tables_to_create.append('payment_method')
                print("✅ Tabela 'payment_method' será criada")
            else:
                print("⚠️  Tabela 'payment_method' já existe")
            
            if not tables_to_create:
                print("\n✅ Todas as tabelas já existem! Nada a fazer.")
                return
            
            print(f"\n🔨 Criando tabelas: {', '.join(tables_to_create)}...")
            
            # Criar as tabelas
            if 'address' in tables_to_create:
                Address.__table__.create(db.engine)
                print("✅ Tabela 'address' criada com sucesso!")
            
            if 'payment_method' in tables_to_create:
                PaymentMethod.__table__.create(db.engine)
                print("✅ Tabela 'payment_method' criada com sucesso!")
            
            print("\n" + "="*60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            print("\n📋 Estrutura das novas tabelas:\n")
            
            if 'address' in tables_to_create:
                print("🏠 TABELA: address")
                print("   Campos:")
                print("   - id (PK)")
                print("   - user_id (FK → user)")
                print("   - apelido (ex: Casa, Trabalho)")
                print("   - rua, numero, complemento")
                print("   - bairro, cidade, estado, cep")
                print("   - telefone")
                print("   - is_default (boolean)")
                print("   - created_at, updated_at\n")
            
            if 'payment_method' in tables_to_create:
                print("💳 TABELA: payment_method")
                print("   Campos:")
                print("   - id (PK)")
                print("   - user_id (FK → user)")
                print("   - apelido (ex: Cartão principal)")
                print("   - stripe_payment_method_id (token Stripe)")
                print("   - card_brand (visa, mastercard, etc)")
                print("   - card_last4 (últimos 4 dígitos)")
                print("   - card_exp_month, card_exp_year")
                print("   - is_default (boolean)")
                print("   - created_at, updated_at\n")
            
            print("🎉 Agora os usuários podem salvar:")
            print("   ✅ Múltiplos endereços de entrega")
            print("   ✅ Múltiplos cartões de crédito")
            print("   ✅ Definir endereço/cartão padrão")
            print("\n💡 Próximos passos:")
            print("   1. Reiniciar a aplicação")
            print("   2. Acessar /perfil para gerenciar endereços/cartões")
            print("   3. No checkout, poderá selecionar dados salvos\n")
        
        except Exception as e:
            print(f"\n❌ ERRO na migração: {str(e)}")
            print(f"   Detalhes: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    print("="*60)
    print("🍯 EJM SANTOS - Migração de Banco de Dados")
    print("="*60)
    print("\nEsta migração adiciona suporte para:")
    print("  • Endereços salvos (múltiplos por usuário)")
    print("  • Cartões salvos (Stripe Payment Methods)")
    print("\n⚠️  IMPORTANTE:")
    print("  • Faça backup antes de executar!")
    print("  • Execute: python scripts/backup/backup_manager.py create\n")
    
    resposta = input("Deseja continuar com a migração? (s/N): ").strip().lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        migrate_database()
    else:
        print("\n❌ Migração cancelada pelo usuário.")
        sys.exit(0)
