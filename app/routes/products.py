# ============================================
# products.py — Blueprint de Produtos e Carrinho
# ============================================

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for

products_bp = Blueprint('products', __name__)

# Estas variáveis serão injetadas pelo app.py
db = None
Product = None
Review = None
User = None
CartItem = None
Order = None
OrderItem = None
logger = None

def init_products(database, models_dict, log):
    """Inicializa o blueprint com dependências"""
    global db, Product, Review, User, CartItem, Order, OrderItem, logger
    db = database
    Product = models_dict['Product']
    Review = models_dict['Review']
    User = models_dict['User']
    CartItem = models_dict['CartItem']
    Order = models_dict['Order']
    OrderItem = models_dict['OrderItem']
    logger = log


# ============================================
# PÁGINAS DE PRODUTOS (HTML)
# ============================================

@products_bp.route("/")
def index():
    """Página inicial"""
    return render_template("index.html")


@products_bp.route("/produtos")
def produtos_page():
    """Página de listagem de produtos"""
    return render_template("produtos.html")


@products_bp.route("/produto/<int:product_id>")
def produto_page(product_id):
    """Página de detalhes de um produto"""
    return render_template("produto.html", product_id=product_id)


@products_bp.route("/sobre")
def sobre_page():
    """Página sobre"""
    return render_template("sobre.html")


@products_bp.route("/perfil")
def perfil_page():
    """Página de perfil do usuário"""
    if not session.get("user_id"):
        return redirect("/login")
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect("/login")
    
    # Buscar todos os pedidos do usuário
    pedidos = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    logger.info(f"Perfil acessado - User ID: {user_id}")
    return render_template("perfil_novo.html", pedidos=pedidos, user=user)


# ============================================
# API DE PRODUTOS (JSON)
# ============================================

@products_bp.route("/api/products")
def api_products():
    """API que retorna todos os produtos com suas avaliações"""
    try:
        prods = Product.query.all()
        data = []
        
        for p in prods:
            # Calcular média de avaliações
            avg = db.session.query(db.func.avg(Review.nota)).filter(Review.product_id == p.id).scalar() or 0
            count = Review.query.filter_by(product_id=p.id).count()
            
            # Limpar caminho da imagem
            imagem = p.imagem.replace('imagens/', '') if p.imagem and p.imagem.startswith('imagens/') else (p.imagem or '')
            
            data.append({
                "id": p.id,
                "titulo": p.titulo,
                "descricao": p.descricao,
                "preco": p.preco,
                "imagem": imagem,
                "estoque": p.estoque,
                "media": round(float(avg), 2),
                "n_reviews": count
            })
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao carregar produtos"}), 500


@products_bp.route("/api/product/<int:product_id>")
def api_product_detail(product_id):
    """API que retorna detalhes de um produto específico"""
    try:
        p = Product.query.get_or_404(product_id)
        
        # Buscar reviews com informações do usuário
        reviews = (
            Review.query.filter_by(product_id=p.id)
            .join(User, Review.user_id == User.id)
            .add_columns(User.nome, Review.nota, Review.comentario, Review.created_at)
            .all()
        )
        
        revs = [
            {
                "nome": r.nome,
                "nota": r.nota,
                "comentario": r.comentario,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ]
        
        return jsonify({
            "id": p.id,
            "titulo": p.titulo,
            "descricao": p.descricao,
            "preco": p.preco,
            "imagem": p.imagem,
            "estoque": p.estoque,
            "reviews": revs
        })
        
    except Exception as e:
        logger.error(f"Erro ao carregar produto {product_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao carregar produto"}), 500


@products_bp.route("/api/products/search")
def api_products_search():
    """Busca e filtra produtos com parâmetros de query"""
    try:
        query = request.args.get('q', '').strip()
        preco_min = request.args.get('preco_min', type=float)
        preco_max = request.args.get('preco_max', type=float)
        ordenar = request.args.get('ordenar', 'nome')  # nome, preco_asc, preco_desc, estoque
        
        # Query base
        produtos = Product.query
        
        # Filtro de busca por título ou descrição
        if query:
            produtos = produtos.filter(
                db.or_(
                    Product.titulo.ilike(f'%{query}%'),
                    Product.descricao.ilike(f'%{query}%')
                )
            )
        
        # Filtros de preço
        if preco_min is not None:
            produtos = produtos.filter(Product.preco >= preco_min)
        if preco_max is not None:
            produtos = produtos.filter(Product.preco <= preco_max)
        
        # Ordenação
        if ordenar == 'preco_asc':
            produtos = produtos.order_by(Product.preco.asc())
        elif ordenar == 'preco_desc':
            produtos = produtos.order_by(Product.preco.desc())
        elif ordenar == 'estoque':
            produtos = produtos.order_by(Product.estoque.desc())
        else:  # nome
            produtos = produtos.order_by(Product.titulo.asc())
        
        produtos = produtos.all()
        data = []
        
        for p in produtos:
            avg = db.session.query(db.func.avg(Review.nota)).filter(Review.product_id == p.id).scalar() or 0
            count = Review.query.filter_by(product_id=p.id).count()
            imagem = p.imagem.replace('imagens/', '') if p.imagem and p.imagem.startswith('imagens/') else (p.imagem or '')
            
            data.append({
                "id": p.id,
                "titulo": p.titulo,
                "descricao": p.descricao,
                "preco": p.preco,
                "imagem": imagem,
                "estoque": p.estoque,
                "media": round(float(avg), 2),
                "n_reviews": count
            })
        
        logger.info(f"Busca de produtos - Query: '{query}' - {len(data)} resultados")
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao buscar produtos"}), 500


# ============================================
# CARRINHO DE COMPRAS
# ============================================

@products_bp.route('/carrinho/add/<int:id>', methods=['POST'])
def carrinho_add(id):
    """Adiciona produto ao carrinho"""
    from app.utils import Validator
    
    try:
        produto = Product.query.get(id)
        if not produto:
            logger.warning(f"Tentativa de adicionar produto inexistente ao carrinho: ID {id}")
            return "Produto não encontrado", 404

        # Verifica estoque disponível
        if produto.estoque <= 0:
            logger.warning(f"Tentativa de adicionar produto esgotado: ID {id}")
            return "Produto esgotado", 400

        if 'user_id' in session:
            # Usuário logado - salva no banco
            user_id = session['user_id']
            item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
            
            quantidade_atual = item.quantity if item else 0
            if quantidade_atual + 1 > produto.estoque:
                return "Estoque insuficiente", 400
            
            if item:
                item.quantity += 1
            else:
                db.session.add(CartItem(user_id=user_id, product_id=id, quantity=1))
            
            db.session.commit()
            logger.info(f"Produto adicionado ao carrinho (DB) - User: {user_id}, Produto: {id}")
            return "OK (db)", 200
        else:
            # Visitante - salva na sessão
            carrinho = session.get('cart', {})
            quantidade_atual = carrinho.get(str(id), 0)
            
            if quantidade_atual + 1 > produto.estoque:
                return "Estoque insuficiente", 400
            
            carrinho[str(id)] = quantidade_atual + 1
            session['cart'] = carrinho
            session.modified = True
            
            logger.info(f"Produto adicionado ao carrinho (sessão) - Produto: {id}")
            return "OK (sessão)", 200
            
    except Exception as e:
        logger.error(f"Erro ao adicionar produto {id} ao carrinho: {str(e)}", exc_info=True)
        return "Erro ao adicionar ao carrinho", 500


@products_bp.route("/carrinho")
def ver_carrinho():
    """Página do carrinho de compras"""
    try:
        produtos, total = [], 0
        
        if 'user_id' in session:
            # Carrinho do banco de dados
            user_id = session['user_id']
            for item in CartItem.query.filter_by(user_id=user_id).all():
                p = item.product
                if p:
                    subtotal = p.preco * item.quantity
                    total += subtotal
                    produtos.append({
                        "id": p.id,
                        "titulo": p.titulo,
                        "preco": p.preco,
                        "quantidade": item.quantity,
                        "subtotal": subtotal,
                        "imagem": p.imagem
                    })
        else:
            # Carrinho da sessão
            carrinho = session.get('cart', {})
            for pid, qtd in carrinho.items():
                p = Product.query.get(int(pid))
                if p:
                    subtotal = p.preco * qtd
                    total += subtotal
                    produtos.append({
                        "id": p.id,
                        "titulo": p.titulo,
                        "preco": p.preco,
                        "quantidade": qtd,
                        "subtotal": subtotal,
                        "imagem": p.imagem
                    })
        
        logger.info(f"Carrinho visualizado - Total: R$ {total:.2f} - {len(produtos)} itens")
        return render_template("carrinho.html", produtos=produtos, total=total)
        
    except Exception as e:
        logger.error(f"Erro ao carregar carrinho: {str(e)}", exc_info=True)
        return render_template("erro.html", mensagem="Erro ao carregar carrinho"), 500


@products_bp.route('/carrinho/update/<int:id>/<string:acao>', methods=['POST'])
def carrinho_update(id, acao):
    """Atualiza quantidade de produto no carrinho"""
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
            
            if acao == 'add':
                if item:
                    item.quantity += 1
                else:
                    db.session.add(CartItem(user_id=user_id, product_id=id, quantity=1))
            elif acao == 'sub' and item:
                item.quantity -= 1
                if item.quantity <= 0:
                    db.session.delete(item)
            
            db.session.commit()
            logger.info(f"Carrinho atualizado (DB) - User: {user_id}, Produto: {id}, Ação: {acao}")
            return "OK", 200
        else:
            carrinho = session.get('cart', {})
            key = str(id)
            
            if acao == 'add':
                carrinho[key] = carrinho.get(key, 0) + 1
            elif acao == 'sub' and key in carrinho:
                carrinho[key] -= 1
                if carrinho[key] <= 0:
                    del carrinho[key]
            
            session['cart'] = carrinho
            session.modified = True
            
            logger.info(f"Carrinho atualizado (sessão) - Produto: {id}, Ação: {acao}")
            return "OK", 200
            
    except Exception as e:
        logger.error(f"Erro ao atualizar carrinho - Produto: {id}, Ação: {acao}: {str(e)}", exc_info=True)
        return "Erro ao atualizar carrinho", 500


@products_bp.route('/carrinho/remove/<int:id>', methods=['POST'])
def carrinho_remove(id):
    """Remove produto do carrinho"""
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            CartItem.query.filter_by(user_id=user_id, product_id=id).delete()
            db.session.commit()
            logger.info(f"Produto removido do carrinho (DB) - User: {user_id}, Produto: {id}")
            return "OK", 200
        else:
            carrinho = session.get('cart', {})
            if str(id) in carrinho:
                del carrinho[str(id)]
            session['cart'] = carrinho
            session.modified = True
            logger.info(f"Produto removido do carrinho (sessão) - Produto: {id}")
            return "OK", 200
            
    except Exception as e:
        logger.error(f"Erro ao remover produto {id} do carrinho: {str(e)}", exc_info=True)
        return "Erro ao remover do carrinho", 500


@products_bp.route("/api/carrinho")
def api_carrinho():
    """API que retorna o conteúdo atual do carrinho"""
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            itens = CartItem.query.filter_by(user_id=user_id).all()
            return jsonify({
                "itens": [
                    {"produto_id": i.product_id, "quantidade": i.quantity}
                    for i in itens
                ]
            })
        else:
            carrinho = session.get("cart", {})
            itens = [{"produto_id": int(k), "quantidade": v} for k, v in carrinho.items()]
            return jsonify({"itens": itens})
            
    except Exception as e:
        logger.error(f"Erro ao obter carrinho via API: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao carregar carrinho"}), 500
