#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para inicializar o banco de dados e adicionar produtos de exemplo
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuração básica
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Criar diretório instance se não existir
instance_dir = Path(__file__).resolve().parent / 'instance'
instance_dir.mkdir(exist_ok=True)

# Criar app Flask simples
app = Flask(__name__)
db_path = instance_dir / 'ejm_dev.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Importar e inicializar modelos
from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

# Produtos de exemplo
produtos_exemplo = [
    {
        "titulo": "Mel Silvestre 500g",
        "descricao": "Mel puro de flores silvestres, colhido artesanalmente. Sabor suave e aromático, ideal para o dia a dia.",
        "preco": 45.90,
        "imagem": "mel_silvestre.jpg",
        "estoque": 50
    },
    {
        "titulo": "Mel de Eucalipto 500g",
        "descricao": "Mel de sabor marcante e aroma característico do eucalipto. Uma opção intensa para bebidas e receitas.",
        "preco": 42.90,
        "imagem": "mel_eucalipto.jpg",
        "estoque": 30
    },
    {
        "titulo": "Mel de Laranjeira 500g",
        "descricao": "Mel leve e aromático com toque cítrico suave. Perfeito para adoçar bebidas e receitas.",
        "preco": 48.90,
        "imagem": "mel_laranjeira.jpg",
        "estoque": 40
    },
    {
        "titulo": "Mel de Abelha Jataí 250g",
        "descricao": "Mel de abelha sem ferrão, raro e especial, com sabor levemente ácido e características próprias.",
        "preco": 89.90,
        "imagem": "mel_jatai.jpg",
        "estoque": 15
    },
    {
        "titulo": "Mel Orgânico 1kg",
        "descricao": "Mel orgânico certificado, produzido sem agrotóxicos. Qualidade premium para sua família.",
        "preco": 79.90,
        "imagem": "mel_organico.jpg",
        "estoque": 25
    },
    {
        "titulo": "Mel com Própolis 300g",
        "descricao": "Combinação de mel com própolis, de sabor intenso. Confira os ingredientes e o modo de uso no rótulo.",
        "preco": 52.90,
        "imagem": "mel_propolis.jpg",
        "estoque": 35
    }
]

def init_database():
    """Inicializa o banco de dados e adiciona produtos"""
    
    with app.app_context():
        print("🔧 Criando tabelas do banco de dados...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar se já existem produtos
        produtos_existentes = Product.query.count()
        
        if produtos_existentes > 0:
            print(f"\n⚠️  Já existem {produtos_existentes} produtos no banco.")
            resposta = input("Deseja adicionar mais produtos? (s/n): ")
            if resposta.lower() != 's':
                print("❌ Operação cancelada.")
                return
        
        print(f"\n📦 Adicionando {len(produtos_exemplo)} produtos...")
        
        for prod_data in produtos_exemplo:
            # Verificar se produto já existe
            produto_existe = Product.query.filter_by(titulo=prod_data['titulo']).first()
            
            if produto_existe:
                print(f"   ⏭️  Produto '{prod_data['titulo']}' já existe - pulando")
                continue
            
            # Criar novo produto
            produto = Product(
                titulo=prod_data['titulo'],
                descricao=prod_data['descricao'],
                preco=prod_data['preco'],
                imagem=prod_data['imagem'],
                estoque=prod_data['estoque']
            )
            
            db.session.add(produto)
            print(f"   ✅ Adicionado: {prod_data['titulo']}")
        
        # Salvar no banco
        try:
            db.session.commit()
            print("\n✅ Todos os produtos foram salvos com sucesso!")
            
            # Mostrar estatísticas
            total_produtos = Product.query.count()
            print(f"\n📊 Total de produtos no banco: {total_produtos}")
            
            # Listar produtos
            print("\n📋 Produtos cadastrados:")
            produtos = Product.query.all()
            for p in produtos:
                print(f"   • {p.titulo} - R$ {p.preco:.2f} - Estoque: {p.estoque}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao salvar produtos: {e}")
            return

if __name__ == "__main__":
    print("="*60)
    print("🍯 EJM SANTOS - Inicialização do Banco de Dados")
    print("="*60)
    
    init_database()
    
    print("\n" + "="*60)
    print("🎉 Inicialização concluída!")
    print("="*60)
    print("\n💡 Próximos passos:")
    print("   1. Inicie o servidor: python application.py")
    print("   2. Acesse: http://localhost:5000")
    print("   3. Veja os produtos na página inicial e em /produtos")
    print("\n")
