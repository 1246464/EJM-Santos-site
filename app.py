# ============================================
# app.py — EJM SANTOS - Loja de Mel Natural 🍯
# ============================================

import mercadopago as mp
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, jsonify, render_template,
    session, redirect
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy import extract

# -------------------------------------------------------
# CONFIGURAÇÃO INICIAL
# -------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "ejm.db")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("EJM_SECRET", "troque_esta_chave_por_uma_segura")

db = SQLAlchemy(app)

# -------------------------------------------------------
# MODELOS DE BANCO DE DADOS
# -------------------------------------------------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(20), default="Pendente")
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    items = db.relationship("OrderItem", backref="order", cascade="all, delete")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantidade = db.Column(db.Integer, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)


class User(db.Model):
    """Usuário do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # 🧩 novo campo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    """Produto à venda"""
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(256))
    mercado_pago_link = db.Column(db.String(400))

class Purchase(db.Model):
    """Registro de compras simuladas"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    """Avaliações dos produtos"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    nota = db.Column(db.Integer, nullable=False)  # de 1 a 5
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product')


# -------------------------------------------------------
# DECORATOR - Verificação de token JWT
# -------------------------------------------------------
def token_required(f):
    """Protege rotas da API que exigem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", None)
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"message": "Token ausente"}), 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                return jsonify({"message": "Usuário não encontrado"}), 401
        except Exception as e:
            return jsonify({"message": "Token inválido", "error": str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    """Restringe acesso a administradores"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return render_template("erro.html", mensagem="Acesso negado: apenas administradores.")
        return f(*args, **kwargs)
    return decorated


# -------------------------------------------------------
# ROTAS DE LOGIN / LOGOUT (Site)
# -------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Página de login do site (HTML)"""
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        if not (email and senha):
            return render_template("login.html", erro="Preencha todos os campos.")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha_hash, senha):
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            print("Sessão iniciada:", session)  # debug opcional
            return redirect("/")
        else:
            return render_template("login.html", erro="Credenciais inválidas.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Encerra a sessão do usuário"""
    session.clear()
    return redirect("/")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Login específico para administradores"""
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha_hash, senha) and user.is_admin:
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            return redirect("/admin")
        else:
            return render_template("admin_login.html", erro="Credenciais inválidas ou sem permissão.")
    return render_template("admin_login.html")

@app.route("/admin")
@admin_required
def admin_dashboard():
    pedidos = Order.query.all()

    total_pedidos = len(pedidos)
    total_pago = sum(1 for p in pedidos if p.status == "Pago")
    enviados = sum(1 for p in pedidos if p.status == "Enviado")
    entregues = sum(1 for p in pedidos if p.status == "Entregue")
    cancelados = sum(1 for p in pedidos if p.status == "Cancelado")

    faturamento = sum(p.total for p in pedidos if p.status in ["Pago", "Enviado", "Entregue"])
    ticket_medio = (faturamento / total_pago) if total_pago > 0 else 0

    # Pegando produtos para a tabela ✅
    produtos = Product.query.all()

    # Gráfico dos últimos 6 meses
    hoje = datetime.utcnow()
    meses_labels = []
    meses_valores = []

    for i in range(5, -1, -1):
        mes_ref = hoje - timedelta(days=30 * i)
        ano = mes_ref.year
        mes = mes_ref.month

        pedidos_mes = Order.query.filter(
            extract('year', Order.created_at) == ano,
            extract('month', Order.created_at) == mes,
            Order.status.in_(["Pago", "Enviado", "Entregue"])
        ).all()

        total_mes = sum(p.total for p in pedidos_mes)

        meses_labels.append(mes_ref.strftime("%b/%Y"))
        meses_valores.append(total_mes)

    return render_template(
        "admin_dashboard.html",
        produtos=produtos,  # ✅ enviado para o template!
        total_pedidos=total_pedidos,
        total_pago=total_pago,
        enviados=enviados,
        entregues=entregues,
        cancelados=cancelados,
        faturamento=faturamento,
        ticket_medio=ticket_medio,
        meses_labels=meses_labels,
        meses_valores=meses_valores
    )

# -------------------------------------------------------
# ROTAS DE API (JSON)
# -------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def api_register():
    """Cadastro de usuário (API JSON)"""
    data = request.json or {}
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")

    if not (nome and email and senha):
        return jsonify({"message": "Campos obrigatórios: nome, email, senha"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email já cadastrado"}), 400

    user = User(nome=nome, email=email, senha_hash=generate_password_hash(senha))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Cadastro realizado com sucesso"}), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    """Login via API (gera token JWT)"""
    data = request.json or {}
    email = data.get("email")
    senha = data.get("senha")

    if not (email and senha):
        return jsonify({"message": "Email e senha necessários"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.senha_hash, senha):
        return jsonify({"message": "Credenciais inválidas"}), 401

    payload = {
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "token": token,
        "user": {"id": user.id, "nome": user.nome, "email": user.email}
    })

@app.route("/api/products", methods=["GET"])
def api_products():
    """Lista de produtos disponíveis"""
    prods = Product.query.all()
    data = []
    for p in prods:
        avg = db.session.query(db.func.avg(Review.nota)).filter(Review.product_id == p.id).scalar() or 0
        count = Review.query.filter_by(product_id=p.id).count()
        data.append({
            "id": p.id,
            "titulo": p.titulo,
            "descricao": p.descricao,
            "preco": p.preco,
            "imagem": p.imagem,
            "mercado_pago_link": p.mercado_pago_link,
            "media": round(float(avg), 2),
            "n_reviews": count
        })
    return jsonify(data)

@app.route("/api/product/<int:product_id>", methods=["GET"])
def api_product_detail(product_id):
    """Detalhes e avaliações de um produto"""
    p = Product.query.get_or_404(product_id)
    reviews = (
        Review.query.filter_by(product_id=p.id)
        .join(User, Review.user_id == User.id)
        .add_columns(User.nome, Review.nota, Review.comentario, Review.created_at)
        .all()
    )
    revs = [{
        "nome": r.nome,
        "nota": r.nota,
        "comentario": r.comentario,
        "created_at": r.created_at.isoformat()
    } for r in reviews]

    return jsonify({
        "id": p.id,
        "titulo": p.titulo,
        "descricao": p.descricao,
        "preco": p.preco,
        "imagem": p.imagem,
        "mercado_pago_link": p.mercado_pago_link,
        "reviews": revs
    })

@app.route("/api/purchase", methods=["POST"])
@token_required
def api_purchase(current_user):
    """Simula uma compra de produto (API protegida)"""
    data = request.json or {}
    product_id = data.get("product_id")
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"message": "Produto não encontrado"}), 404

    purchase = Purchase(user_id=current_user.id, product_id=product_id)
    db.session.add(purchase)
    db.session.commit()
    return jsonify({"message": "Compra registrada com sucesso."})

@app.route("/api/review", methods=["POST"])
@token_required
def api_review(current_user):
    """Envia uma avaliação de produto"""
    data = request.json or {}
    product_id = data.get("product_id")
    nota = data.get("nota")
    comentario = data.get("comentario", "")

    if not (product_id and nota):
        return jsonify({"message": "Product_id e nota são obrigatórios"}), 400

    # só pode avaliar se comprou
    bought = Purchase.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not bought:
        return jsonify({"message": "Você só pode avaliar produtos que comprou."}), 403

    try:
        nota_int = int(nota)
        if nota_int < 1 or nota_int > 5:
            raise ValueError()
    except:
        return jsonify({"message": "Nota deve ser entre 1 e 5"}), 400

    review = Review(user_id=current_user.id, product_id=product_id, nota=nota_int, comentario=comentario)
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Avaliação registrada com sucesso."})

@app.route("/api/me", methods=["GET"])
@token_required
def api_me(current_user):
    """Retorna dados do usuário logado (API)"""
    purchases = (
        db.session.query(Product.id, Product.titulo)
        .join(Purchase, Purchase.product_id == Product.id)
        .filter(Purchase.user_id == current_user.id)
        .all()
    )
    return jsonify({
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "compras": [{"product_id": pid, "titulo": titulo} for pid, titulo in purchases]
    })

@app.route("/api/reviews/me", methods=["GET"])
@token_required
def api_reviews_me(current_user):
    """Lista avaliações feitas pelo usuário"""
    reviews = (
        db.session.query(Review, Product.titulo)
        .join(Product, Review.product_id == Product.id)
        .filter(Review.user_id == current_user.id)
        .all()
    )
    return jsonify([
        {"titulo": titulo, "nota": r.nota, "comentario": r.comentario}
        for r, titulo in reviews
    ])

# -------------------------------------------------------
# ROTAS DE PÁGINAS (Front-end HTML)
# -------------------------------------------------------
@app.route("/")
def index():
    """Página inicial"""
    return render_template("index.html")

@app.route("/produtos")
def produtos_page():
    """Página de produtos"""
    return render_template("produtos.html")

@app.route("/produto/<int:product_id>")
def produto_page(product_id):
    """Página de detalhes de produto"""
    return render_template("produto.html", product_id=product_id)

@app.route("/perfil")
def perfil_page():
    """Página de perfil do usuário"""
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("perfil.html")

@app.route("/sobre")
def sobre_page():
    """Página sobre a empresa"""
    return render_template("sobre.html")

# -------------------------------------------------------
# CONTROLE DE CACHE (para refletir login imediatamente)
# -------------------------------------------------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# -------------------------------------------------------
# ROTAS DE GERENCIAMENTO DE PRODUTOS (ADMIN)
# -------------------------------------------------------
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(app.static_folder, "imagens")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/admin/novo", methods=["GET", "POST"])
@admin_required
def admin_novo_produto():
    """Cria um novo produto"""
    if request.method == "POST":
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        preco = request.form.get("preco")
        link = request.form.get("mercado_pago_link")

        imagem_file = request.files.get("imagem")
        nome_arquivo = None
        if imagem_file and imagem_file.filename:
            nome_arquivo = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))

        p = Product(
            titulo=titulo,
            descricao=descricao,
            preco=float(preco or 0),
            imagem=f"imagens/{nome_arquivo}" if nome_arquivo else "",
            mercado_pago_link=link,
        )
        db.session.add(p)
        db.session.commit()
        return redirect("/admin")

    return render_template("admin_novo.html")


@app.route("/admin/editar/<int:pid>", methods=["GET", "POST"])
@admin_required
def admin_editar_produto(pid):
    """Edita um produto existente"""
    p = Product.query.get_or_404(pid)
    if request.method == "POST":
        p.titulo = request.form.get("titulo")
        p.descricao = request.form.get("descricao")
        p.preco = float(request.form.get("preco") or 0)
        p.mercado_pago_link = request.form.get("mercado_pago_link")

        imagem_file = request.files.get("imagem")
        if imagem_file and imagem_file.filename:
            nome_arquivo = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))
            p.imagem = f"imagens/{nome_arquivo}"

        db.session.commit()
        return redirect("/admin")

    return render_template("admin_editar.html", produto=p)


@app.route("/admin/remover/<int:pid>")
@admin_required
def admin_remover_produto(pid):
    """Remove um produto"""
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return redirect("/admin")

@app.route('/carrinho/add/<int:id>', methods=['POST'])
def carrinho_add(id):
    produto = Product.query.get(id)
    if not produto:
        return "Produto não encontrado", 404

    # Se o usuário estiver logado → salva no banco
    if 'user_id' in session:
        user_id = session['user_id']
        item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()

        if item:
            item.quantity += 1
        else:
            novo = CartItem(user_id=user_id, product_id=id, quantity=1)
            db.session.add(novo)

        db.session.commit()
        return "Item adicionado ao carrinho (banco)", 200

    # Se o usuário NÃO estiver logado → salva na sessão
    carrinho = session.get('cart', {})
    id_str = str(id)

    if id_str in carrinho:
        carrinho[id_str] += 1
    else:
        carrinho[id_str] = 1

    session['cart'] = carrinho
    session.modified = True

    return "Item adicionado ao carrinho (sessão)", 200


@app.route("/carrinho")
def ver_carrinho():
    produtos = []
    total = 0

    if 'user_id' in session:
        user_id = session['user_id']
        itens = CartItem.query.filter_by(user_id=user_id).all()
        for item in itens:
            p = item.product
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
        carrinho = session.get('cart', {})
        for id, qtd in carrinho.items():
            p = Product.query.get(int(id))
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

    return render_template("carrinho.html", produtos=produtos, total=total)


@app.route('/carrinho/update/<int:id>/<string:acao>', methods=['POST'])
def carrinho_update(id, acao):
    id = int(id)

    # 🧩 Se o usuário estiver logado → salva no banco
    if 'user_id' in session:
        user_id = session['user_id']
        item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()

        if acao == 'add':
            if item:
                item.quantity += 1
            else:
                novo = CartItem(user_id=user_id, product_id=id, quantity=1)
                db.session.add(novo)

        elif acao == 'sub':
            if item:
                item.quantity -= 1
                if item.quantity <= 0:
                    db.session.delete(item)

        db.session.commit()
        return "OK", 200

    # 🧩 Se o usuário NÃO estiver logado → salva na sessão
    carrinho = session.get('cart', {})
    id_str = str(id)

    if acao == 'add':
        carrinho[id_str] = carrinho.get(id_str, 0) + 1
    elif acao == 'sub':
        if id_str in carrinho:
            carrinho[id_str] -= 1
            if carrinho[id_str] <= 0:
                del carrinho[id_str]

    session['cart'] = carrinho
    session.modified = True
    return "OK", 200


@app.route('/carrinho/remove/<int:id>', methods=['POST'])
def carrinho_remove(id):
    carrinho = session.get('cart', {})
    id = str(id)
    if id in carrinho:
        del carrinho[id]
    session['cart'] = carrinho
    session.modified = True
    return "OK", 200

@app.route("/finalizar-compra")
def finalizar_compra():
    if not session.get('user_id'):
        session['redirect_after_login'] = "/finalizar-compra"
        return redirect("/login")

    carrinho = session.get('cart', {})
    if not carrinho:
        return redirect("/carrinho")

    total = 0
    items = []

    for pid, qtd in carrinho.items():
        p = Product.query.get(int(pid))
        if p:
            subtotal = p.preco * qtd
            total += subtotal
            items.append((p, qtd, p.preco))

    # Criar o pedido
    pedido = Order(
        user_id=session['user_id'],
        total=total,
        status="Pendente"
    )
    db.session.add(pedido)
    db.session.commit()  # ✅ gera id do pedido

    # Criar os itens do pedido
    for p, qtd, preco in items:
        item = OrderItem(
            order_id=pedido.id,
            product_id=p.id,
            quantidade=qtd,
            preco_unitario=preco
        )
        db.session.add(item)

    db.session.commit()

    # Esvaziar o carrinho
    session.pop('cart', None)

    return redirect(f"/pedido/{pedido.id}")

@app.route("/pedido/<int:id>")
def ver_pedido(id):
    if not session.get('user_id'):
        return redirect("/login")

    pedido = Order.query.get_or_404(id)
    if pedido.user_id != session.get('user_id') and not session.get('is_admin'):
        return "Acesso não autorizado", 403

    items = OrderItem.query.filter_by(order_id=id).all()

    return render_template("pedido_detalhe.html", pedido=pedido, items=items)

@app.route("/checkout", methods=["POST"])
def checkout():
    carrinho = session.get("carrinho", {})

    if not carrinho:
        return jsonify({"error": "Carrinho vazio"}), 400

    items = []
    total = 0

    for product_id, qtd in carrinho.items():
        product = Product.query.get(product_id)
        if not product:
            continue

        subtotal = product.preco * qtd
        total += subtotal

        items.append({
            "title": product.titulo,
            "quantity": qtd,
            "unit_price": float(product.preco),
            "currency_id": "BRL"
        })

    preference_data = {
        "items": items,
        "back_urls": {
            "success": "http://localhost:5000/pedido/sucesso",
            "failure": "http://localhost:5000/pedido/erro",
            "pending": "http://localhost:5000/pedido/pendente"
        },
        "auto_return": "approved"
    }

    preference = mp.preference().create(preference_data)
    link_pagamento = preference["response"]["init_point"]

    return jsonify({"checkout_url": link_pagamento})


# ---------------------------
# ADMIN: PEDIDOS
# ---------------------------
@app.route("/admin/pedidos")
@admin_required
def admin_pedidos():
    # Ordena mais recentes primeiro
    pedidos = Order.query.order_by(Order.created_at.desc()).all()
    # Mapeia itens por pedido para mostrar contagem rápida
    itens_por_pedido = {
        p.id: OrderItem.query.filter_by(order_id=p.id).count() for p in pedidos
    }
    return render_template("admin_pedidos.html", pedidos=pedidos, itens_por_pedido=itens_por_pedido)


@app.route("/admin/pedidos/<int:pedido_id>")
@admin_required
def admin_pedido_detalhe(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    itens = OrderItem.query.filter_by(order_id=pedido_id).all()

    # Dados do usuário (se quiser mostrar nome/email)
    user = User.query.get(pedido.user_id)

    # Monta itens com produto associado
    detalhe_itens = []
    for it in itens:
        prod = Product.query.get(it.product_id)
        detalhe_itens.append({
            "id": it.id,
            "produto_id": it.product_id,
            "titulo": prod.titulo if prod else f"#{it.product_id}",
            "preco_unit": it.preco_unitario,
            "quantidade": it.quantidade,
            "subtotal": it.preco_unitario * it.quantidade,
            "imagem": prod.imagem if prod else ""
        })

    return render_template(
        "admin_pedido_detalhe.html",
        pedido=pedido,
        itens=detalhe_itens,
        user=user
    )


@app.route("/admin/pedidos/<int:pedido_id>/status", methods=["POST"])
@admin_required
def admin_pedido_status(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    novo_status = request.form.get("status")

    # Opcional: validar fluxo (Pendente -> Pago -> Enviado -> Entregue)
    status_validos = ["Pendente", "Pago", "Enviado", "Entregue", "Cancelado"]
    if novo_status not in status_validos:
        return "Status inválido", 400

    pedido.status = novo_status
    db.session.commit()
    return redirect(f"/admin/pedidos/{pedido_id}")

# -------------------------------------------------------
# EXECUÇÃO DO APP
# -------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
