# ============================================
# admin.py — Blueprint de Administração
# ============================================

from flask import Blueprint, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import extract
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Estas variáveis serão injetadas pelo app.py
db = None
User = None
Product = None
Order = None
OrderItem = None
logger = None
email_service = None
UPLOAD_FOLDER = None

def init_admin(database, models_dict, log, email_svc, upload_folder):
    """Inicializa o blueprint com dependências"""
    global db, User, Product, Order, OrderItem, logger, email_service, UPLOAD_FOLDER
    db = database
    User = models_dict['User']
    Product = models_dict['Product']
    Order = models_dict['Order']
    OrderItem = models_dict['OrderItem']
    logger = log
    email_service = email_svc
    UPLOAD_FOLDER = upload_folder


def admin_required(f):
    """Decorator para proteger rotas de admin"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            logger.warning(f"Tentativa de acesso admin sem login - IP: {request.remote_addr}")
            return redirect("/login")
        
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            logger.warning(f"Tentativa de acesso admin negada - User ID: {user_id}")
            return render_template("erro.html", mensagem="Acesso negado: apenas administradores."), 403
        
        return f(*args, **kwargs)
    return decorated


# ============================================
# DASHBOARD ADMIN
# ============================================

@admin_bp.route("")
@admin_required
def admin_dashboard():
    """Dashboard principal do admin com estatísticas"""
    try:
        pedidos = Order.query.all()
        total_pedidos = len(pedidos)
        total_pago = sum(1 for p in pedidos if p.status == "Pago")
        enviados = sum(1 for p in pedidos if p.status == "Enviado")
        entregues = sum(1 for p in pedidos if p.status == "Entregue")
        cancelados = sum(1 for p in pedidos if p.status == "Cancelado")
        faturamento = sum(p.total for p in pedidos if p.status in ["Pago", "Enviado", "Entregue"])
        ticket_medio = (faturamento / total_pago) if total_pago > 0 else 0

        # Gráfico de faturamento dos últimos 6 meses
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
        
        logger.info(f"Admin dashboard acessado - User ID: {session.get('user_id')}")
        
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
    except Exception as e:
        logger.error(f"Erro no dashboard admin: {str(e)}", exc_info=True)
        return render_template("erro.html", mensagem="Erro ao carregar dashboard"), 500


# ============================================
# GESTÃO DE PRODUTOS
# ============================================

@admin_bp.route("/novo", methods=["GET", "POST"])
@admin_required
def admin_novo_produto():
    """Adicionar novo produto"""
    from app.utils import Validator
    
    if request.method == "POST":
        try:
            # Coletar dados do formulário
            data = {
                'titulo': request.form.get("titulo", "").strip(),
                'descricao': request.form.get("descricao", "").strip(),
                'preco': request.form.get("preco"),
                'estoque': request.form.get("estoque", 0)
            }
            
            # Validar dados
            is_valid, errors = Validator.validate_product_data(data)
            if not is_valid:
                logger.warning(f"Tentativa de criar produto com dados inválidos: {errors}")
                return render_template("admin_novo.html", erro="; ".join(errors))
            
            # Processar upload de imagem
            imagem_file = request.files.get("imagem")
            nome_arquivo = None
            if imagem_file and imagem_file.filename:
                nome_arquivo = secure_filename(imagem_file.filename)
                imagem_file.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))
            
            # Criar produto
            p = Product(
                titulo=data['titulo'],
                descricao=data['descricao'],
                preco=float(data['preco']),
                estoque=int(data['estoque']),
                imagem=f"imagens/{nome_arquivo}" if nome_arquivo else ""
            )
            db.session.add(p)
            db.session.commit()
            
            logger.info(f"Produto criado - ID: {p.id} ({p.titulo}) - Admin: {session.get('user_id')}")
            return redirect("/admin")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar produto: {str(e)}", exc_info=True)
            return render_template("admin_novo.html", erro="Erro ao criar produto")
    
    return render_template("admin_novo.html")


@admin_bp.route("/editar/<int:pid>", methods=["GET", "POST"])
@admin_required
def admin_editar_produto(pid):
    """Editar produto existente"""
    from app.utils import Validator
    
    p = Product.query.get_or_404(pid)
    
    if request.method == "POST":
        try:
            # Coletar dados
            data = {
                'titulo': request.form.get("titulo", "").strip(),
                'descricao': request.form.get("descricao", "").strip(),
                'preco': request.form.get("preco"),
                'estoque': request.form.get("estoque", 0)
            }
            
            # Validar
            is_valid, errors = Validator.validate_product_data(data)
            if not is_valid:
                logger.warning(f"Tentativa de editar produto {pid} com dados inválidos: {errors}")
                return render_template("admin_editar.html", produto=p, erro="; ".join(errors))
            
            # Atualizar dados
            p.titulo = data['titulo']
            p.descricao = data['descricao']
            p.preco = float(data['preco'])
            p.estoque = int(data['estoque'])
            
            # Processar nova imagem se enviada
            imagem_file = request.files.get("imagem")
            if imagem_file and imagem_file.filename:
                nome_arquivo = secure_filename(imagem_file.filename)
                imagem_file.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))
                p.imagem = f"imagens/{nome_arquivo}"
            
            db.session.commit()
            
            logger.info(f"Produto editado - ID: {pid} ({p.titulo}) - Admin: {session.get('user_id')}")
            return redirect("/admin")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar produto {pid}: {str(e)}", exc_info=True)
            return render_template("admin_editar.html", produto=p, erro="Erro ao editar produto")
    
    return render_template("admin_editar.html", produto=p)


@admin_bp.route("/remover/<int:pid>")
@admin_required
def admin_remover_produto(pid):
    """Remover produto"""
    try:
        p = Product.query.get_or_404(pid)
        titulo = p.titulo
        
        db.session.delete(p)
        db.session.commit()
        
        logger.info(f"Produto removido - ID: {pid} ({titulo}) - Admin: {session.get('user_id')}")
        return redirect("/admin")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover produto {pid}: {str(e)}", exc_info=True)
        return redirect("/admin")


# ============================================
# GESTÃO DE PEDIDOS
# ============================================

@admin_bp.route("/pedidos")
@admin_required
def admin_pedidos():
    """Lista todos os pedidos"""
    try:
        pedidos = Order.query.order_by(Order.created_at.desc()).all()
        itens_por_pedido = {p.id: OrderItem.query.filter_by(order_id=p.id).count() for p in pedidos}
        
        logger.info(f"Lista de pedidos acessada - Admin: {session.get('user_id')}")
        return render_template("admin_pedidos.html", pedidos=pedidos, itens_por_pedido=itens_por_pedido)
        
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {str(e)}", exc_info=True)
        return render_template("erro.html", mensagem="Erro ao carregar pedidos"), 500


@admin_bp.route("/pedidos/<int:pedido_id>")
@admin_required
def admin_pedido_detalhe(pedido_id):
    """Detalhes de um pedido específico"""
    try:
        pedido = Order.query.get_or_404(pedido_id)
        itens = OrderItem.query.filter_by(order_id=pedido_id).all()
        user = User.query.get(pedido.user_id)
        
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
        
        logger.info(f"Detalhes do pedido {pedido_id} acessado - Admin: {session.get('user_id')}")
        return render_template("admin_pedido_detalhe.html", pedido=pedido, itens=detalhe_itens, user=user)
        
    except Exception as e:
        logger.error(f"Erro ao carregar detalhes do pedido {pedido_id}: {str(e)}", exc_info=True)
        return render_template("erro.html", mensagem="Erro ao carregar pedido"), 500


@admin_bp.route("/pedidos/<int:pedido_id>/status", methods=["POST"])
@admin_required
def admin_pedido_status(pedido_id):
    """Atualizar status de um pedido"""
    try:
        pedido = Order.query.get_or_404(pedido_id)
        old_status = pedido.status
        novo_status = request.form.get("status")
        
        status_validos = ["Pendente", "Pago", "Enviado", "Entregue", "Cancelado"]
        if novo_status not in status_validos:
            logger.warning(f"Tentativa de status inválido: {novo_status}")
            return "Status inválido", 400
        
        pedido.status = novo_status
        db.session.commit()
        
        logger.info(f"Status do pedido {pedido_id} alterado: {old_status} -> {novo_status} - Admin: {session.get('user_id')}")
        
        # Enviar email de atualização se mudou
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
                logger.error(f"Erro ao enviar email de atualização para pedido {pedido_id}: {str(e)}")
        
        return redirect(f"/admin/pedidos/{pedido_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}", exc_info=True)
        return "Erro ao atualizar status", 500
