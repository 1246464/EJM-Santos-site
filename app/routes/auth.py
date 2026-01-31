# ============================================
# auth.py — Blueprint de Autenticação
# ============================================

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt

auth_bp = Blueprint('auth', __name__)

# Estas variáveis serão injetadas pelo app.py
db = None
User = None
app_config = None
email_service = None
logger = None

def init_auth(database, user_model, config, email_svc, log):
    """Inicializa o blueprint com dependências"""
    global db, User, app_config, email_service, logger
    db = database
    User = user_model
    app_config = config
    email_service = email_svc
    logger = log


# ============================================
# ROTAS DE PÁGINA (HTML)
# ============================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """Página de login de usuários"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        
        # Validação básica
        if not email or not senha:
            logger.warning(f"Tentativa de login sem credenciais - IP: {request.remote_addr}")
            return render_template("login.html", erro="Preencha todos os campos.")
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.senha_hash, senha):
            # Login bem-sucedido
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            
            logger.info(f"Login bem-sucedido - User ID: {user.id} ({user.email})")
            return redirect("/")
        
        # Credenciais inválidas
        logger.warning(f"Tentativa de login falhou para email: {email} - IP: {request.remote_addr}")
        return render_template("login.html", erro="Credenciais inválidas.")
    
    # GET request
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Faz logout do usuário"""
    user_id = session.get("user_id")
    if user_id:
        logger.info(f"Logout - User ID: {user_id}")
    
    session.clear()
    return redirect("/")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Página de login de administradores"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.senha_hash, senha) and user.is_admin:
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            
            logger.info(f"Login admin bem-sucedido - User ID: {user.id} ({user.email})")
            return redirect("/admin")
        
        logger.warning(f"Tentativa de login admin falhou para: {email} - IP: {request.remote_addr}")
        return render_template("admin_login.html", erro="Credenciais inválidas ou sem permissão.")
    
    return render_template("admin_login.html")


# ============================================
# API DE AUTENTICAÇÃO (JSON)
# ============================================

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    """API para cadastro de novos usuários"""
    from app.utils import Validator
    
    data = request.json or {}
    
    # Validar dados de entrada
    is_valid, errors = Validator.validate_user_registration(data)
    if not is_valid:
        logger.warning(f"Tentativa de cadastro com dados inválidos: {errors}")
        return jsonify({"message": "Dados inválidos", "errors": errors}), 400
    
    nome = Validator.sanitize_string(data.get("nome"), 120)
    email = data.get("email").strip().lower()
    senha = data.get("senha")
    
    # Verificar se email já existe
    if User.query.filter_by(email=email).first():
        logger.warning(f"Tentativa de cadastro com email já existente: {email}")
        return jsonify({"message": "Email já cadastrado"}), 400
    
    try:
        # Criar novo usuário
        user = User(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha)
        )
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
        logger.error(f"Erro ao cadastrar usuário: {str(e)}", exc_info=True)
        return jsonify({"message": "Erro ao realizar cadastro"}), 500


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """API para login (retorna JWT token)"""
    from app.utils import Validator
    
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    senha = data.get("senha", "")
    
    # Validação básica
    if not email or not senha:
        logger.warning(f"Tentativa de login API sem credenciais - IP: {request.remote_addr}")
        return jsonify({"message": "Email e senha necessários"}), 400
    
    # Validar formato do email
    is_valid, msg = Validator.validate_email(email)
    if not is_valid:
        return jsonify({"message": msg}), 400
    
    # Buscar usuário
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.senha_hash, senha):
        logger.warning(f"Tentativa de login API falhou para: {email} - IP: {request.remote_addr}")
        return jsonify({"message": "Credenciais inválidas"}), 401
    
    # Gerar JWT token
    payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, app_config["SECRET_KEY"], algorithm="HS256")
    
    logger.info(f"Login API bem-sucedido - User ID: {user.id} ({email})")
    
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "is_admin": user.is_admin
        }
    })
