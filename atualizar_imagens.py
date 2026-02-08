#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para atualizar nomes das imagens dos produtos"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
instance_dir = Path(__file__).resolve().parent / 'instance'
app = Flask(__name__)
db_path = instance_dir / 'ejm_dev.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app.models import init_models
User, Product, Order, OrderItem, Review, CartItem, Address, PaymentMethod = init_models(db)

# Mapeamento de produtos para imagens existentes
mapeamento = {
    "Mel Silvestre 500g": "mel_silvestre.webp",
    "Mel de Eucalipto 500g": "Mel_de_Eucalipto.png",
    "Mel de Laranjeira 500g": "mel_laranjeira.png",
    "Mel de Abelha Jataí 250g": "mel.webp",  # Imagem genérica
    "Mel Orgânico 1kg": "1760708557479.jpg",
    "Mel com Própolis 300g": "1760708557485.jpg"
}

with app.app_context():
    print("🖼️  Atualizando imagens dos produtos...")
    
    for titulo, imagem in mapeamento.items():
        produto = Product.query.filter_by(titulo=titulo).first()
        if produto:
            produto.imagem = imagem
            print(f"   ✅ {titulo} -> {imagem}")
    
    db.session.commit()
    print("\n✅ Imagens atualizadas com sucesso!")
    
    # Listar produtos atualizados
    print("\n📋 Produtos com imagens:")
    produtos = Product.query.all()
    for p in produtos:
        print(f"   • {p.titulo} -> {p.imagem}")
