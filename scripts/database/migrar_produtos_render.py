"""
Script para migrar produtos do SQLite local para PostgreSQL do Render
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from datetime import datetime

# Bases separados para evitar conflito de tabelas com mesmo nome
BaseLocal = declarative_base()
BaseRender = declarative_base()

# Modelo para o SQLite local (colunas antigas)
class ProductLocal(BaseLocal):
    __tablename__ = 'product'
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(120), nullable=False)
    descricao = Column(Text)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    imagem = Column(String(256))

# Modelo para o PostgreSQL Render (usar mesma estrutura do local)
class ProductRender(BaseRender):
    __tablename__ = 'product'
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(120), nullable=False)
    descricao = Column(Text)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    imagem = Column(String(256))

def migrar_produtos():
    """Migra produtos do SQLite local para PostgreSQL do Render"""
    
    # URL do PostgreSQL no Render
    render_db_url = "postgresql://ejm_santos_user:aFUqgdVAxIE7jlEMmCLJZuB13v3dgulD@dpg-d64isi6r433s73eaj0bg-a.oregon-postgres.render.com/ejm_santos"
    
    # URL do SQLite local
    local_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'ejm_dev.db')
    local_db_url = f"sqlite:///{local_db_path}"
    
    print("="*60)
    print("🔄 MIGRAÇÃO DE PRODUTOS - SQLite → PostgreSQL")
    print("="*60)
    
    try:
        # Conectar no SQLite local
        print("\n📂 Conectando no SQLite local...")
        local_engine = create_engine(local_db_url)
        LocalSession = sessionmaker(bind=local_engine)
        local_session = LocalSession()
        
        # Ler produtos do SQLite
        produtos_locais = local_session.query(ProductLocal).all()
        print(f"✅ {len(produtos_locais)} produtos encontrados no SQLite")
        
        if not produtos_locais:
            print("\n⚠️ Nenhum produto encontrado no banco local!")
            return
        
        # Conectar no PostgreSQL do Render
        print("\n🐘 Conectando no PostgreSQL do Render...")
        render_engine = create_engine(render_db_url)
        RenderSession = sessionmaker(bind=render_engine)
        render_session = RenderSession()
        
        # Verificar quantos produtos já existem no Render
        produtos_render = render_session.query(ProductRender).all()
        print(f"ℹ️ {len(produtos_render)} produtos já existem no Render")
        
        # Copiar produtos
        print("\n📦 Copiando produtos...\n")
        produtos_adicionados = 0
        produtos_pulados = 0
        
        for produto_local in produtos_locais:
            # Verificar se produto já existe (por titulo)
            produto_existente = render_session.query(ProductRender).filter_by(
                titulo=produto_local.titulo
            ).first()
            
            if produto_existente:
                print(f"⏭️ {produto_local.titulo} - já existe, pulando...")
                produtos_pulados += 1
                continue
            
            # Criar novo produto no Render
            novo_produto = ProductRender(
                titulo=produto_local.titulo,
                descricao=produto_local.descricao,
                preco=produto_local.preco,
                estoque=produto_local.estoque,
                imagem=produto_local.imagem
            )
            
            render_session.add(novo_produto)
            print(f"✅ {produto_local.titulo} - adicionado!")
            produtos_adicionados += 1
        
        # Salvar no banco
        render_session.commit()
        
        # Resumo
        print("\n" + "="*60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"📊 Produtos adicionados: {produtos_adicionados}")
        print(f"⏭️ Produtos já existentes: {produtos_pulados}")
        print(f"📦 Total no Render agora: {len(render_session.query(ProductRender).all())}")
        print("="*60)
        
        # Fechar conexões
        local_session.close()
        render_session.close()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_produtos()
