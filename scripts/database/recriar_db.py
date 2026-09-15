"""
Script para recriar o banco de dados com dados iniciais
"""
import os
os.environ['FLASK_ENV'] = 'production'  # Força production

from application import app, db, User, Product
from werkzeug.security import generate_password_hash

admin_email = os.getenv("EJM_ADMIN_EMAIL")
admin_password = os.getenv("EJM_ADMIN_PASSWORD")

if not admin_email or not admin_password or len(admin_password) < 12:
    raise RuntimeError(
        "Defina EJM_ADMIN_EMAIL e uma EJM_ADMIN_PASSWORD com pelo menos 12 caracteres"
    )

with app.app_context():
    # Recriar todas as tabelas
    print("🔄 Recriando banco de dados...")
    db.drop_all()
    db.create_all()
    
    # Criar usuário admin
    print("👤 Criando usuário administrador...")
    admin = User(
        nome="Administrador",
        email=admin_email.strip().lower(),
        senha_hash=generate_password_hash(admin_password),
        is_admin=True
    )
    db.session.add(admin)
    
    # Criar produtos
    print("🍯 Criando produtos...")
    produtos = [
        {
            "titulo": "Mel Silvestre",
            "descricao": "Do sabor das flores do campo, direto da natureza.",
            "preco": 49.9,
            "imagem": "imagens/mel_silvestre.webp"
        },
        {
            "titulo": "Mel de Eucalipto",
            "descricao": "Sabor marcante e aroma forte, ideal para chás.",
            "preco": 39.9,
            "imagem": "imagens/Mel_de_Eucalipto.png"
        },
        {
            "titulo": "Mel de Laranjeira",
            "descricao": "Leve, aromático e com um toque cítrico suave.",
            "preco": 34.9,
            "imagem": "imagens/mel_laranjeira.png"
        },
        {
            "titulo": "Mel de Trilha",
            "descricao": "Mel escuro, encorpado e cheio de energia natural.",
            "preco": 29.9,
            "imagem": "imagens/trilha_mel.jpg"
        }
    ]
    
    for p in produtos:
        produto = Product(**p)
        db.session.add(produto)
    
    db.session.commit()
    
    print("\n✅ Banco de dados recriado com sucesso!")
    print(f"📦 {Product.query.count()} produtos adicionados")
    print(f"👤 {User.query.count()} usuário criado")
    print("\n🔑 Login Admin:")
    print(f"   Email: {admin_email.strip().lower()}")
