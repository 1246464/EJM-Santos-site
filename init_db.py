# init_db.py
from app import app, db, Product

# lista de produtos que você quer ter no site
produtos = [
    {
        "titulo": "Mel Silvestre",
        "descricao": "Do sabor das flores do campo, direto da natureza.",
        "preco": 49.9,
        "imagem": "mel_silvestre.webp", 
        "mercado_pago_link": "https://mpago.la/1fvNNDL"
    },
    {
        "titulo": "Mel de Eucalipto",
        "descricao": "Sabor marcante e aroma forte, ideal para chás.",
        "preco": 39.9,
        "imagem": "Mel_de_Eucalipto.png",
        "mercado_pago_link": "https://mpago.la/2ZbehYw"
    },
    {
        "titulo": "Mel de Laranjeira",
        "descricao": "Leve, aromático e com um toque cítrico suave.",
        "preco": 34.9,
        "imagem": "mel_laranjeira.png",
        "mercado_pago_link": "https://mpago.la/1xoRXpy"
    },
    {
        "titulo": "Mel de Trilha",
        "descricao": "Mel escuro, encorpado e cheio de energia natural.",
        "preco": 29.9,
        "imagem": "trilha_mel.jpg",
        "mercado_pago_link": "https://mpago.la/1xoRXpy"
    }
]

with app.app_context():
    for p in produtos:
        # busca pelo título (ou outro campo único)
        produto = Product.query.filter_by(titulo=p["titulo"]).first()
        if produto:
            # atualiza os campos existentes
            produto.descricao = p["descricao"]
            produto.preco = p["preco"]
            produto.imagem = p["imagem"]
            produto.mercado_pago_link = p["mercado_pago_link"]
        else:
            # cria novo produto se não existir
            novo_produto = Product(**p)
            db.session.add(novo_produto)
    db.session.commit()

print("Produtos atualizados com sucesso!")
