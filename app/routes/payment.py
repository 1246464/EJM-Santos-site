# ============================================
# routes/payment.py — Blueprint de Pagamento
# ============================================

from flask import Blueprint, request, jsonify, render_template, session, redirect
import stripe

payment_bp = Blueprint('payment', __name__)

# Variáveis globais (serão injetadas)
db = None
Product = None
Order = None
logger = None
email_service = None
CartHelper = None
OrderHelper = None
STRIPE_PUBLIC_KEY = None


def init_payment(database, models_dict, log, email_svc, cart_helper, order_helper, stripe_key):
    """Inicializa o blueprint com dependências"""
    global db, Product, Order, logger, email_service, CartHelper, OrderHelper, STRIPE_PUBLIC_KEY
    db = database
    Product = models_dict['Product']
    Order = models_dict['Order']
    logger = log
    email_service = email_svc
    CartHelper = cart_helper
    OrderHelper = order_helper
    STRIPE_PUBLIC_KEY = stripe_key


@payment_bp.route('/checkout')
def checkout():
    """Exibe a página de checkout com formulário de cartão"""
    user_id = session.get('user_id')
    if not user_id:
        session['redirect_after_login'] = "/checkout"
        return redirect("/login")

    carrinho_itens = CartHelper.snapshot_cart_for_checkout(
        db, 
        db.session.query(type('CartItem', (), {})).first().__class__, 
        Product
    )
    
    if not carrinho_itens:
        return redirect("/carrinho")

    total = sum(it["preco"] * it["quantidade"] for it in carrinho_itens)
    
    return render_template("checkout.html", 
                         itens=carrinho_itens, 
                         total=total,
                         stripe_public_key=STRIPE_PUBLIC_KEY)


@payment_bp.route('/processar-pagamento', methods=['POST'])
def processar_pagamento():
    """Processa o pagamento com Stripe"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            logger.warning(f"Tentativa de pagamento sem login - IP: {request.remote_addr}")
            return jsonify({"error": "Usuário não logado"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400
        
        payment_method_id = data.get('payment_method_id')
        endereco = data.get('endereco', {})
        
        if not payment_method_id:
            logger.warning(f"Pagamento sem método - User: {user_id}")
            return jsonify({"error": "Método de pagamento inválido"}), 400
        
        # Validar endereço
        if not all([endereco.get('rua'), endereco.get('numero'), endereco.get('bairro'), 
                    endereco.get('cidade'), endereco.get('telefone')]):
            logger.warning(f"Endereço incompleto no pagamento - User: {user_id}")
            return jsonify({"error": "Endereço de entrega incompleto"}), 400

        # Pegar itens do carrinho
        from app.models import CartItem
        carrinho_itens = CartHelper.snapshot_cart_for_checkout(db, CartItem, Product)
        
        if not carrinho_itens:
            logger.warning(f"Tentativa de pagamento com carrinho vazio - User: {user_id}")
            return jsonify({"error": "Carrinho vazio"}), 400

        # Calcular total (em centavos para Stripe)
        total = sum(it["preco"] * it["quantidade"] for it in carrinho_itens)
        total_centavos = int(total * 100)

        try:
            # Criar PaymentIntent no Stripe
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

            if intent['status'] == 'succeeded':
                # Descontar estoque
                for item in carrinho_itens:
                    produto = Product.query.get(item["product_id"])
                    if produto:
                        produto.estoque -= item["quantidade"]
                        if produto.estoque < 0:
                            produto.estoque = 0
                
                # Criar pedido
                from app.models import User, OrderItem
                pedido = OrderHelper.create_order_from_items(
                    db, Order, OrderItem, User,
                    user_id, carrinho_itens, email_service, logger
                )
                
                pedido.status = "Pago"
                pedido.endereco_rua = endereco.get('rua')
                pedido.endereco_numero = endereco.get('numero')
                pedido.endereco_complemento = endereco.get('complemento', '')
                pedido.endereco_bairro = endereco.get('bairro')
                pedido.endereco_cidade = endereco.get('cidade')
                pedido.telefone = endereco.get('telefone')
                db.session.commit()

                # Limpar carrinho
                CartHelper.clear_current_cart(db, CartItem)
                
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
            logger.warning(f"Erro de cartão - User: {user_id}: {e.user_message}")
            return jsonify({"error": f"Erro no cartão: {e.user_message}"}), 400
        except stripe.error.StripeError as e:
            logger.error(f"Erro do Stripe - User: {user_id}: {str(e)}")
            return jsonify({"error": f"Erro ao processar pagamento: {str(e)}"}), 500
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro inesperado no pagamento - User: {session.get('user_id')}: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro inesperado ao processar pagamento"}), 500


@payment_bp.route("/pagamento/sucesso")
def pagamento_sucesso():
    """Página de sucesso do pagamento"""
    pedido_id = request.args.get("pedido_id", type=int)
    return render_template("pagamento_sucesso.html", pedido_id=pedido_id)


@payment_bp.route("/pagamento/falha")
def pagamento_falha():
    """Página de falha no pagamento"""
    return render_template("pagamento_falha.html")


@payment_bp.route("/finalizar-compra")
def finalizar_compra():
    """Cria pedido pendente antes do pagamento"""
    if not session.get('user_id'):
        session['redirect_after_login'] = "/finalizar-compra"
        return redirect("/login")

    from app.models import CartItem, User, OrderItem
    itens = CartHelper.snapshot_cart_for_checkout(db, CartItem, Product)
    
    if not itens:
        return redirect("/carrinho")

    pedido = OrderHelper.create_order_from_items(
        db, Order, OrderItem, User,
        session['user_id'], itens, email_service, logger
    )
    
    # Esvaziar carrinho
    CartHelper.clear_current_cart(db, CartItem)
    
    return redirect(f"/pedido/{pedido.id}")


@payment_bp.route("/pedido/<int:id>")
def ver_pedido(id):
    """Visualizar detalhes de um pedido"""
    if not session.get('user_id'):
        return redirect("/login")
    
    pedido = Order.query.get_or_404(id)
    
    if pedido.user_id != session.get('user_id') and not session.get('is_admin'):
        return "Acesso não autorizado", 403
    
    from app.models import OrderItem
    detalhes = OrderHelper.get_order_details(Order, OrderItem, Product, id)
    
    if not detalhes:
        return "Pedido não encontrado", 404
    
    return render_template("pedido_detalhe.html", 
                         pedido=detalhes['pedido'], 
                         items=detalhes['itens'])
