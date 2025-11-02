# ============================================
# app.py — EJM SANTOS - Loja de Mel Natural 🍯
# Versão consolidada, documentada e pronta p/ Checkout Pro
# ============================================

import os
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
import mercadopago
from flask import (
    Flask, request, jsonify, render_template,
    session, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy import extract

# -----------------------------
# Config / Bootstrap
# -----------------------------
load_dotenv()

from pathlib import Path
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "ejm.db")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("EJM_SECRET", "chave_fallback")

db = SQLAlchemy(app)

# Helper: SDK Mercado Pago
def mp_sdk():
    token = os.getenv("MP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("MP_ACCESS_TOKEN não definido no .env")
    return mercadopago.SDK(token)

# -----------------------------
# MODELOS
# -----------------------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pendente")  # Pendente, Pago, Enviado...
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Relacionamento
    itens = db.relationship('OrderItem', backref='pedido', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantidade = db.Column(db.Integer)
    preco_unitario = db.Column(db.Float)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(256))
    mercado_pago_link = db.Column(db.String(400))

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    comentario = db.Column(db.Text)
    nota = db.Column(db.Integer)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product')

# -----------------------------
# Helpers de Autenticação
# -----------------------------
def token_required(f):
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

# -----------------------------
# Helpers de Carrinho / Pedido
# -----------------------------
def snapshot_cart_for_checkout():
    """
    Retorna itens do carrinho atual em formato padrão:
    [{"titulo": str, "quantidade": int, "preco": float, "product_id": int}]
    Considera usuário logado (DB) e visitante (session['cart']).
    """
    itens = []
    if session.get('user_id'):
        user_id = session['user_id']
        for it in CartItem.query.filter_by(user_id=user_id).all():
            if it.product:
                itens.append({
                    "titulo": it.product.titulo,
                    "quantidade": int(it.quantity),
                    "preco": float(it.product.preco),
                    "product_id": it.product.id
                })
    else:
        cart = session.get('cart', {})
        for pid_str, qtd in cart.items():
            p = Product.query.get(int(pid_str))
            if p:
                itens.append({
                    "titulo": p.titulo,
                    "quantidade": int(qtd),
                    "preco": float(p.preco),
                    "product_id": p.id
                })
    return itens

def clear_current_cart():
    """Esvazia o carrinho (session e DB do usuário logado)."""
    session.pop('cart', None)
    if session.get('user_id'):
        CartItem.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()

def create_order_from_items(user_id, itens):
    """Cria Order + OrderItems a partir dos itens do carrinho."""
    total = sum(i["preco"] * i["quantidade"] for i in itens)
    pedido = Order(user_id=user_id, total=total, status="Pendente")
    db.session.add(pedido)
    db.session.commit()  # gera pedido.id

    for it in itens:
        db.session.add(OrderItem(
            order_id=pedido.id,
            product_id=it["product_id"],
            quantidade=it["quantidade"],
            preco_unitario=it["preco"]
        ))
    db.session.commit()
    return pedido

# -----------------------------
# ROTAS: Login / Logout / Admin
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login_page():
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
            return redirect("/")
        return render_template("login.html", erro="Credenciais inválidas.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha_hash, senha) and user.is_admin:
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            return redirect("/admin")
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

    hoje = datetime.utcnow()
    meses_labels, meses_valores = [], []
    for i in range(5, -1, -1):
        mes_ref = hoje - timedelta(days=30 * i)
        ano, mes = mes_ref.year, mes_ref.month
        pedidos_mes = Order.query.filter(
            extract('year', Order.created_at) == ano,
            extract('month', Order.created_at) == mes,
            Order.status.in_(["Pago", "Enviado", "Entregue"])
        ).all()
        total_mes = sum(p.total for p in pedidos_mes)
        meses_labels.append(mes_ref.strftime("%b/%Y"))
        meses_valores.append(total_mes)

    produtos = Product.query.all()
    return render_template(
        "admin_dashboard.html",
        produtos=produtos,
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

# -----------------------------
# API (JSON)
# -----------------------------
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    nome, email, senha = data.get("nome"), data.get("email"), data.get("senha")
    if not (nome and email and senha):
        return jsonify({"message": "Campos obrigatórios: nome, email, senha"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email já cadastrado"}), 400
    user = User(nome=nome, email=email, senha_hash=generate_password_hash(senha))
    db.session.add(user); db.session.commit()
    return jsonify({"message": "Cadastro realizado com sucesso"}), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    email, senha = data.get("email"), data.get("senha")
    if not (email and senha):
        return jsonify({"message": "Email e senha necessários"}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.senha_hash, senha):
        return jsonify({"message": "Credenciais inválidas"}), 401
    payload = {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)}
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": token, "user": {"id": user.id, "nome": user.nome, "email": user.email}})

@app.route("/api/products")
def api_products():
    prods = Product.query.all()
    data = []
    for p in prods:
        avg = db.session.query(db.func.avg(Review.nota)).filter(Review.product_id == p.id).scalar() or 0
        count = Review.query.filter_by(product_id=p.id).count()
        data.append({
            "id": p.id, "titulo": p.titulo, "descricao": p.descricao, "preco": p.preco,
            "imagem": p.imagem, "mercado_pago_link": p.mercado_pago_link,
            "media": round(float(avg), 2), "n_reviews": count
        })
    return jsonify(data)

@app.route("/api/product/<int:product_id>")
def api_product_detail(product_id):
    p = Product.query.get_or_404(product_id)
    reviews = (
        Review.query.filter_by(product_id=p.id)
        .join(User, Review.user_id == User.id)
        .add_columns(User.nome, Review.nota, Review.comentario, Review.created_at)
        .all()
    )
    revs = [{"nome": r.nome, "nota": r.nota, "comentario": r.comentario, "created_at": r.created_at.isoformat()} for r in reviews]
    return jsonify({"id": p.id, "titulo": p.titulo, "descricao": p.descricao, "preco": p.preco, "imagem": p.imagem,
                    "mercado_pago_link": p.mercado_pago_link, "reviews": revs})

@app.route("/api/purchase", methods=["POST"])
@token_required
def api_purchase(current_user):
    data = request.json or {}
    product_id = data.get("product_id")
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"message": "Produto não encontrado"}), 404
    db.session.add(Purchase(user_id=current_user.id, product_id=product_id))
    db.session.commit()
    return jsonify({"message": "Compra registrada com sucesso."})

@app.route("/api/review", methods=["POST"])
@token_required
def api_review(current_user):
    data = request.json or {}
    product_id, nota, comentario = data.get("product_id"), data.get("nota"), data.get("comentario", "")
    if not (product_id and nota):
        return jsonify({"message": "product_id e nota são obrigatórios"}), 400
    if not Purchase.query.filter_by(user_id=current_user.id, product_id=product_id).first():
        return jsonify({"message": "Você só pode avaliar produtos que comprou."}), 403
    try:
        nota_int = int(nota)
        if not (1 <= nota_int <= 5):
            raise ValueError()
    except:
        return jsonify({"message": "Nota deve ser entre 1 e 5"}), 400
    db.session.add(Review(user_id=current_user.id, product_id=product_id, nota=nota_int, comentario=comentario))
    db.session.commit()
    return jsonify({"message": "Avaliação registrada com sucesso."})

@app.route("/api/me")
@token_required
def api_me(current_user):
    purchases = (
        db.session.query(Product.id, Product.titulo)
        .join(Purchase, Purchase.product_id == Product.id)
        .filter(Purchase.user_id == current_user.id)
        .all()
    )
    return jsonify({"id": current_user.id, "nome": current_user.nome, "email": current_user.email,
                    "compras": [{"product_id": pid, "titulo": titulo} for pid, titulo in purchases]})

@app.route("/api/reviews/me")
@token_required
def api_reviews_me(current_user):
    reviews = (
        db.session.query(Review, Product.titulo)
        .join(Product, Review.product_id == Product.id)
        .filter(Review.user_id == current_user.id)
        .all()
    )
    return jsonify([{"titulo": titulo, "nota": r.nota, "comentario": r.comentario} for r, titulo in reviews])

# -----------------------------
# Páginas (HTML)
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/produtos")
def produtos_page():
    return render_template("produtos.html")

@app.route("/produto/<int:product_id>")
def produto_page(product_id):
    return render_template("produto.html", product_id=product_id)

@app.route("/perfil")
def perfil_page():
    if not session.get("user_id"):
        return redirect("/login")
    return render_template("perfil.html")

@app.route("/sobre")
def sobre_page():
    return render_template("sobre.html")

# Evita cache de páginas pós-login
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# -----------------------------
# Admin: Produtos (upload)
# -----------------------------
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = os.path.join(app.static_folder, "imagens")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/admin/novo", methods=["GET", "POST"])
@admin_required
def admin_novo_produto():
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
            titulo=titulo, descricao=descricao, preco=float(preco or 0),
            imagem=f"imagens/{nome_arquivo}" if nome_arquivo else "",
            mercado_pago_link=link
        )
        db.session.add(p); db.session.commit()
        return redirect("/admin")
    return render_template("admin_novo.html")

@app.route("/admin/editar/<int:pid>", methods=["GET", "POST"])
@admin_required
def admin_editar_produto(pid):
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
    p = Product.query.get_or_404(pid)
    db.session.delete(p); db.session.commit()
    return redirect("/admin")

# -----------------------------
# Carrinho (DB p/ logados, sessão p/ visitantes)
# -----------------------------
@app.route('/carrinho/add/<int:id>', methods=['POST'])
def carrinho_add(id):
    produto = Product.query.get(id)
    if not produto: return "Produto não encontrado", 404

    if 'user_id' in session:
        user_id = session['user_id']
        item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
        if item: item.quantity += 1
        else: db.session.add(CartItem(user_id=user_id, product_id=id, quantity=1))
        db.session.commit()
        return "OK (db)", 200

    carrinho = session.get('cart', {})
    carrinho[str(id)] = carrinho.get(str(id), 0) + 1
    session['cart'] = carrinho; session.modified = True
    return "OK (sessão)", 200

@app.route("/carrinho")
def ver_carrinho():
    produtos, total = [], 0
    if 'user_id' in session:
        user_id = session['user_id']
        for item in CartItem.query.filter_by(user_id=user_id).all():
            p = item.product
            if p:
                subtotal = p.preco * item.quantity
                total += subtotal
                produtos.append({"id": p.id, "titulo": p.titulo, "preco": p.preco,
                                 "quantidade": item.quantity, "subtotal": subtotal, "imagem": p.imagem})
    else:
        carrinho = session.get('cart', {})
        for pid, qtd in carrinho.items():
            p = Product.query.get(int(pid))
            if p:
                subtotal = p.preco * qtd
                total += subtotal
                produtos.append({"id": p.id, "titulo": p.titulo, "preco": p.preco,
                                 "quantidade": qtd, "subtotal": subtotal, "imagem": p.imagem})
    return render_template("carrinho.html", produtos=produtos, total=total)

@app.route('/carrinho/update/<int:id>/<string:acao>', methods=['POST'])
def carrinho_update(id, acao):
    if 'user_id' in session:
        user_id = session['user_id']
        item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
        if acao == 'add':
            if item: item.quantity += 1
            else: db.session.add(CartItem(user_id=user_id, product_id=id, quantity=1))
        elif acao == 'sub' and item:
            item.quantity -= 1
            if item.quantity <= 0: db.session.delete(item)
        db.session.commit()
        return "OK", 200

    carrinho = session.get('cart', {}); key = str(id)
    if acao == 'add': carrinho[key] = carrinho.get(key, 0) + 1
    elif acao == 'sub' and key in carrinho:
        carrinho[key] -= 1
        if carrinho[key] <= 0: del carrinho[key]
    session['cart'] = carrinho; session.modified = True
    return "OK", 200

@app.route('/carrinho/remove/<int:id>', methods=['POST'])
def carrinho_remove(id):
    if 'user_id' in session:
        user_id = session['user_id']
        item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
        if item: db.session.delete(item); db.session.commit()
        return "OK", 200
    carrinho = session.get('cart', {})
    carrinho.pop(str(id), None)
    session['cart'] = carrinho; session.modified = True
    return "OK", 200

# -----------------------------
# Fluxo de pedido local (pré-checkout)
# -----------------------------
@app.route("/finalizar-compra")
def finalizar_compra():
    if not session.get('user_id'):
        session['redirect_after_login'] = "/finalizar-compra"
        return redirect("/login")

    itens = snapshot_cart_for_checkout()
    if not itens:
        return redirect("/carrinho")

    pedido = create_order_from_items(session['user_id'], itens)
    # Esvazia carrinho após criar pedido (para não duplicar)
    clear_current_cart()
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

# -----------------------------
# CHECKOUT PRO — Mercado Pago
# -----------------------------
@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Cria uma preferência de pagamento do Mercado Pago
    com base no carrinho atual. Suporta ambiente local
    e ambiente de produção (Render).
    """

    # 1️⃣ Verifica se o usuário está logado
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Usuário não logado."}), 401

    # 2️⃣ Captura itens do carrinho
    carrinho_itens = snapshot_cart_for_checkout()
    if not carrinho_itens:
        return jsonify({"error": "Carrinho vazio."}), 400

    # 3️⃣ Inicializa o SDK do Mercado Pago
    import mercadopago
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

    # 4️⃣ Prepara lista de itens para o pagamento
    items = [{
        "title": it["titulo"],
        "quantity": it["quantidade"],
        "currency_id": "BRL",
        "unit_price": it["preco"]
    } for it in carrinho_itens]

    # 5️⃣ Detecta se está em ambiente local ou produção
    base_url = request.host_url.rstrip("/")  # ex: http://127.0.0.1:5000
    is_local = "127.0.0.1" in base_url or "localhost" in base_url

    # 🔹 URLs de retorno
    success_url = url_for('pagamento_sucesso', _external=True)
    failure_url = url_for('pagamento_falha', _external=True)
    pending_url = url_for('pagamento_pendente', _external=True)

    # 🔹 Monta o dicionário de preferência
    preference_data = {
        "items": items,
        "payer": {"name": session.get('user_name', 'Cliente')},
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url
        },
        "external_reference": str(user_id)
    }

    # 6️⃣ Ambiente local → remover campos que causam erro (MP não aceita URLs locais)
    if not is_local:
        preference_data["auto_return"] = "approved"
        preference_data["notification_url"] = f"{base_url}/webhooks/mercadopago"

    # 7️⃣ Cria a preferência
    try:
        pref_resp = sdk.preference().create(preference_data)
        pref = pref_resp.get("response", {})
        init_point = pref.get("init_point")

        if not init_point:
            print("❌ Falha MP:", pref_resp)
            return jsonify({"error": "Falha ao criar preferência"}), 500

    except Exception as e:
        print("❌ Erro Mercado Pago:", str(e))
        return jsonify({"error": "Erro ao criar preferência", "detalhe": str(e)}), 500

    # 8️⃣ Limpa o carrinho visual (não remove pedidos no banco)
    clear_current_cart()

    print("✅ Checkout criado com sucesso:", init_point)
    return jsonify({"checkout_url": init_point})


# -----------------------------
# Retornos (Back URLs)
# -----------------------------
@app.route("/pagamento/sucesso")
def pagamento_sucesso():
    # Params possíveis: payment_id / collection_id, status, preference_id, external_reference
    pedido_id = request.args.get("pedido_id", type=int)
    payment_id = request.args.get("payment_id") or request.args.get("collection_id")
    status = request.args.get("status")

    # Confirma com o MP (boa prática)
    if payment_id and pedido_id:
        try:
            sdk = mp_sdk()
            pay = sdk.payment().get(payment_id).get("response", {})
            # Validações mínimas
            ext_ref = str(pay.get("external_reference"))
            status_mp = pay.get("status")
            transaction_amount = float(pay.get("transaction_amount") or 0.0)
            pedido = Order.query.get(pedido_id)

            if pedido and ext_ref == str(pedido.id) and status_mp == "approved" and abs(pedido.total - transaction_amount) < 0.01:
                pedido.status = "Pago"
                db.session.commit()
        except Exception as e:
            # Não quebra a UX; só registra/loga se desejar
            print("Falha ao validar pagamento:", e)

    return render_template("pagamento_sucesso.html", pedido_id=pedido_id, status=status)

@app.route("/pagamento/falha")
def pagamento_falha():
    pedido_id = request.args.get("pedido_id", type=int)
    return render_template("pagamento_falha.html", pedido_id=pedido_id)

@app.route("/pagamento/pendente")
def pagamento_pendente():
    pedido_id = request.args.get("pedido_id", type=int)
    return render_template("pagamento_pendente.html", pedido_id=pedido_id)

# -------------------------------------------------------
# 🌐 WEBHOOK - Retorno automático do Mercado Pago
# -------------------------------------------------------

@app.route("/webhooks/mercadopago", methods=["POST"])
def webhook_mercadopago():
    """
    Webhook para receber notificações automáticas do Mercado Pago.
    Atualiza o status dos pedidos conforme o pagamento é processado.
    """

    data = request.get_json(silent=True)
    print("📩 Webhook recebido:", data)

    if not data:
        return jsonify({"status": "sem_dados"}), 400

    # Verifica se é uma notificação de pagamento
    evento = data.get("type") or data.get("topic")
    if evento != "payment":
        print("⚠️ Evento ignorado:", evento)
        return jsonify({"status": "evento_ignorado"}), 200

    # ID do pagamento
    pagamento_id = data.get("data", {}).get("id")
    if not pagamento_id:
        print("⚠️ Nenhum ID de pagamento encontrado.")
        return jsonify({"status": "sem_id"}), 400

    # Consulta detalhes do pagamento no Mercado Pago
    import mercadopago
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

    try:
        pagamento = sdk.payment().get(pagamento_id)
        info = pagamento.get("response", {})

        status_pagamento = info.get("status")
        referencia = info.get("external_reference")
        valor = info.get("transaction_amount")

        print(f"💰 Pagamento {pagamento_id} recebido | Status: {status_pagamento} | Pedido: {referencia}")

        # Atualiza pedido no banco (referência = user_id ou pedido.id)
        if referencia:
            pedido = Order.query.filter_by(user_id=referencia).order_by(Order.id.desc()).first()
            if pedido:
                pedido.status = (
                    "Pago" if status_pagamento == "approved" else
                    "Pendente" if status_pagamento == "in_process" else
                    "Cancelado"
                )
                db.session.commit()
                print(f"✅ Pedido {pedido.id} atualizado para: {pedido.status}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ Erro no webhook:", str(e))
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Admin: Pedidos
# -----------------------------
@app.route("/admin/pedidos")
@admin_required
def admin_pedidos():
    pedidos = Order.query.order_by(Order.created_at.desc()).all()
    itens_por_pedido = {p.id: OrderItem.query.filter_by(order_id=p.id).count() for p in pedidos}
    return render_template("admin_pedidos.html", pedidos=pedidos, itens_por_pedido=itens_por_pedido)

@app.route("/admin/pedidos/<int:pedido_id>")
@admin_required
def admin_pedido_detalhe(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    itens = OrderItem.query.filter_by(order_id=pedido_id).all()
    user = User.query.get(pedido.user_id)
    detalhe_itens = []
    for it in itens:
        prod = Product.query.get(it.product_id)
        detalhe_itens.append({
            "id": it.id, "produto_id": it.product_id,
            "titulo": prod.titulo if prod else f"#{it.product_id}",
            "preco_unit": it.preco_unitario, "quantidade": it.quantidade,
            "subtotal": it.preco_unitario * it.quantidade,
            "imagem": prod.imagem if prod else ""
        })
    return render_template("admin_pedido_detalhe.html", pedido=pedido, itens=detalhe_itens, user=user)

@app.route("/admin/pedidos/<int:pedido_id>/status", methods=["POST"])
@admin_required
def admin_pedido_status(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    novo_status = request.form.get("status")
    status_validos = ["Pendente", "Pago", "Enviado", "Entregue", "Cancelado"]
    if novo_status not in status_validos:
        return "Status inválido", 400
    pedido.status = novo_status
    db.session.commit()
    return redirect(f"/admin/pedidos/{pedido_id}")

# -----------------------------
# Execução
# -----------------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
