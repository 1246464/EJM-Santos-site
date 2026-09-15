"""API dedicada ao aplicativo Android nativo."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
import re
import secrets
from threading import Thread

import jwt
import stripe
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.utils.validators import Validator


mobile_bp = Blueprint("mobile", __name__, url_prefix="/api/mobile")

db = None
User = None
Order = None
OrderItem = None
Product = None
Address = None
CartItem = None
Review = None
PaymentMethod = None
app_config = None
logger = None
email_service = None


def init_mobile(database, models, config, log, email_svc=None):
    global db, User, Order, OrderItem, Product, Address, CartItem, Review, PaymentMethod
    global app_config, logger, email_service
    db = database
    User = models["User"]
    Order = models["Order"]
    OrderItem = models["OrderItem"]
    Product = models["Product"]
    Address = models["Address"]
    CartItem = models["CartItem"]
    Review = models["Review"]
    PaymentMethod = models["PaymentMethod"]
    app_config = config
    logger = log
    email_service = email_svc


def _create_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user.id,
        "type": "mobile",
        "version": user.mobile_token_version or 0,
        "iat": now,
        "exp": now + timedelta(days=30),
    }
    return jwt.encode(payload, app_config["SECRET_KEY"], algorithm="HS256")


def _user_payload(user):
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "is_admin": user.is_admin,
    }


def _utcnow():
    # Os modelos existentes usam DateTime sem fuso; mantenha a comparação
    # consistente até a migração global para timestamps timezone-aware.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _valid_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"[0-9]", password)
    )


def _money(value):
    """Normaliza valores monetários para duas casas decimais."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _address_for_user(user, address_id):
    try:
        parsed_id = int(address_id)
    except (TypeError, ValueError):
        return None
    return Address.query.filter_by(id=parsed_id, user_id=user.id).first()


def _requested_quantities(raw_items):
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Seu carrinho está vazio")
    if len(raw_items) > 50:
        raise ValueError("O carrinho ultrapassou o limite de itens")

    quantities = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("Item do carrinho inválido")
        try:
            product_id = int(raw_item.get("product_id"))
            quantity = int(raw_item.get("quantity"))
        except (TypeError, ValueError):
            raise ValueError("Item do carrinho inválido") from None
        if product_id <= 0 or quantity <= 0 or quantity > 99:
            raise ValueError("Quantidade de produto inválida")
        quantities[product_id] = quantities.get(product_id, 0) + quantity
        if quantities[product_id] > 99:
            raise ValueError("Quantidade de produto inválida")
    return quantities


def _cart_snapshot(raw_items):
    """Busca preço e estoque atuais; nunca confia nos valores enviados pelo app."""
    quantities = _requested_quantities(raw_items)
    products = Product.query.filter(Product.id.in_(quantities.keys())).all()
    by_id = {product.id: product for product in products}

    if len(by_id) != len(quantities):
        raise LookupError("Um dos produtos não está mais disponível")

    lines = []
    subtotal = Decimal("0.00")
    for product_id, quantity in quantities.items():
        product = by_id[product_id]
        if product.estoque < quantity:
            raise RuntimeError(
                f"Estoque insuficiente para {product.titulo}. Disponível: {product.estoque}"
            )
        unit_price = _money(product.preco)
        line_total = unit_price * quantity
        subtotal += line_total
        lines.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })
    return lines, _money(subtotal)


def _delivery_for(address):
    from app.utils.distance import calculate_delivery_fee, format_endereco_completo

    address_data = {
        "rua": address.rua,
        "numero": address.numero,
        "bairro": address.bairro,
        "cidade": address.cidade,
        "estado": address.estado,
        "cep": address.cep,
    }
    distance_km, delivery_fee = calculate_delivery_fee(
        app_config.get("STORE_COORDINATES", (-23.550520, -46.633308)),
        format_endereco_completo(address_data),
        app_config.get("DELIVERY_FEE_PER_KM", 1.50),
    )
    return float(distance_km), _money(delivery_fee)


def _order_payload(order):
    data = order.to_dict(include_items=True)
    for item_data, item in zip(data["items"], order.items):
        item_data["produto"] = {
            "titulo": item.product.titulo if item.product else "Produto indisponível",
            "imagem": item.product.imagem if item.product else "",
        }
    return data


def _create_reserved_order(user, address, lines, subtotal, distance_km,
                           delivery_fee, client_reference, payment_method,
                           status, payment_status):
    """Cria pedido e reserva estoque dentro da transação atual."""
    order = Order(
        user_id=user.id,
        subtotal=float(subtotal),
        delivery_fee=float(delivery_fee),
        delivery_distance_km=distance_km,
        total=float(subtotal + delivery_fee),
        status=status,
        client_reference=client_reference,
        payment_method=payment_method,
        payment_status=payment_status,
        inventory_released=False,
        endereco_rua=address.rua,
        endereco_numero=address.numero,
        endereco_complemento=address.complemento,
        endereco_bairro=address.bairro,
        endereco_cidade=address.cidade,
        endereco_estado=address.estado,
        endereco_cep=address.cep,
        telefone=address.telefone,
    )
    db.session.add(order)
    db.session.flush()

    for line in lines:
        product = line["product"]
        quantity = line["quantity"]
        # UPDATE condicional impede estoque negativo mesmo com duas compras
        # concorrentes para a última unidade.
        changed = Product.query.filter(
            Product.id == product.id,
            Product.estoque >= quantity,
        ).update(
            {Product.estoque: Product.estoque - quantity},
            synchronize_session=False,
        )
        if changed != 1:
            raise RuntimeError(f"Estoque insuficiente para {product.titulo}")
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantidade=quantity,
            preco_unitario=float(line["unit_price"]),
        ))
    return order


def _release_inventory(order):
    """Devolve uma reserva cancelada apenas uma vez."""
    if order.inventory_released:
        return
    for item in order.items:
        Product.query.filter(Product.id == item.product_id).update(
            {Product.estoque: Product.estoque + item.quantidade},
            synchronize_session=False,
        )
    order.inventory_released = True


def _valid_client_reference(value):
    return re.fullmatch(r"[A-Za-z0-9_-]{8,64}", str(value or "").strip()) is not None


def _stripe_enabled():
    return bool(
        app_config.get("STRIPE_SECRET_KEY")
        and app_config.get("STRIPE_PUBLIC_KEY")
        and app_config.get("STRIPE_WEBHOOK_SECRET")
    )


def _notify_order_status(order, old_status, new_status):
    if app_config.get("TESTING") or not email_service or old_status == new_status:
        return
    args = {
        "user_name": order.user.nome,
        "user_email": order.user.email,
        "order_id": order.id,
        "old_status": old_status,
        "new_status": new_status,
    }
    Thread(
        target=lambda: email_service.send_order_status_update(**args),
        name=f"email-order-status-{order.id}",
        daemon=True,
    ).start()


def _notify_order_created(order):
    if app_config.get("TESTING") or not email_service:
        return
    items = [{
        "titulo": item.product.titulo if item.product else f"Produto #{item.product_id}",
        "quantidade": item.quantidade,
        "preco": item.preco_unitario * item.quantidade,
    } for item in order.items]
    args = {
        "user_name": order.user.nome,
        "user_email": order.user.email,
        "order_id": order.id,
        "order_items": items,
        "total": order.total,
        "endereco_completo": (
            f"{order.endereco_rua}, {order.endereco_numero} - "
            f"{order.endereco_bairro}, {order.endereco_cidade}"
        ),
    }
    Thread(
        target=lambda: email_service.send_order_confirmation(**args),
        name=f"email-order-created-{order.id}",
        daemon=True,
    ).start()


def token_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"message": "Token de acesso necessário"}), 401

        try:
            token = authorization.removeprefix("Bearer ").strip()
            payload = jwt.decode(token, app_config["SECRET_KEY"], algorithms=["HS256"])
            if payload.get("type") != "mobile":
                raise jwt.InvalidTokenError("tipo de token inválido")
            user = db.session.get(User, payload.get("user_id"))
            if not user or not user.is_active:
                raise jwt.InvalidTokenError("usuário não encontrado")
            if payload.get("version", 0) != (user.mobile_token_version or 0):
                raise jwt.InvalidTokenError("sessão revogada")
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Sessão expirada"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token inválido"}), 401

        return view(user, *args, **kwargs)
    return decorated


@mobile_bp.get("/health")
def health():
    return jsonify({"status": "ok", "api": "mobile", "version": 1})


@mobile_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("senha", "")

    valid_email, _ = Validator.validate_email(email)
    if not valid_email or not password:
        return jsonify({"message": "Email e senha são obrigatórios"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not check_password_hash(user.senha_hash, password):
        return jsonify({"message": "Credenciais inválidas"}), 401

    logger.info("Login no aplicativo - User ID: %s", user.id)
    return jsonify({"token": _create_token(user), "user": _user_payload(user)})


@mobile_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("nome", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("senha", "")

    valid_name, name_error = Validator.validate_name(name)
    valid_email, email_error = Validator.validate_email(email)
    if not valid_name:
        return jsonify({"message": name_error}), 400
    if not valid_email:
        return jsonify({"message": email_error}), 400
    if not _valid_password(password):
        return jsonify({"message": "A senha deve ter 8 caracteres, maiúscula, minúscula e número"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email já cadastrado"}), 409

    try:
        user = User(
            nome=name,
            email=email,
            senha_hash=generate_password_hash(password),
            is_admin=False,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        logger.info("Cadastro no aplicativo - User ID: %s", user.id)
        return jsonify({"token": _create_token(user), "user": _user_payload(user)}), 201
    except Exception:
        db.session.rollback()
        logger.exception("Falha ao cadastrar usuário pelo aplicativo")
        return jsonify({"message": "Não foi possível concluir o cadastro"}), 500


@mobile_bp.get("/me")
@token_required
def me(user):
    return jsonify({"user": _user_payload(user)})


@mobile_bp.post("/auth/refresh")
@token_required
def refresh_token(user):
    return jsonify({"token": _create_token(user), "user": _user_payload(user)})


@mobile_bp.post("/auth/logout")
@token_required
def logout(user):
    user.mobile_token_version = (user.mobile_token_version or 0) + 1
    db.session.commit()
    logger.info("Sessões móveis revogadas - User ID: %s", user.id)
    return jsonify({"message": "Sessão encerrada"})


@mobile_bp.post("/auth/password/reset/request")
def request_password_reset():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    generic_response = {
        "message": "Se o email estiver cadastrado, enviaremos um código de recuperação"
    }

    valid_email, _ = Validator.validate_email(email)
    if not valid_email:
        return jsonify(generic_response), 202

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        # Mantém custo semelhante e não revela se o endereço está cadastrado.
        generate_password_hash(f"{secrets.randbelow(1_000_000):06d}")
        return jsonify(generic_response), 202

    code = f"{secrets.randbelow(1_000_000):06d}"
    user.password_reset_hash = generate_password_hash(code)
    user.password_reset_expires_at = _utcnow() + timedelta(minutes=15)
    user.password_reset_attempts = 0
    db.session.commit()

    if email_service and not app_config.get("TESTING"):
        reset_email_args = {
            "user_name": user.nome,
            "user_email": user.email,
            "code": code,
            "expires_minutes": 15,
        }
        Thread(
            target=lambda: email_service.send_password_reset_code(**reset_email_args),
            name=f"email-password-reset-{user.id}",
            daemon=True,
        ).start()
    logger.info("Recuperação de senha solicitada - User ID: %s", user.id)
    return jsonify(generic_response), 202


@mobile_bp.post("/auth/password/reset/confirm")
def confirm_password_reset():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    code = str(data.get("code", "")).strip()
    new_password = str(data.get("new_password", ""))

    if not _valid_password(new_password):
        return jsonify({
            "message": "A senha deve ter 8 caracteres, maiúscula, minúscula e número"
        }), 400

    user = User.query.filter_by(email=email, is_active=True).first()
    invalid = (
        not user
        or not user.password_reset_hash
        or not user.password_reset_expires_at
        or user.password_reset_expires_at < _utcnow()
        or user.password_reset_attempts >= 5
    )
    if invalid:
        return jsonify({"message": "Código inválido ou expirado"}), 400

    if not re.fullmatch(r"\d{6}", code) or not check_password_hash(
            user.password_reset_hash, code):
        user.password_reset_attempts = (user.password_reset_attempts or 0) + 1
        if user.password_reset_attempts >= 5:
            user.password_reset_hash = None
            user.password_reset_expires_at = None
        db.session.commit()
        return jsonify({"message": "Código inválido ou expirado"}), 400

    user.senha_hash = generate_password_hash(new_password)
    user.password_reset_hash = None
    user.password_reset_expires_at = None
    user.password_reset_attempts = 0
    user.mobile_token_version = (user.mobile_token_version or 0) + 1
    db.session.commit()
    logger.info("Senha recuperada pelo aplicativo - User ID: %s", user.id)
    return jsonify({"message": "Senha atualizada. Entre novamente"})


@mobile_bp.post("/auth/password/change")
@token_required
def change_password(user):
    data = request.get_json(silent=True) or {}
    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))
    if not check_password_hash(user.senha_hash, current_password):
        return jsonify({"message": "Senha atual incorreta"}), 400
    if not _valid_password(new_password):
        return jsonify({
            "message": "A nova senha deve ter 8 caracteres, maiúscula, minúscula e número"
        }), 400
    if check_password_hash(user.senha_hash, new_password):
        return jsonify({"message": "Escolha uma senha diferente da atual"}), 400

    user.senha_hash = generate_password_hash(new_password)
    user.mobile_token_version = (user.mobile_token_version or 0) + 1
    db.session.commit()
    logger.info("Senha alterada pelo aplicativo - User ID: %s", user.id)
    return jsonify({
        "message": "Senha alterada",
        "token": _create_token(user),
        "user": _user_payload(user),
    })


@mobile_bp.post("/account/delete")
@token_required
def delete_account(user):
    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))
    confirmation = str(data.get("confirmation", "")).strip().upper()
    if user.is_admin:
        return jsonify({"message": "Uma conta administradora não pode ser excluída pelo app"}), 403
    if confirmation != "EXCLUIR" or not check_password_hash(user.senha_hash, password):
        return jsonify({"message": "Senha ou confirmação inválida"}), 400

    try:
        # Pedidos permanecem vinculados a um registro anonimizado para preservar
        # a operação e o histórico financeiro. Dados de uso da conta são removidos.
        Address.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        CartItem.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Review.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        PaymentMethod.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        user.nome = "Conta excluída"
        user.email = f"deleted-{user.id}-{secrets.token_hex(8)}@deleted.invalid"
        user.senha_hash = generate_password_hash(secrets.token_urlsafe(32))
        user.is_active = False
        user.deleted_at = _utcnow()
        user.password_reset_hash = None
        user.password_reset_expires_at = None
        user.password_reset_attempts = 0
        user.mobile_token_version = (user.mobile_token_version or 0) + 1
        db.session.commit()
        logger.info("Conta anonimizada pelo aplicativo - User ID: %s", user.id)
        return jsonify({
            "message": "Conta excluída. Dados necessários dos pedidos foram preservados"
        })
    except Exception:
        db.session.rollback()
        logger.exception("Falha ao excluir conta pelo aplicativo - User ID: %s", user.id)
        return jsonify({"message": "Não foi possível excluir a conta"}), 500


@mobile_bp.get("/orders")
@token_required
def orders(user):
    user_orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    result = []
    for order in user_orders:
        result.append(_order_payload(order))
    return jsonify({"orders": result})


@mobile_bp.post("/checkout/quote")
@token_required
def checkout_quote(user):
    data = request.get_json(silent=True) or {}
    address = _address_for_user(user, data.get("address_id"))
    if not address:
        return jsonify({"message": "Selecione um endereço válido"}), 404

    try:
        lines, subtotal = _cart_snapshot(data.get("items"))
        distance_km, delivery_fee = _delivery_for(address)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except LookupError as error:
        return jsonify({"message": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 409
    except Exception:
        logger.exception("Falha ao calcular checkout móvel")
        return jsonify({"message": "Não foi possível calcular a entrega"}), 503

    return jsonify({
        "address": address.to_dict(),
        "items": [{
            "product_id": line["product"].id,
            "title": line["product"].titulo,
            "quantity": line["quantity"],
            "unit_price": float(line["unit_price"]),
            "subtotal": float(line["line_total"]),
        } for line in lines],
        "subtotal": float(subtotal),
        "delivery_distance_km": distance_km,
        "delivery_fee": float(delivery_fee),
        "total": float(subtotal + delivery_fee),
        "payment_methods": (
            ["cash_on_delivery", "stripe"] if _stripe_enabled()
            else ["cash_on_delivery"]
        ),
    })


@mobile_bp.post("/orders")
@token_required
def create_order(user):
    data = request.get_json(silent=True) or {}
    client_reference = str(data.get("client_reference", "")).strip()
    if not _valid_client_reference(client_reference):
        return jsonify({"message": "Identificador da compra inválido"}), 400

    payment_method = str(data.get("payment_method", "")).strip()
    if payment_method != "cash_on_delivery":
        return jsonify({"message": "Forma de pagamento indisponível"}), 400

    existing = Order.query.filter_by(
        user_id=user.id, client_reference=client_reference
    ).first()
    if existing:
        if existing.payment_method != payment_method:
            return jsonify({
                "message": "Já existe um pagamento iniciado para esta compra"
            }), 409
        return jsonify({
            "message": "Pedido já recebido",
            "duplicate": True,
            "order": _order_payload(existing),
        })

    address = _address_for_user(user, data.get("address_id"))
    if not address:
        return jsonify({"message": "Selecione um endereço válido"}), 404

    try:
        # A taxa pode depender de uma chamada de geocodificação; faça isso antes
        # da transação que altera o estoque.
        distance_km, delivery_fee = _delivery_for(address)
        lines, subtotal = _cart_snapshot(data.get("items"))

        order = _create_reserved_order(
            user, address, lines, subtotal, distance_km, delivery_fee,
            client_reference, payment_method, "Pendente", "pending",
        )

        db.session.commit()
        logger.info(
            "Pedido móvel criado - ID: %s - User: %s - Total: R$ %.2f",
            order.id, user.id, order.total,
        )
        _notify_order_created(order)
        return jsonify({
            "message": "Pedido realizado com sucesso",
            "duplicate": False,
            "order": _order_payload(order),
        }), 201
    except ValueError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 400
    except LookupError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 404
    except RuntimeError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 409
    except Exception:
        db.session.rollback()
        # Uma disputa entre dois reenvios pode atingir o índice único. Nesse
        # caso, devolva o pedido já criado em vez de gerar uma segunda venda.
        existing = Order.query.filter_by(
            user_id=user.id, client_reference=client_reference
        ).first()
        if existing:
            return jsonify({
                "message": "Pedido já recebido",
                "duplicate": True,
                "order": _order_payload(existing),
            })
        logger.exception("Falha ao criar pedido móvel")
        return jsonify({"message": "Não foi possível concluir o pedido"}), 500


def _stripe_intent_payload(order, intent):
    return {
        "publishable_key": app_config["STRIPE_PUBLIC_KEY"],
        "client_secret": intent["client_secret"],
        "order": _order_payload(order),
    }


@mobile_bp.post("/payments/stripe/intent")
@token_required
def create_stripe_intent(user):
    if not _stripe_enabled():
        return jsonify({
            "message": "Pagamento por cartão ainda não está configurado"
        }), 503

    data = request.get_json(silent=True) or {}
    client_reference = str(data.get("client_reference", "")).strip()
    if not _valid_client_reference(client_reference):
        return jsonify({"message": "Identificador da compra inválido"}), 400

    existing = Order.query.filter_by(
        user_id=user.id, client_reference=client_reference
    ).first()
    if existing:
        if existing.payment_method != "stripe" or not existing.external_payment_id:
            return jsonify({"message": "Esta compra já foi utilizada"}), 409
        if existing.payment_status == "paid":
            return jsonify({"message": "Este pedido já está pago", "order": _order_payload(existing)}), 409
        if existing.payment_status == "canceled":
            return jsonify({
                "message": "Este pagamento expirou. Volte ao carrinho e tente novamente"
            }), 409
        try:
            intent = stripe.PaymentIntent.retrieve(existing.external_payment_id)
            return jsonify(_stripe_intent_payload(existing, intent))
        except stripe.error.StripeError:
            logger.exception("Falha ao recuperar PaymentIntent %s", existing.external_payment_id)
            return jsonify({"message": "Não foi possível retomar o pagamento"}), 502

    address = _address_for_user(user, data.get("address_id"))
    if not address:
        return jsonify({"message": "Selecione um endereço válido"}), 404

    intent = None
    try:
        distance_km, delivery_fee = _delivery_for(address)
        lines, subtotal = _cart_snapshot(data.get("items"))
        order = _create_reserved_order(
            user, address, lines, subtotal, distance_km, delivery_fee,
            client_reference, "stripe", "Aguardando pagamento", "requires_payment",
        )

        total_cents = int(_money(subtotal + delivery_fee) * 100)
        intent = stripe.PaymentIntent.create(
            amount=total_cents,
            currency="brl",
            automatic_payment_methods={"enabled": True},
            description=f"Pedido EJM Santos #{order.id}",
            receipt_email=user.email,
            metadata={
                "order_id": str(order.id),
                "user_id": str(user.id),
                "client_reference": client_reference,
            },
            idempotency_key=f"ejm-mobile-{client_reference}",
        )
        order.external_payment_id = intent["id"]
        db.session.commit()
        logger.info("PaymentIntent criado - Pedido: %s - Intent: %s", order.id, intent["id"])
        return jsonify(_stripe_intent_payload(order, intent)), 201
    except ValueError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 400
    except LookupError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 404
    except RuntimeError as error:
        db.session.rollback()
        return jsonify({"message": str(error)}), 409
    except stripe.error.StripeError:
        db.session.rollback()
        logger.exception("Falha do Stripe ao iniciar pagamento móvel")
        return jsonify({"message": "O Stripe não conseguiu iniciar o pagamento"}), 502
    except Exception:
        db.session.rollback()
        if intent is not None:
            try:
                stripe.PaymentIntent.cancel(intent["id"])
            except Exception:
                logger.exception("Não foi possível cancelar PaymentIntent órfão")
        logger.exception("Falha ao preparar pagamento móvel")
        return jsonify({"message": "Não foi possível preparar o pagamento"}), 500


@mobile_bp.post("/payments/stripe/webhook")
def stripe_webhook():
    webhook_secret = app_config.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("Webhook Stripe chamado sem STRIPE_WEBHOOK_SECRET configurado")
        return jsonify({"message": "Webhook indisponível"}), 503

    try:
        event = stripe.Webhook.construct_event(
            request.get_data(cache=False),
            request.headers.get("Stripe-Signature", ""),
            webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        logger.warning("Webhook Stripe rejeitado por assinatura inválida")
        return jsonify({"message": "Assinatura inválida"}), 400

    event_type = event["type"]
    intent = event["data"]["object"]
    if event_type not in {
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.canceled",
    }:
        return jsonify({"received": True})

    order = Order.query.filter_by(external_payment_id=intent.get("id")).first()
    if not order:
        logger.warning("Webhook para PaymentIntent desconhecido: %s", intent.get("id"))
        return jsonify({"received": True})

    old_status = order.status
    if event_type == "payment_intent.succeeded":
        expected_amount = int(_money(order.total) * 100)
        paid_amount = int(intent.get("amount_received") or intent.get("amount") or 0)
        if intent.get("currency") != "brl" or paid_amount != expected_amount:
            order.payment_status = "amount_mismatch"
            order.status = "Revisão necessária"
            logger.error(
                "Pagamento divergente - Pedido: %s - esperado: %s - recebido: %s %s",
                order.id, expected_amount, paid_amount, intent.get("currency"),
            )
        else:
            order.payment_status = "paid"
            order.status = "Pago"
    elif event_type == "payment_intent.payment_failed" and order.payment_status != "paid":
        order.payment_status = "failed"
        order.status = "Pagamento recusado"
    elif event_type == "payment_intent.canceled" and order.payment_status != "paid":
        _release_inventory(order)
        order.payment_status = "canceled"
        order.status = "Cancelado"

    db.session.commit()
    _notify_order_status(order, old_status, order.status)
    logger.info("Webhook Stripe processado - Pedido: %s - Evento: %s", order.id, event_type)
    return jsonify({"received": True})


@mobile_bp.get("/addresses")
@token_required
def addresses(user):
    saved = Address.query.filter_by(user_id=user.id).order_by(
        Address.is_default.desc(), Address.created_at.desc()
    ).all()
    return jsonify({"addresses": [address.to_dict() for address in saved]})


@mobile_bp.post("/addresses")
@token_required
def create_address(user):
    data = request.get_json(silent=True) or {}
    required = ("apelido", "rua", "numero", "bairro", "cidade", "telefone")
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"message": f"Preencha o campo {missing[0]}"}), 400

    if len(str(data.get("estado", "")).strip()) not in (0, 2):
        return jsonify({"message": "Use a sigla do estado com duas letras"}), 400

    try:
        existing_count = Address.query.filter_by(user_id=user.id).count()
        make_default = existing_count == 0 or bool(data.get("is_default"))
        if make_default:
            Address.query.filter_by(user_id=user.id, is_default=True).update({"is_default": False})

        address = Address(
            user_id=user.id,
            apelido=str(data["apelido"]).strip()[:50],
            rua=str(data["rua"]).strip()[:200],
            numero=str(data["numero"]).strip()[:20],
            complemento=str(data.get("complemento", "")).strip()[:100],
            bairro=str(data["bairro"]).strip()[:100],
            cidade=str(data["cidade"]).strip()[:100],
            estado=str(data.get("estado", "")).strip().upper()[:2],
            cep=str(data.get("cep", "")).strip()[:10],
            telefone=str(data["telefone"]).strip()[:20],
            is_default=make_default,
        )
        db.session.add(address)
        db.session.commit()
        return jsonify({"message": "Endereço salvo", "address": address.to_dict()}), 201
    except Exception:
        db.session.rollback()
        logger.exception("Falha ao salvar endereço pelo aplicativo")
        return jsonify({"message": "Não foi possível salvar o endereço"}), 500


@mobile_bp.post("/addresses/<int:address_id>/default")
@token_required
def make_address_default(user, address_id):
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        return jsonify({"message": "Endereço não encontrado"}), 404
    Address.query.filter_by(user_id=user.id, is_default=True).update({"is_default": False})
    address.is_default = True
    db.session.commit()
    return jsonify({"message": "Endereço padrão atualizado"})


@mobile_bp.delete("/addresses/<int:address_id>")
@token_required
def delete_address(user, address_id):
    address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        return jsonify({"message": "Endereço não encontrado"}), 404

    was_default = address.is_default
    db.session.delete(address)
    db.session.commit()
    if was_default:
        replacement = Address.query.filter_by(user_id=user.id).first()
        if replacement:
            replacement.is_default = True
            db.session.commit()
    return jsonify({"message": "Endereço removido"})
