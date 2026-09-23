# ============================================
# admin.py — Blueprint de Administração
# ============================================

from flask import Blueprint, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import extract
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Estas variáveis serão injetadas pelo app.py
db = None
User = None
Product = None
Order = None
OrderItem = None
Supplier = None
Brand = None
FulfillmentOrigin = None
ProductInventory = None
DeliverySettings = None
logger = None
email_service = None
UPLOAD_FOLDER = None

def init_admin(database, models_dict, log, email_svc, upload_folder):
    """Inicializa o blueprint com dependências"""
    global db, User, Product, Order, OrderItem, logger, email_service, UPLOAD_FOLDER
    global Supplier, Brand, FulfillmentOrigin, ProductInventory, DeliverySettings
    db = database
    User = models_dict['User']
    Product = models_dict['Product']
    Order = models_dict['Order']
    OrderItem = models_dict['OrderItem']
    Supplier = models_dict['Supplier']
    Brand = models_dict['Brand']
    FulfillmentOrigin = models_dict['FulfillmentOrigin']
    ProductInventory = models_dict['ProductInventory']
    DeliverySettings = models_dict['DeliverySettings']
    logger = log
    email_service = email_svc
    UPLOAD_FOLDER = upload_folder


def _optional_int(value):
    try:
        return int(value) if str(value or "").strip() else None
    except (TypeError, ValueError):
        return None


def _optional_float(value, field_name, allow_negative=False):
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} deve ser um número") from exc
    if parsed < 0 and not allow_negative:
        raise ValueError(f"{field_name} não pode ser negativo")
    return parsed


def _coordinate(value, field_name, minimum, maximum):
    parsed = _optional_float(value, field_name, allow_negative=True)
    if parsed is not None and not minimum <= parsed <= maximum:
        raise ValueError(f"{field_name} deve ficar entre {minimum} e {maximum}")
    return parsed


def _existing_id(model, value, field_name):
    identifier = _optional_int(value)
    if identifier is not None and db.session.get(model, identifier) is None:
        raise ValueError(f"{field_name} selecionado não existe")
    return identifier


def _safe_form_error(error, fallback):
    return str(error) if isinstance(error, ValueError) else fallback


def _product_form_context(**extra):
    context = {
        "supplier_options": Supplier.query.filter_by(active=True).order_by(
            Supplier.trade_name
        ).all(),
        "brand_options": Brand.query.filter_by(active=True).order_by(Brand.name).all(),
        "origin_options": FulfillmentOrigin.query.filter_by(active=True).order_by(
            FulfillmentOrigin.name
        ).all(),
    }
    context.update(extra)
    return context


def _sync_primary_inventory(product):
    if not product.fulfillment_origin_id:
        return
    inventories = ProductInventory.query.filter_by(
        product_id=product.id, active=True
    ).all()
    inventory = next(
        (
            row
            for row in inventories
            if row.origin_id == product.fulfillment_origin_id
        ),
        None,
    )
    if len(inventories) <= 1:
        if inventory is None and inventories:
            inventory = inventories[0]
            inventory.origin_id = product.fulfillment_origin_id
        elif inventory is None:
            inventory = ProductInventory(
                product_id=product.id,
                origin_id=product.fulfillment_origin_id,
            )
            db.session.add(inventory)
        inventory.quantity = product.estoque or 0
        inventory.active = True
        return

    # Com várias origens, o estoque total é administrado na tela de logística.
    product.estoque = sum(row.quantity or 0 for row in inventories)


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
        status_com_receita = {"Pago", "Agendado", "Enviado", "Saiu para Entrega", "Entregue"}
        pedidos_com_receita = [p for p in pedidos if p.status in status_com_receita]
        faturamento = sum((p.total or 0) for p in pedidos_com_receita)
        ticket_medio = (faturamento / len(pedidos_com_receita)) if pedidos_com_receita else 0
        pedidos_pendentes = sum(1 for p in pedidos if p.status in {"Pendente", "Pago"})
        pedidos_validos = max(total_pedidos - cancelados, 0)
        taxa_conclusao = (entregues / pedidos_validos * 100) if pedidos_validos else 0

        # Gráfico de faturamento dos últimos 6 meses
        hoje = datetime.utcnow()
        meses_labels, meses_valores = [], []
        nomes_meses = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
        for meses_atras in range(5, -1, -1):
            indice_mes = hoje.year * 12 + (hoje.month - 1) - meses_atras
            ano, mes_zero = divmod(indice_mes, 12)
            mes = mes_zero + 1
            pedidos_mes = Order.query.filter(
                extract('year', Order.created_at) == ano,
                extract('month', Order.created_at) == mes,
                Order.status.in_(status_com_receita)
            ).all()
            total_mes = sum((p.total or 0) for p in pedidos_mes)
            meses_labels.append(f"{nomes_meses[mes - 1]}/{str(ano)[-2:]}")
            meses_valores.append(total_mes)

        maior_valor_mes = max(meses_valores, default=0)
        meses_serie = [
            {
                "label": label,
                "valor": valor,
                "altura": max(round(valor / maior_valor_mes * 100), 4) if maior_valor_mes else 4,
            }
            for label, valor in zip(meses_labels, meses_valores)
        ]

        produtos = Product.query.order_by(Product.created_at.desc(), Product.id.desc()).all()
        produtos_baixo_estoque = sorted(
            (produto for produto in produtos if (produto.estoque or 0) <= 10),
            key=lambda produto: (produto.estoque or 0, produto.titulo.lower()),
        )
        produtos_esgotados = sum(1 for produto in produtos if (produto.estoque or 0) <= 0)
        estoque_total = sum((produto.estoque or 0) for produto in produtos)
        clientes_ativos = User.query.filter_by(is_admin=False, is_active=True).count()
        fornecedores_ativos = Supplier.query.filter_by(active=True).count()
        origens_ativas = FulfillmentOrigin.query.filter_by(active=True).count()
        pedidos_recentes = sorted(
            pedidos,
            key=lambda pedido: pedido.created_at or datetime.min,
            reverse=True,
        )[:5]
        data_atual = f"{hoje.day:02d} de {nomes_meses[hoje.month - 1].lower()} de {hoje.year}"
        
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
            pedidos_pendentes=pedidos_pendentes,
            taxa_conclusao=taxa_conclusao,
            clientes_ativos=clientes_ativos,
            estoque_total=estoque_total,
            produtos_esgotados=produtos_esgotados,
            produtos_baixo_estoque=produtos_baixo_estoque[:5],
            pedidos_recentes=pedidos_recentes,
            data_atual=data_atual,
            meses_labels=meses_labels,
            meses_valores=meses_valores,
            meses_serie=meses_serie,
            fornecedores_ativos=fornecedores_ativos,
            origens_ativas=origens_ativas,
        )
    except Exception as e:
        logger.error(f"Erro no dashboard admin: {str(e)}", exc_info=True)
        return render_template("erro.html", mensagem="Erro ao carregar dashboard"), 500


# ============================================
# LOGÍSTICA E PARCEIROS
# ============================================

@admin_bp.route("/logistica")
@admin_required
def admin_logistica():
    settings = DeliverySettings.current()
    suppliers = Supplier.query.order_by(Supplier.active.desc(), Supplier.trade_name).all()
    brands = Brand.query.order_by(Brand.active.desc(), Brand.name).all()
    origins = FulfillmentOrigin.query.order_by(
        FulfillmentOrigin.active.desc(), FulfillmentOrigin.name
    ).all()
    inventories = ProductInventory.query.order_by(ProductInventory.updated_at.desc()).all()
    products = Product.query.order_by(Product.titulo).all()
    linked_products = sum(1 for product in products if product.fulfillment_origin_id)
    readiness = {
        "settings": bool(settings),
        "base": bool(settings and settings.base_origin_id),
        "costs": bool(
            settings
            and settings.fuel_efficiency_km_l
            and settings.fuel_price_per_liter
            and settings.hourly_rate is not None
        ),
        "origins": bool(origins),
        "products": linked_products,
        "products_total": len(products),
    }
    return render_template(
        "admin_logistica.html",
        settings=settings,
        suppliers=suppliers,
        brands=brands,
        origins=origins,
        inventories=inventories,
        products=products,
        readiness=readiness,
        success=request.args.get("success", ""),
        error=request.args.get("error", ""),
    )


@admin_bp.route("/logistica/configuracao", methods=["POST"])
@admin_required
def admin_logistica_configuracao():
    try:
        settings = DeliverySettings.current() or DeliverySettings()
        settings.base_origin_id = _existing_id(
            FulfillmentOrigin, request.form.get("base_origin_id"), "Local de saída"
        )
        settings.motorcycle_enabled = request.form.get("motorcycle_enabled") == "on"
        settings.vehicle_name = request.form.get("vehicle_name", "Suzuki 125").strip()
        settings.max_roundtrip_km = _optional_float(
            request.form.get("max_roundtrip_km"), "Limite de percurso"
        ) or 40.0
        settings.max_package_weight_kg = _optional_float(
            request.form.get("max_package_weight_kg"), "Peso máximo"
        )
        settings.fuel_efficiency_km_l = _optional_float(
            request.form.get("fuel_efficiency_km_l"), "Consumo da moto"
        )
        settings.fuel_price_per_liter = _optional_float(
            request.form.get("fuel_price_per_liter"), "Preço do combustível"
        )
        settings.maintenance_cost_per_km = _optional_float(
            request.form.get("maintenance_cost_per_km"), "Reserva de manutenção"
        ) or 0.0
        settings.hourly_rate = _optional_float(
            request.form.get("hourly_rate"), "Valor da hora"
        ) or 0.0
        settings.minimum_fee = _optional_float(
            request.form.get("minimum_fee"), "Taxa mínima"
        ) or 0.0
        settings.route_buffer_percent = _optional_float(
            request.form.get("route_buffer_percent"), "Margem de tempo"
        ) or 0.0
        settings.scheduled_delivery_enabled = (
            request.form.get("scheduled_delivery_enabled") == "on"
        )
        cutoff = request.form.get("same_day_cutoff", "14:00")
        datetime.strptime(cutoff, "%H:%M")
        settings.same_day_cutoff = cutoff
        db.session.add(settings)
        db.session.commit()
        return redirect(url_for("admin.admin_logistica", success="Configuração salva"))
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao salvar configuração logística", exc_info=True)
        return redirect(url_for(
            "admin.admin_logistica",
            error=_safe_form_error(exc, "Não foi possível salvar a configuração"),
        ))


@admin_bp.route("/logistica/fornecedores", methods=["POST"])
@admin_required
def admin_logistica_fornecedor():
    try:
        trade_name = request.form.get("trade_name", "").strip()
        if not trade_name:
            raise ValueError("Informe o nome do fornecedor")
        preparation_days = max(int(request.form.get("preparation_days", 1)), 0)
        supplier = Supplier(
            trade_name=trade_name,
            legal_name=request.form.get("legal_name", "").strip() or None,
            document=request.form.get("document", "").strip() or None,
            email=request.form.get("email", "").strip().lower() or None,
            phone=request.form.get("phone", "").strip() or None,
            direct_shipping=request.form.get("direct_shipping") == "on",
            preparation_days=preparation_days,
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(supplier)
        db.session.commit()
        return redirect(url_for("admin.admin_logistica", success="Fornecedor cadastrado"))
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao cadastrar fornecedor", exc_info=True)
        return redirect(url_for(
            "admin.admin_logistica",
            error=_safe_form_error(exc, "Não foi possível cadastrar o fornecedor"),
        ))


@admin_bp.route("/logistica/marcas", methods=["POST"])
@admin_required
def admin_logistica_marca():
    try:
        name = request.form.get("name", "").strip()
        if not name:
            raise ValueError("Informe o nome da marca")
        db.session.add(Brand(
            name=name,
            supplier_id=_existing_id(
                Supplier, request.form.get("supplier_id"), "Fornecedor"
            ),
        ))
        db.session.commit()
        return redirect(url_for("admin.admin_logistica", success="Marca cadastrada"))
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao cadastrar marca", exc_info=True)
        return redirect(url_for(
            "admin.admin_logistica",
            error=_safe_form_error(exc, "Não foi possível cadastrar a marca"),
        ))


@admin_bp.route("/logistica/origens", methods=["POST"])
@admin_required
def admin_logistica_origem():
    try:
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        if not name or not city:
            raise ValueError("Informe o nome e a cidade da origem")
        origin_type = request.form.get("origin_type", "supplier")
        if origin_type not in {"store", "supplier"}:
            raise ValueError("Tipo de origem inválido")
        origin = FulfillmentOrigin(
            name=name,
            origin_type=origin_type,
            supplier_id=_existing_id(
                Supplier, request.form.get("supplier_id"), "Fornecedor"
            ),
            postal_code=request.form.get("postal_code", "").strip() or None,
            street=request.form.get("street", "").strip() or None,
            number=request.form.get("number", "").strip() or None,
            complement=request.form.get("complement", "").strip() or None,
            district=request.form.get("district", "").strip() or None,
            city=city,
            state=request.form.get("state", "").strip().upper()[:2] or None,
            latitude=_coordinate(request.form.get("latitude"), "Latitude", -90, 90),
            longitude=_coordinate(
                request.form.get("longitude"), "Longitude", -180, 180
            ),
            direct_dispatch=request.form.get("direct_dispatch") == "on",
            carrier_pickup=request.form.get("carrier_pickup") == "on",
            preparation_days=max(int(request.form.get("preparation_days", 1)), 0),
        )
        db.session.add(origin)
        db.session.commit()
        return redirect(url_for("admin.admin_logistica", success="Origem cadastrada"))
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao cadastrar origem", exc_info=True)
        return redirect(url_for(
            "admin.admin_logistica",
            error=_safe_form_error(exc, "Não foi possível cadastrar a origem"),
        ))


@admin_bp.route("/logistica/estoque", methods=["POST"])
@admin_required
def admin_logistica_estoque():
    try:
        product_id = _optional_int(request.form.get("product_id"))
        origin_id = _optional_int(request.form.get("origin_id"))
        quantity = int(request.form.get("quantity", 0))
        product = db.session.get(Product, product_id)
        origin = db.session.get(FulfillmentOrigin, origin_id)
        if not product or not origin or quantity < 0:
            raise ValueError("Produto, origem ou quantidade inválidos")
        inventory = ProductInventory.query.filter_by(
            product_id=product.id, origin_id=origin.id
        ).first()
        if not inventory:
            inventory = ProductInventory(product_id=product.id, origin_id=origin.id)
            db.session.add(inventory)
        inventory.quantity = quantity
        inventory.active = True
        product.fulfillment_origin_id = origin.id
        product.supplier_id = product.supplier_id or origin.supplier_id
        db.session.flush()
        product.estoque = sum(
            row.quantity or 0
            for row in ProductInventory.query.filter_by(
                product_id=product.id, active=True
            ).all()
        )
        db.session.commit()
        return redirect(url_for("admin.admin_logistica", success="Estoque por origem salvo"))
    except Exception as exc:
        db.session.rollback()
        logger.error("Erro ao salvar estoque por origem", exc_info=True)
        return redirect(url_for(
            "admin.admin_logistica",
            error=_safe_form_error(exc, "Não foi possível salvar o estoque"),
        ))


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
                'estoque': request.form.get("estoque", 0),
                'categoria': request.form.get("categoria", "mel").strip(),
                'origem': request.form.get("origem", "").strip(),
                'beneficios': request.form.get("beneficios", "").strip(),
                'sem_adicao_acucar': request.form.get("sem_adicao_acucar") == "on",
                'destaque': request.form.get("destaque") == "on",
                'supplier_id': _existing_id(
                    Supplier, request.form.get("supplier_id"), "Fornecedor"
                ),
                'brand_id': _existing_id(
                    Brand, request.form.get("brand_id"), "Marca"
                ),
                'fulfillment_origin_id': _existing_id(
                    FulfillmentOrigin,
                    request.form.get("fulfillment_origin_id"),
                    "Origem",
                ),
            }
            package = {
                'weight_kg': _optional_float(request.form.get("weight_kg"), "Peso"),
                'width_cm': _optional_float(request.form.get("width_cm"), "Largura"),
                'height_cm': _optional_float(request.form.get("height_cm"), "Altura"),
                'length_cm': _optional_float(request.form.get("length_cm"), "Comprimento"),
            }
            
            # Validar dados
            is_valid, errors = Validator.validate_product_data(data)
            if not is_valid:
                logger.warning(f"Tentativa de criar produto com dados inválidos: {errors}")
                return render_template(
                    "admin_novo.html", **_product_form_context(erro="; ".join(errors))
                )
            
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
                imagem=f"imagens/{nome_arquivo}" if nome_arquivo else "",
                categoria=data['categoria'],
                origem=data['origem'],
                beneficios=data['beneficios'],
                sem_adicao_acucar=data['sem_adicao_acucar'],
                destaque=data['destaque'],
                supplier_id=data['supplier_id'],
                brand_id=data['brand_id'],
                fulfillment_origin_id=data['fulfillment_origin_id'],
                **package,
            )
            db.session.add(p)
            db.session.flush()
            _sync_primary_inventory(p)
            db.session.commit()
            
            logger.info(f"Produto criado - ID: {p.id} ({p.titulo}) - Admin: {session.get('user_id')}")
            return redirect("/admin")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar produto: {str(e)}", exc_info=True)
            return render_template(
                "admin_novo.html", **_product_form_context(erro="Erro ao criar produto")
            )
    
    return render_template("admin_novo.html", **_product_form_context())


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
                'estoque': request.form.get("estoque", 0),
                'categoria': request.form.get("categoria", "mel").strip(),
                'origem': request.form.get("origem", "").strip(),
                'beneficios': request.form.get("beneficios", "").strip(),
                'sem_adicao_acucar': request.form.get("sem_adicao_acucar") == "on",
                'destaque': request.form.get("destaque") == "on",
                'supplier_id': _existing_id(
                    Supplier, request.form.get("supplier_id"), "Fornecedor"
                ),
                'brand_id': _existing_id(
                    Brand, request.form.get("brand_id"), "Marca"
                ),
                'fulfillment_origin_id': _existing_id(
                    FulfillmentOrigin,
                    request.form.get("fulfillment_origin_id"),
                    "Origem",
                ),
            }
            package = {
                'weight_kg': _optional_float(request.form.get("weight_kg"), "Peso"),
                'width_cm': _optional_float(request.form.get("width_cm"), "Largura"),
                'height_cm': _optional_float(request.form.get("height_cm"), "Altura"),
                'length_cm': _optional_float(request.form.get("length_cm"), "Comprimento"),
            }
            
            # Validar
            is_valid, errors = Validator.validate_product_data(data)
            if not is_valid:
                logger.warning(f"Tentativa de editar produto {pid} com dados inválidos: {errors}")
                return render_template(
                    "admin_editar.html",
                    **_product_form_context(produto=p, erro="; ".join(errors)),
                )
            
            # Atualizar dados
            p.titulo = data['titulo']
            p.descricao = data['descricao']
            p.preco = float(data['preco'])
            p.estoque = int(data['estoque'])
            p.categoria = data['categoria']
            p.origem = data['origem']
            p.beneficios = data['beneficios']
            p.sem_adicao_acucar = data['sem_adicao_acucar']
            p.destaque = data['destaque']
            p.supplier_id = data['supplier_id']
            p.brand_id = data['brand_id']
            p.fulfillment_origin_id = data['fulfillment_origin_id']
            for field, value in package.items():
                setattr(p, field, value)
            
            # Processar nova imagem se enviada
            imagem_file = request.files.get("imagem")
            if imagem_file and imagem_file.filename:
                nome_arquivo = secure_filename(imagem_file.filename)
                imagem_file.save(os.path.join(UPLOAD_FOLDER, nome_arquivo))
                p.imagem = f"imagens/{nome_arquivo}"
            
            _sync_primary_inventory(p)
            db.session.commit()
            
            logger.info(f"Produto editado - ID: {pid} ({p.titulo}) - Admin: {session.get('user_id')}")
            return redirect("/admin")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar produto {pid}: {str(e)}", exc_info=True)
            return render_template(
                "admin_editar.html",
                **_product_form_context(produto=p, erro="Erro ao editar produto"),
            )
    
    return render_template(
        "admin_editar.html", **_product_form_context(produto=p)
    )


@admin_bp.route("/remover/<int:pid>", methods=["POST"])
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
        
        status_validos = ["Pendente", "Pago", "Agendado", "Saiu para Entrega", "Entregue", "Cancelado"]
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
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return "Erro ao atualizar status", 500


@admin_bp.route("/pedidos/<int:pedido_id>/agendar-entrega", methods=["POST"])
@admin_required
def admin_agendar_entrega(pedido_id):
    """Agendar data de entrega para um pedido"""
    try:
        pedido = Order.query.get_or_404(pedido_id)
        
        # Receber data e hora
        delivery_date_str = request.form.get("delivery_date")
        delivery_time_str = request.form.get("delivery_time", "14:00")  # Padrão 14h
        delivery_notes = request.form.get("delivery_notes", "")
        
        if not delivery_date_str:
            logger.warning(f"Tentativa de agendar sem data - Pedido {pedido_id}")
            return "Data de entrega obrigatória", 400
        
        # Combinar data e hora
        from datetime import datetime
        delivery_datetime = datetime.strptime(f"{delivery_date_str} {delivery_time_str}", "%Y-%m-%d %H:%M")
        
        # Atualizar pedido
        pedido.delivery_date = delivery_datetime
        pedido.delivery_scheduled_at = datetime.utcnow()
        pedido.delivery_notes = delivery_notes
        pedido.status = "Agendado"
        
        db.session.commit()
        
        logger.info(f"Entrega agendada para pedido {pedido_id}: {delivery_datetime} - Admin: {session.get('user_id')}")
        
        # Enviar email ao cliente
        try:
            user = User.query.get(pedido.user_id)
            if user:
                email_service.send_delivery_scheduled(
                    user_name=user.nome,
                    user_email=user.email,
                    order_id=pedido.id,
                    delivery_date=delivery_datetime,
                    delivery_notes=delivery_notes
                )
        except Exception as e:
            logger.error(f"Erro ao enviar email de agendamento para pedido {pedido_id}: {str(e)}")
        
        return redirect(f"/admin/pedidos/{pedido_id}")
        
    except ValueError:
        logger.error(f"Formato de data/hora inválido - Pedido {pedido_id}")
        return "Formato de data/hora inválido", 400
    except Exception as e:
        logger.error(f"Erro ao agendar entrega do pedido {pedido_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return "Erro ao agendar entrega", 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}", exc_info=True)
        return "Erro ao atualizar status", 500
