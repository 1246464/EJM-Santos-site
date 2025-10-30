# api.py
from flask import Blueprint, jsonify, request
from app import db, Product
from werkzeug.security import check_password_hash
import jwt, datetime
from functools import wraps
from flask import current_app as app

api = Blueprint('api', __name__, url_prefix='/api')

# ---------------------------
# Autenticação por token
# ---------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token ausente!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except Exception as e:
            return jsonify({'message': 'Token inválido!', 'erro': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# Endpoints públicos
# ---------------------------
@api.route('/produtos', methods=['GET'])
def listar_produtos():
    produtos = Product.query.all()
    lista = [
        {
            'id': p.id,
            'titulo': p.titulo,
            'descricao': p.descricao,
            'preco': p.preco,
            'imagem': p.imagem
        } for p in produtos
    ]
    return jsonify(lista)

# ---------------------------
# Endpoints protegidos
# ---------------------------
@api.route('/produto', methods=['POST'])
@token_required
def adicionar_produto():
    data = request.get_json()
    novo = Product(
        titulo=data.get('titulo'),
        descricao=data.get('descricao'),
        preco=data.get('preco'),
        imagem=data.get('imagem')
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'message': 'Produto criado com sucesso!'}), 201
