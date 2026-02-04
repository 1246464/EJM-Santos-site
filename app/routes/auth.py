# ============================================
# auth.py — Blueprint de Autenticação
# ============================================

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import re

auth_bp = Blueprint('auth', __name__)

# Estas variáveis serão injetadas pelo app.py
db = None
User = None
app_config = None
email_service = None
logger = None
limiter = None

def init_auth(database, user_model, config, email_svc, log, rate_limiter=None):
    """Inicializa o blueprint com dependências"""
    global db, User, app_config, email_service, logger, limiter
    db = database
    User = user_model
    app_config = config
    email_service = email_svc
    logger = log
    limiter = rate_limiter


# ============================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida senha forte: mín 8 chars, 1 maiúscula, 1 minúscula, 1 número"""
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter ao menos 1 letra maiúscula"
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter ao menos 1 letra minúscula"
    if not re.search(r'[0-9]', password):
        return False, "Senha deve conter ao menos 1 número"
    return True, "OK"


# ============================================
# ROTAS DE PÁGINA (HTML)
# ============================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """Página de login de usuários"""
    # Aplicar rate limit se disponível
    if limiter:
        limiter.limit("10 per minute")(login_page)
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        # Validação de entrada
        if not email or not senha:
            logger.warning(f"Login sem credenciais - IP: {request.remote_addr}")
            return render_template("login.html", erro="Preencha todos os campos."), 400
        
        if not validate_email(email):
            logger.warning(f"Login com email inválido: {email} - IP: {request.remote_addr}")
            return render_template("login.html", erro="Email inválido."), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.senha_hash, senha):
            # Login bem-sucedido
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = user.is_admin
            session.permanent = True  # Usar PERMANENT_SESSION_LIFETIME
            
            logger.info(f"✅ Login - User: {user.id} ({user.email}) - IP: {request.remote_addr}")
            return redirect("/")
        
        # Credenciais inválidas (mesma mensagem para não revelar se email existe)
        logger.warning(f"❌ Login falhou: {email} - IP: {request.remote_addr}")
        return render_template("login.html", erro="Email ou senha inválidos."), 401
    
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
    # Aplicar rate limit se disponível
    if limiter:
        limiter.limit("5 per minute")(admin_login)
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        # Validação
        if not email or not senha:
            logger.warning(f"Admin login sem credenciais - IP: {request.remote_addr}")
            return render_template("admin_login.html", erro="Preencha todos os campos."), 400
        
        if not validate_email(email):
            logger.warning(f"Admin login email inválido: {email} - IP: {request.remote_addr}")
            return render_template("admin_login.html", erro="Email inválido."), 400
        
        # Buscar usuário admin
        user = User.query.filter_by(email=email, is_admin=True).first()
        
        if user and check_password_hash(user.senha_hash, senha):
            session["user_id"] = user.id
            session["user_name"] = user.nome
            session["is_admin"] = True
            session.permanent = True
            
            logger.info(f"✅ Admin login - User: {user.id} ({user.email}) - IP: {request.remote_addr}")
            return redirect("/admin")
        
        logger.warning(f"❌ Admin login falhou: {email} - IP: {request.remote_addr}")
        return render_template("admin_login.html", erro="Credenciais de administrador inválidas."), 401
    
    return render_template("admin_login.html")


# ============================================
# API DE AUTENTICAÇÃO (JSON)
# ============================================

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    """API para cadastro de novos usuários"""
    # Aplicar rate limit se disponível
    if limiter:
        limiter.limit("3 per hour")(api_register)
    
    data = request.json or {}
    
    # Validar campos obrigatórios
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip().lower()
    senha = data.get("senha", "")
    
    if not nome or not email or not senha:
        logger.warning(f"Cadastro incompleto - IP: {request.remote_addr}")
        return jsonify({"message": "Todos os campos são obrigatórios"}), 400
    
    # Validar email
    if not validate_email(email):
        logger.warning(f"Cadastro email inválido: {email} - IP: {request.remote_addr}")
        return jsonify({"message": "Email inválido"}), 400
    
    # Validar senha forte
    is_valid, msg = validate_password(senha)
    if not is_valid:
        logger.warning(f"Cadastro senha fraca - IP: {request.remote_addr}")
        return jsonify({"message": msg}), 400
    
    # Validar nome (sem caracteres especiais perigosos)
    if len(nome) < 3 or len(nome) > 120:
        return jsonify({"message": "Nome deve ter entre 3 e 120 caracteres"}), 400
    if re.search(r'[<>{}]', nome):
        return jsonify({"message": "Nome contém caracteres inválidos"}), 400
    
    # Verificar se email já existe
    if User.query.filter_by(email=email).first():
        logger.warning(f"❌ Cadastro email duplicado: {email} - IP: {request.remote_addr}")
        return jsonify({"message": "Email já cadastrado"}), 409
    
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
