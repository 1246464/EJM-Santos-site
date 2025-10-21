# app.py
import os
import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "ejm.db")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("EJM_SECRET", "troque_esta_chave_por_uma_segura")

db = SQLAlchemy(app)

# -----------------------
# MODELS
# -----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(256))  # path relativo em static/images
    mercado_pago_link = db.Column(db.String(400), nullable=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    nota = db.Column(db.Integer, nullable=False)  # 1..5
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# -----------------------
# AUTH HELPERS
# -----------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"message": "Token ausente"}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({"message": "Usuário não encontrado"}), 401
        except Exception as e:
            return jsonify({"message": "Token inválido", "error": str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# -----------------------
# API Endpoints
# -----------------------
@app.route("/api/reviews/me", methods=["GET"])
@token_required
def api_reviews_me(current_user):
    reviews = (
        db.session.query(Review, Product.titulo)
        .join(Product, Review.product_id == Product.id)
        .filter(Review.user_id == current_user.id)
        .all()
    )
    return jsonify([
        {
            "titulo": titulo,
            "nota": r.nota,
            "comentario": r.comentario
        }
        for r, titulo in reviews
    ])

@app.route("/api/register", methods=["POST"])
def api_register():
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

    # ✅ novo jeito com PyJWT 2.10.1
    #jwt_instance = jwt.JWT()
    #token = jwt_instance.encode(payload, app.config['SECRET_KEY'], alg='HS256')
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "token": token,
        "user": {"id": user.id, "nome": user.nome, "email": user.email}
    })


@app.route("/api/products", methods=["GET"])
def api_products():
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
    p = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=p.id).join(User, Review.user_id==User.id).add_columns(User.nome, Review.nota, Review.comentario, Review.created_at).all()
    revs = []
    for r in reviews:
        revs.append({
            "nome": r.nome,
            "nota": r.nota,
            "comentario": r.comentario,
            "created_at": r.created_at.isoformat()
        })
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
    data = request.json or {}
    product_id = data.get("product_id")
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"message": "Produto não encontrado"}), 404
    purchase = Purchase(user_id=current_user.id, product_id=product_id)
    db.session.add(purchase)
    db.session.commit()
    return jsonify({"message": "Compra simulada registrada — agora você pode avaliar o produto."})

@app.route("/api/review", methods=["POST"])
@token_required
def api_review(current_user):
    data = request.json or {}
    product_id = data.get("product_id")
    nota = data.get("nota")
    comentario = data.get("comentario", "")
    if not (product_id and nota):
        return jsonify({"message": "Product_id e nota necessários"}), 400
    # verifica se o usuário comprou esse produto
    bought = Purchase.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not bought:
        return jsonify({"message": "Você só pode avaliar produtos que comprou."}), 403
    # verifica nota
    try:
        nota_int = int(nota)
        if nota_int < 1 or nota_int > 5:
            raise ValueError()
    except:
        return jsonify({"message": "Nota deve ser inteiro entre 1 e 5"}), 400
    review = Review(user_id=current_user.id, product_id=product_id, nota=nota_int, comentario=comentario)
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Avaliação registrada com sucesso."})

@app.route("/api/me", methods=["GET"])
@token_required
def api_me(current_user):
    purchases = (
        db.session.query(Product.id, Product.titulo)
        .join(Purchase, Purchase.product_id == Product.id)
        .filter(Purchase.user_id == current_user.id)
        .all()
    )
    purchases_list = [{"product_id": pid, "titulo": titulo} for pid, titulo in purchases]

    return jsonify({
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "compras": purchases_list
    })

# -----------------------
# FRONT ROUTES
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/produtos")
def produtos_page():
    return render_template("produtos.html")

@app.route("/produto/<int:product_id>")
def produto_page(product_id):
    return render_template("produto.html", product_id=product_id)

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/perfil")
def perfil_page():
    return render_template("perfil.html")

@app.route("/sobre")
def sobre_page():
    return render_template("sobre.html")

# serve imagens em static/images normalmente (Flask já faz isso se usar /static/images/...)
# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
       db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)

