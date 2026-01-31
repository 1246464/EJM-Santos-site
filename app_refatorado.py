# ============================================
# app_refatorado.py — EJM SANTOS REFATORADO
# Versão modular com blueprints e validações
# ============================================

import os
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
import stripe
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy import extract

# Importar serviço de email
from email_service import email_service

# Importar utilidades
from app.utils import setup_logger, log_request, log_user_action, log_error, Validator, ValidationError

# Importar blueprints
from app.routes import auth_bp, init_auth, admin_bp, init_admin, products_bp, init_products

# ============================================
# CONFIGURAÇÃO
# ============================================
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

# Configuração do Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Configurar upload de imagens
UPLOAD_FOLDER = os.path.join(app.static_folder, "imagens")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ============================================
# LOGGING
# ============================================
logger = setup_logger(app)

# ============================================
# MODELOS
# ============================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pendente", index=True)
    
    endereco_rua = db.Column(db.String(200))
    endereco_numero = db.Column(db.String(20))
    endereco_complemento = db.Column(db.String(100))
    endereco_bairro = db.Column(db.String(100))
    endereco_cidade = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
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


# ============================================
# HELPERS DE AUTENTICAÇÃO
# ============================================
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
            logger.warning(f"Token inválido: {str(e)}")
            return jsonify({"message": "Token inválido", "error": str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# ============================================
# HELPERS DE CARRINHO / PEDIDO
# ============================================
def snapshot_cart_for_checkout():
    """Retorna itens do carrinho para checkout"""
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
    """Esvazia o carrinho"""
    session.pop('cart', None)
    if session.get('user_id'):
        CartItem.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
    logger.info(f"Carrinho limpo - User: {session.get('user_id', 'visitante')}")


def create_order_from_items(user_id, itens):
    """Cria Order + OrderItems"""
    try:
        total = sum(i["preco"] * i["quantidade"] for i in itens)
        pedido = Order(user_id=user_id, total=total, status="Pendente")
        db.session.add(pedido)
        db.session.commit()

        for it in itens:
            db.session.add(OrderItem(
                order_id=pedido.id,
                product_id=it["product_id"],
                quantidade=it["quantidade"],
                preco_unitario=it["preco"]
            ))
        db.session.commit()
        
        logger.info(f"Pedido criado - ID: {pedido.id}, User: {user_id}, Total: R$ {total:.2f}")
        
        # Enviar email de confirmação
        try:
            user = User.query.get(user_id)
            if user:
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
        logger.error(f"Erro ao criar pedido: {str(e)}", exc_info=True)
        raise


# ============================================
# REGISTRAR BLUEPRINTS
# ============================================

# Inicializar auth blueprint
init_auth(db, User, app.config, email_service, logger)
app.register_blueprint(auth_bp)

# Inicializar admin blueprint
models_dict = {
    'User': User,
    'Product': Product,
    'Order': Order,
    'OrderItem': OrderItem
}
init_admin(db, models_dict, logger, email_service, UPLOAD_FOLDER)
app.register_blueprint(admin_bp)

# Inicializar products blueprint
products_models_dict = {
    'Product': Product,
    'Review': Review,
    'User': User,
    'CartItem': CartItem,
    'Order': Order,
    'OrderItem': OrderItem
}
init_products(db, products_models_dict, logger)
app.register_blueprint(products_bp)

logger.info("Blueprints registrados com sucesso")


# ============================================
# ROTAS DE API RESTANTES
# ============================================

@app.route("/api/purchase", methods=["POST"])
@token_required
def api_purchase(current_user):
    """API para registrar compra (legacy)"""
    try:
        data = request.json or {}
        product_id = data.get("product_id")
        p = Product.query.get(product_id)
        if not p:
            return jsonify({"message": "Produto não encontrado"}), 404
        
        existing_order = OrderItem.query.join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product_id
        ).first()
        if existing_order:
            return jsonify({"message": "Compra já registrada."})
        
        order = Order(user_id=current_user.id, status="Pendente", total=p.preco)
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderItem(order_id=order.id, product_id=product_id, quantidade=1, preco_unitario=p.preco))
        db.session.commit()
        
        logger.info(f"Compra registrada via API - User: {current_user.id}, Produto: {product_id}")
        return jsonify({"message": "Compra registrada com sucesso."})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na API de compra: {str(e)}", exc_info=True)
        return jsonify({"message": "Erro ao processar compra"}), 500


@app.route("/api/review", methods=["POST"])
@token_required
def api_review(current_user):
    """API para enviar avaliação"""
    try:
        data = request.json or {}
        product_id = data.get("product_id")
        nota = data.get("nota")
        comentario = data.get("comentario", "")
        
        # Validações
        if not product_id or not nota:
            return jsonify({"message": "product_id e nota são obrigatórios"}), 400
        
        try:
            nota_int = int(nota)
            if nota_int < 1 or nota_int > 5:
                return jsonify({"message": "Nota deve ser entre 1 e 5"}), 400
        except (ValueError, TypeError):
            return jsonify({"message": "Nota inválida"}), 400
        
        # Verificar se produto existe
        p = Product.query.get(product_id)
        if not p:
            return jsonify({"message": "Produto não encontrado"}), 404
        
        # Verificar se já avaliou
        existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            return jsonify({"message": "Você já avaliou este produto"}), 400
        
        # Criar avaliação
        review = Review(
            user_id=current_user.id,
            product_id=product_id,
            nota=nota_int,
            comentario=Validator.sanitize_string(comentario, 1000)
        )
        db.session.add(review)
        db.session.commit()
        
        logger.info(f"Avaliação criada - User: {current_user.id}, Produto: {product_id}, Nota: {nota_int}")
        return jsonify({"message": "Avaliação enviada com sucesso!"})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar avaliação: {str(e)}", exc_info=True)
        return jsonify({"message": "Erro ao enviar avaliação"}), 500


@app.route("/api/me")
@token_required
def api_me(current_user):
    """API para obter dados do usuário atual"""
    pedidos = Order.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "total_pedidos": len(pedidos)
    })


@app.route("/api/reviews/me")
@token_required
def api_reviews_me(current_user):
    """API para obter avaliações do usuário"""
    reviews = (
        Review.query.filter_by(user_id=current_user.id)
        .join(Product, Review.product_id == Product.id)
        .add_columns(Product.titulo, Review.nota, Review.comentario, Review.created_at)
        .all()
    )
    data = [{
        "produto": r.titulo,
        "nota": r.nota,
        "comentario": r.comentario,
        "data": r.created_at.isoformat()
    } for r in reviews]
    return jsonify(data)


# ============================================
# CHECKOUT E PAGAMENTO
# ============================================

@app.route("/finalizar-compra")
def finalizar_compra():
    """Página de finalização de compra (redirect para checkout)"""
    if not session.get("user_id"):
        return redirect("/login")
    return redirect("/checkout")


@app.route("/checkout")
def checkout():
    """Página de checkout"""
    if not session.get("user_id"):
        return redirect("/login")
    
    itens = snapshot_cart_for_checkout()
    if not itens:
        return redirect("/carrinho")
    
    total = sum(i["preco"] * i["quantidade"] for i in itens)
    logger.info(f"Checkout iniciado - User: {session.get('user_id')}, Total: R$ {total:.2f}")
    
    return render_template("checkout.html", itens=itens, total=total, stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route('/processar-pagamento', methods=['POST'])
def processar_pagamento():
    """Processa pagamento com Stripe"""
    try:
        if not session.get("user_id"):
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Obter dados do formulário
        payment_method_id = request.json.get('payment_method_id')
        endereco_data = request.json.get('endereco', {})
        
        # Validar endereço
        is_valid, errors = Validator.validate_address(endereco_data)
        if not is_valid:
            logger.warning(f"Dados de endereço inválidos: {errors}")
            return jsonify({"error": "Dados de endereço inválidos", "details": errors}), 400
        
        # Obter itens do carrinho
        itens = snapshot_cart_for_checkout()
        if not itens:
            return jsonify({"error": "Carrinho vazio"}), 400
        
        total = sum(i["preco"] * i["quantidade"] for i in itens)
        total_centavos = int(total * 100)
        
        # Criar Payment Intent no Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=total_centavos,
            currency='brl',
            payment_method=payment_method_id,
            confirm=True,
            description=f'Pedido EJM Santos - User {user_id}',
            metadata={
                'user_id': user_id,
                'user_email': user.email
            },
            return_url=request.host_url + 'pagamento/sucesso'
        )
        
        # Criar pedido no banco
        pedido = create_order_from_items(user_id, itens)
        
        # Adicionar endereço ao pedido
        pedido.endereco_rua = Validator.sanitize_string(endereco_data.get('endereco_rua'), 200)
        pedido.endereco_numero = Validator.sanitize_string(endereco_data.get('endereco_numero'), 20)
        pedido.endereco_complemento = Validator.sanitize_string(endereco_data.get('endereco_complemento', ''), 100)
        pedido.endereco_bairro = Validator.sanitize_string(endereco_data.get('endereco_bairro'), 100)
        pedido.endereco_cidade = Validator.sanitize_string(endereco_data.get('endereco_cidade'), 100)
        pedido.telefone = Validator.sanitize_string(endereco_data.get('telefone', ''), 20)
        pedido.status = "Pago"
        db.session.commit()
        
        # Atualizar estoque
        for item in itens:
            produto = Product.query.get(item['product_id'])
            if produto:
                produto.estoque -= item['quantidade']
        db.session.commit()
        
        # Limpar carrinho
        clear_current_cart()
        
        logger.info(f"Pagamento processado com sucesso - Pedido: {pedido.id}, Total: R$ {total:.2f}")
        
        return jsonify({
            "success": True,
            "order_id": pedido.id,
            "payment_intent_id": payment_intent.id
        })
        
    except stripe.error.CardError as e:
        logger.warning(f"Erro no cartão: {str(e)}")
        return jsonify({"error": f"Erro no cartão: {e.user_message}"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar pagamento: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao processar pagamento"}), 500


@app.route("/pagamento/sucesso")
def pagamento_sucesso():
    """Página de sucesso do pagamento"""
    return render_template("pagamento_sucesso.html")


@app.route("/pagamento/falha")
def pagamento_falha():
    """Página de falha do pagamento"""
    return render_template("pagamento_falha.html")


@app.route("/pedido/<int:id>")
def ver_pedido(id):
    """Página de detalhes do pedido"""
    if not session.get("user_id"):
        return redirect("/login")
    
    user_id = session['user_id']
    pedido = Order.query.filter_by(id=id, user_id=user_id).first_or_404()
    itens = OrderItem.query.filter_by(order_id=id).all()
    
    detalhe_itens = []
    for it in itens:
        prod = Product.query.get(it.product_id)
        detalhe_itens.append({
            "titulo": prod.titulo if prod else f"Produto #{it.product_id}",
            "quantidade": it.quantidade,
            "preco_unit": it.preco_unitario,
            "subtotal": it.preco_unitario * it.quantidade,
            "imagem": prod.imagem if prod else ""
        })
    
    return render_template("pedido_detalhe.html", pedido=pedido, itens=detalhe_itens)


# ============================================
# MIDDLEWARE
# ============================================

@app.after_request
def add_header(response):
    """Evita cache de páginas"""
    response.headers["Cache-Control"] = "no-store"
    return response


@app.before_request
def log_requests():
    """Loga todas as requisições"""
    if not request.path.startswith('/static'):
        logger.debug(f"{request.method} {request.path} - IP: {request.remote_addr}")


# ============================================
# TRATAMENTO DE ERROS
# ============================================

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 - {request.path}")
    return render_template("erro.html", mensagem="Página não encontrada"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 - {str(e)}", exc_info=True)
    return render_template("erro.html", mensagem="Erro interno do servidor"), 500


# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
        logger.info("Banco de dados inicializado")
    app.run(host="0.0.0.0", port=5000, debug=True)
