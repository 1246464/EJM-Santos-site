# ============================================
# app.py — EJM SANTOS - Loja de Mel Natural 🍯
# ============================================

import os
import datetime
from functools import wraps
from flask import (
    Flask, request, jsonify, render_template,
    session, redirect
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

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
class User(db.Model):
    """Usuário do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # 🧩 novo campo
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Review(db.Model):
    """Avaliações dos produtos"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    nota = db.Column(db.Integer, nullable=False)  # de 1 a 5
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
            session["is_admin"] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", erro="Credenciais inválidas ou sem permissão.")
    return render_template("admin_login.html")

@app.route("/admin")
@admin_required
def admin_dashboard():
    """Painel de controle do administrador"""
    produtos = Product.query.all()
    return render_template("admin_dashboard.html", produtos=produtos)


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


# -------------------------------------------------------
# EXECUÇÃO DO APP
# -------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
