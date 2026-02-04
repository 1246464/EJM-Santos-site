# ============================================
# app.py — EJM SANTOS - Loja de Mel Natural 🍯
# Versão consolidada, documentada e pronta p/ Checkout Pro
# ============================================

import os
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
import stripe
from flask import (
    Flask, request, jsonify, render_template,
    session, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy import extract

# Importar serviço de email
from email_service import email_service

# Importar utils de tratamento de erros e logging
from app.utils.logger import setup_logger
from app.utils.error_handlers import register_error_handlers
from app.utils import exceptions

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
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

db = SQLAlchemy(app)

# Configurar logging
logger = setup_logger(app)
logger.info("="*50)
logger.info("🍯 Iniciando EJM Santos - Loja de Mel Natural")
logger.info("="*50)

# Registrar error handlers
register_error_handlers(app, logger)

# Configuração do Stripe
try:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    if not stripe.api_key:
        logger.warning("⚠️ STRIPE_SECRET_KEY não configurada")
    else:
        logger.info("✅ Stripe configurado com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao configurar Stripe: {e}")
    STRIPE_PUBLIC_KEY = None

# -----------------------------
# MODELOS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(256))
    estoque = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pendente", index=True)  # Pendente, Pago, Enviado, Entregue, Cancelado
    
    # Endereço de entrega (entrega local)
    endereco_rua = db.Column(db.String(200))
    endereco_numero = db.Column(db.String(20))
    endereco_complemento = db.Column(db.String(100))
    endereco_bairro = db.Column(db.String(100))
    endereco_cidade = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    comentario = db.Column(db.Text)
    nota = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)

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
    try:
        if not itens:
            raise ValueError("Carrinho vazio")
        
        if not user_id:
            raise ValueError("Usuário não identificado")
        
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
        
        logger.info(f"Pedido criado - ID: {pedido.id} - User: {user_id} - Total: R$ {total:.2f}")
        
        # Enviar email de confirmação de pedido
        try:
            user = User.query.get(user_id)
            if user:
                # Preparar dados dos itens para o email
                order_items_data = []
                for it in itens:
                    order_items_data.append({
                        'titulo': it.get('titulo', 'Produto'),
                        'quantidade': it['quantidade'],
                        'preco': it['preco'] * it['quantidade']
                    })
                
                email_service.send_order_confirmation(
                    user_name=user.nome,
                    user_email=user.email,
                    order_id=pedido.id,
                    order_items=order_items_data,
                    total=total
                )
        except Exception as e:
            logger.error(f"Erro ao enviar email de confirmação do pedido {pedido.id}: {str(e)}")
        
        return pedido
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar pedido para user {user_id}: {str(e)}", exc_info=True)
        raise

# -----------------------------
# ROTAS: Login / Logout / Admin
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        try:
            email = request.form.get("email", "").strip()
            senha = request.form.get("senha", "")
            
            if not (email and senha):
                logger.warning(f"Tentativa de login sem credenciais - IP: {request.remote_addr}")
                return render_template("login.html", erro="Preencha todos os campos.")
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.senha_hash, senha):
                session["user_id"] = user.id
                session["user_name"] = user.nome
                session["is_admin"] = user.is_admin
                logger.info(f"Login bem-sucedido - User ID: {user.id} ({email})")
                return redirect("/")
            
            logger.warning(f"Login falhou para: {email} - IP: {request.remote_addr}")
            return render_template("login.html", erro="Credenciais inválidas.")
        
        except Exception as e:
            logger.error(f"Erro durante login: {str(e)}", exc_info=True)
            return render_template("login.html", erro="Erro ao processar login. Tente novamente.")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        logger.info(f"Logout - User ID: {user_id}")
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
    try:
        data = request.json or {}
        nome, email, senha = data.get("nome"), data.get("email"), data.get("senha")
        
        if not (nome and email and senha):
            logger.warning(f"Cadastro API com campos faltando - IP: {request.remote_addr}")
            return jsonify({"message": "Campos obrigatórios: nome, email, senha"}), 400
        
        # Validar email
        email = email.strip().lower()
        if "@" not in email:
            return jsonify({"message": "Email inválido"}), 400
        
        if User.query.filter_by(email=email).first():
            logger.warning(f"Tentativa de cadastro com email existente: {email}")
            return jsonify({"message": "Email já cadastrado"}), 400
        
        user = User(nome=nome, email=email, senha_hash=generate_password_hash(senha))
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"Novo usuário cadastrado - ID: {user.id} ({email})")
        
        # Enviar email de boas-vindas
        try:
            email_service.send_welcome_email(nome, email)
        except Exception as e:
            logger.error(f"Erro ao enviar email de boas-vindas para {email}: {str(e)}")
        
        return jsonify({"message": "Cadastro realizado com sucesso"}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no cadastro API: {str(e)}", exc_info=True)
        return jsonify({"message": "Erro ao realizar cadastro"}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.json or {}
        email, senha = data.get("email"), data.get("senha")
        
        if not (email and senha):
            logger.warning(f"Login API sem credenciais - IP: {request.remote_addr}")
            return jsonify({"message": "Email e senha necessários"}), 400
        
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.senha_hash, senha):
            logger.warning(f"Login API falhou para: {email} - IP: {request.remote_addr}")
            return jsonify({"message": "Credenciais inválidas"}), 401
        
        payload = {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)}
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        
        logger.info(f"Login API bem-sucedido - User ID: {user.id} ({email})")
        
        return jsonify({
            "token": token, 
            "user": {"id": user.id, "nome": user.nome, "email": user.email}
        })
    
    except Exception as e:
        logger.error(f"Erro no login API: {str(e)}", exc_info=True)
        return jsonify({"message": "Erro ao processar login"}), 500

@app.route("/api/products")
def api_products():
    prods = Product.query.all()
    data = []
    for p in prods:
        avg = db.session.query(db.func.avg(Review.nota)).filter(Review.product_id == p.id).scalar() or 0
        count = Review.query.filter_by(product_id=p.id).count()
        # Remove 'imagens/' do início se existir
        imagem = p.imagem.replace('imagens/', '') if p.imagem and p.imagem.startswith('imagens/') else p.imagem
        data.append({
            "id": p.id, "titulo": p.titulo, "descricao": p.descricao, "preco": p.preco,
            "imagem": imagem, "estoque": p.estoque,
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
    return jsonify({"id": p.id, "titulo": p.titulo, "descricao": p.descricao, "preco": p.preco, "imagem": p.imagem, "reviews": revs})

@app.route("/api/purchase", methods=["POST"])
@token_required
def api_purchase(current_user):
    data = request.json or {}
    product_id = data.get("product_id")
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"message": "Produto não encontrado"}), 404
    # Verificar se já comprou este produto
    existing_order = OrderItem.query.join(Order).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id
    ).first()
    if existing_order:
        return jsonify({"message": "Compra já registrada."})
    # Criar novo pedido
    order = Order(user_id=current_user.id, status="Pendente")
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product_id, quantidade=1, preco_unitario=p.preco))
    db.session.commit()
    return jsonify({"message": "Compra registrada com sucesso."})

@app.route("/api/review", methods=["POST"])
@token_required
def api_review(current_user):
    data = request.json or {}
    product_id, nota, comentario = data.get("product_id"), data.get("nota"), data.get("comentario", "")
    if not (product_id and nota):
        return jsonify({"message": "product_id e nota são obrigatórios"}), 400
    # Verificar se o usuário comprou este produto
    purchased = OrderItem.query.join(Order).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id
    ).first()
    if not purchased:
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
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == current_user.id)
        .distinct()
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

@app.route("/api/products/search")
def api_products_search():
    """Busca e filtra produtos com parâmetros de query"""
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
        # Remove 'imagens/' do início se existir
        imagem = p.imagem.replace('imagens/', '') if p.imagem and p.imagem.startswith('imagens/') else (p.imagem or '')
        data.append({
            "id": p.id, "titulo": p.titulo, "descricao": p.descricao,
            "preco": p.preco, "imagem": imagem,
            "estoque": p.estoque,
            "media": round(float(avg), 2), "n_reviews": count
        })
    return jsonify(data)

from flask import session, jsonify

@app.route("/api/carrinho")
def api_carrinho():
    """Retorna o conteúdo atual do carrinho (sessão ou banco)"""
    if 'user_id' in session:
        # Se o usuário estiver logado, puxa do banco
        user_id = session['user_id']
        itens = CartItem.query.filter_by(user_id=user_id).all()
        return jsonify({
            "itens": [
                {"produto_id": i.product_id, "quantidade": i.quantity}
                for i in itens
            ]
        })

    # Caso contrário, usa o carrinho salvo na sessão
    carrinho = session.get("cart", {})
    itens = [{"produto_id": int(k), "quantidade": v} for k, v in carrinho.items()]
    return jsonify({"itens": itens})

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
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Buscar todos os pedidos do usuário
    pedidos = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return render_template("perfil_novo.html", pedidos=pedidos, user=user)

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
        estoque = request.form.get("estoque", 0)
        imagem_file = request.files.get("imagem")
        nome_arquivo = None
        if imagem_file and imagem_file.filename:
            nome_arquivo = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))
        p = Product(
            titulo=titulo, descricao=descricao, preco=float(preco or 0),
            estoque=int(estoque),
            imagem=f"imagens/{nome_arquivo}" if nome_arquivo else ""
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
        p.estoque = int(request.form.get("estoque", 0))
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
    try:
        produto = Product.query.get(id)
        if not produto:
            logger.warning(f"Tentativa de adicionar produto inexistente ao carrinho: {id}")
            return "Produto não encontrado", 404

        # Verifica estoque disponível
        if produto.estoque <= 0:
            logger.warning(f"Tentativa de adicionar produto esgotado: {id}")
            return "Produto esgotado", 400

        if 'user_id' in session:
            user_id = session['user_id']
            item = CartItem.query.filter_by(user_id=user_id, product_id=id).first()
            
            # Verifica se já tem no carrinho e valida estoque
            quantidade_atual = item.quantity if item else 0
            if quantidade_atual + 1 > produto.estoque:
                logger.warning(f"Estoque insuficiente para produto {id} - User: {user_id}")
                return "Estoque insuficiente", 400
            
            if item:
                item.quantity += 1
            else:
                db.session.add(CartItem(user_id=user_id, product_id=id, quantity=1))
            
            db.session.commit()
            logger.info(f"Produto {id} adicionado ao carrinho (DB) - User: {user_id}")
            return "OK (db)", 200

        carrinho = session.get('cart', {})
        quantidade_atual = carrinho.get(str(id), 0)
        
        # Valida estoque para carrinho de sessão
        if quantidade_atual + 1 > produto.estoque:
            logger.warning(f"Estoque insuficiente para produto {id} (sessão)")
            return "Estoque insuficiente", 400
        
        carrinho[str(id)] = quantidade_atual + 1
        session['cart'] = carrinho
        session.modified = True
        logger.info(f"Produto {id} adicionado ao carrinho (sessão)")
        return "OK (sessão)", 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar produto {id} ao carrinho: {str(e)}", exc_info=True)
        return "Erro ao adicionar ao carrinho", 500

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
# CHECKOUT — Stripe Payment
# -----------------------------
@app.route('/checkout')
def checkout():
    """
    Exibe a página de checkout com formulário de cartão
    """
    user_id = session.get('user_id')
    if not user_id:
        session['redirect_after_login'] = "/checkout"
        return redirect("/login")

    carrinho_itens = snapshot_cart_for_checkout()
    if not carrinho_itens:
        return redirect("/carrinho")

    total = sum(it["preco"] * it["quantidade"] for it in carrinho_itens)
    
    return render_template("checkout.html", 
                         itens=carrinho_itens, 
                         total=total,
                         stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/processar-pagamento', methods=['POST'])
def processar_pagamento():
    """
    Processa o pagamento com Stripe usando os dados do cartão
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            logger.warning(f"Tentativa de pagamento sem login - IP: {request.remote_addr}")
            return jsonify({"error": "Usuário não logado"}), 401

        # Captura dados do formulário
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400
        
        payment_method_id = data.get('payment_method_id')
        endereco = data.get('endereco', {})
        
        if not payment_method_id:
            logger.warning(f"Pagamento sem método - User: {user_id}")
            return jsonify({"error": "Método de pagamento inválido"}), 400
        
        # Valida endereço
        if not all([endereco.get('rua'), endereco.get('numero'), endereco.get('bairro'), 
                    endereco.get('cidade'), endereco.get('telefone')]):
            logger.warning(f"Endereço incompleto no pagamento - User: {user_id}")
            return jsonify({"error": "Endereço de entrega incompleto"}), 400

        # Pega itens do carrinho
        carrinho_itens = snapshot_cart_for_checkout()
        if not carrinho_itens:
            logger.warning(f"Tentativa de pagamento com carrinho vazio - User: {user_id}")
            return jsonify({"error": "Carrinho vazio"}), 400

        # Calcula total (em centavos para Stripe)
        total = sum(it["preco"] * it["quantidade"] for it in carrinho_itens)
        total_centavos = int(total * 100)

        try:
            # Cria o PaymentIntent no Stripe
            intent = stripe.PaymentIntent.create(
                amount=total_centavos,
                currency="brl",
                payment_method=payment_method_id,
                confirm=True,
                description=f"Pedido EJM Santos - Usuario #{user_id}",
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                }
            )

            # Se o pagamento foi aprovado
            if intent['status'] == 'succeeded':
                # Desconta estoque dos produtos
                for item in carrinho_itens:
                    produto = Product.query.get(item["product_id"])
                    if produto:
                        produto.estoque -= item["quantidade"]
                        if produto.estoque < 0:
                            produto.estoque = 0
                
                # Cria o pedido no banco com endereço
                pedido = create_order_from_items(user_id, carrinho_itens)
                pedido.status = "Pago"
                pedido.endereco_rua = endereco.get('rua')
                pedido.endereco_numero = endereco.get('numero')
                pedido.endereco_complemento = endereco.get('complemento', '')
                pedido.endereco_bairro = endereco.get('bairro')
                pedido.endereco_cidade = endereco.get('cidade')
                pedido.telefone = endereco.get('telefone')
                db.session.commit()

                # Limpa o carrinho
                clear_current_cart()
                
                logger.info(f"✅ Pagamento aprovado - Pedido {pedido.id} - User: {user_id} - Total: R$ {total:.2f}")

                return jsonify({
                    "success": True,
                    "pedido_id": pedido.id,
                    "message": "Pagamento realizado com sucesso!"
                })
            else:
                logger.warning(f"Pagamento não aprovado - User: {user_id} - Status: {intent['status']}")
                return jsonify({"error": "Pagamento não aprovado"}), 400

        except stripe.error.CardError as e:
            # Erro no cartão
            logger.warning(f"Erro de cartão - User: {user_id}: {e.user_message}")
            return jsonify({"error": f"Erro no cartão: {e.user_message}"}), 400
        except stripe.error.StripeError as e:
            # Erro do Stripe
            logger.error(f"Erro do Stripe - User: {user_id}: {str(e)}")
            return jsonify({"error": f"Erro ao processar pagamento: {str(e)}"}), 500
    
    except Exception as e:
        # Erro geral
        db.session.rollback()
        logger.error(f"Erro inesperado no pagamento - User: {session.get('user_id')}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500


# -----------------------------
# Retornos de Pagamento
# -----------------------------
@app.route("/pagamento/sucesso")
def pagamento_sucesso():
    pedido_id = request.args.get("pedido_id", type=int)
    return render_template("pagamento_sucesso.html", pedido_id=pedido_id)

@app.route("/pagamento/falha")
def pagamento_falha():
    return render_template("pagamento_falha.html")

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
    old_status = pedido.status
    novo_status = request.form.get("status")
    status_validos = ["Pendente", "Pago", "Enviado", "Entregue", "Cancelado"]
    if novo_status not in status_validos:
        return "Status inválido", 400
    
    pedido.status = novo_status
    db.session.commit()
    
    # Enviar email de atualização de status se mudou
    if old_status != novo_status:
        try:
            user = User.query.get(pedido.user_id)
            if user:
                email_service.send_order_status_update(
                    user_name=user.nome,
                    user_email=user.email,
                    order_id=pedido.id,
                    old_status=old_status,
                    new_status=novo_status
                )
        except Exception as e:
            print(f"⚠️ Erro ao enviar email de atualização: {e}")
    
    return redirect(f"/admin/pedidos/{pedido_id}")

# -----------------------------
# Execução
# -----------------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
