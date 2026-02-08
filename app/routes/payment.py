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
    
    # Buscar endereços e métodos de pagamento salvos
    from app.models import Address, PaymentMethod
    saved_addresses = Address.query.filter_by(user_id=user_id).order_by(
        Address.is_default.desc(), 
        Address.created_at.desc()
    ).all()
    
    saved_payment_methods = PaymentMethod.query.filter_by(user_id=user_id).order_by(
        PaymentMethod.is_default.desc(), 
        PaymentMethod.created_at.desc()
    ).all()
    
    return render_template("checkout.html", 
                         itens=carrinho_itens, 
                         total=total,
                         stripe_public_key=STRIPE_PUBLIC_KEY,
                         saved_addresses=saved_addresses,
                         saved_payment_methods=saved_payment_methods)


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
        
        # Suporta tanto payment method novo quanto salvo
        payment_method_id = data.get('payment_method_id')
        saved_payment_method_id = data.get('saved_payment_method_id')
        save_card = data.get('save_card', False)  # Salvar novo cartão?
        card_nickname = data.get('card_nickname', 'Meu cartão')  # Apelido para salvar
        
        # Suporta tanto endereço novo quanto salvo
        saved_address_id = data.get('saved_address_id')
        endereco_data = data.get('endereco', {})
        save_address = data.get('save_address', False)  # Salvar novo endereço?
        address_nickname = data.get('address_nickname', 'Meu endereço')  # Apelido para salvar
        
        # Validar que tem método de pagamento (novo OU salvo)
        if not payment_method_id and not saved_payment_method_id:
            logger.warning(f"Pagamento sem método - User: {user_id}")
            return jsonify({"error": "Método de pagamento inválido"}), 400
        
        # Se usa payment method salvo, buscar o ID do Stripe
        if saved_payment_method_id:
            from app.models import PaymentMethod
            saved_pm = PaymentMethod.query.filter_by(id=saved_payment_method_id, user_id=user_id).first()
            if not saved_pm:
                return jsonify({"error": "Cartão salvo não encontrado"}), 404
            payment_method_id = saved_pm.stripe_payment_method_id
        
        # Buscar ou validar endereço
        endereco = {}
        if saved_address_id:
            # Usa endereço salvo
            from app.models import Address
            saved_addr = Address.query.filter_by(id=saved_address_id, user_id=user_id).first()
            if not saved_addr:
                return jsonify({"error": "Endereço salvo não encontrado"}), 404
            endereco = {
                'rua': saved_addr.rua,
                'numero': saved_addr.numero,
                'complemento': saved_addr.complemento or '',
                'bairro': saved_addr.bairro,
                'cidade': saved_addr.cidade,
                'telefone': saved_addr.telefone
            }
        else:
            # Usa endereço novo - validar
            endereco = endereco_data
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
                
                # Salvar endereço se solicitado (e não estava usando um salvo)
                if save_address and not saved_address_id:
                    try:
                        from app.models import Address
                        new_address = Address(
                            user_id=user_id,
                            apelido=address_nickname,
                            rua=endereco['rua'],
                            numero=endereco['numero'],
                            complemento=endereco.get('complemento', ''),
                            bairro=endereco['bairro'],
                            cidade=endereco['cidade'],
                            telefone=endereco['telefone'],
                            is_default=(Address.query.filter_by(user_id=user_id).count() == 0)
                        )
                        db.session.add(new_address)
                        db.session.commit()
                        logger.info(f"✅ Endereço salvo - User: {user_id}")
                    except Exception as e:
                        logger.error(f"Erro ao salvar endereço: {str(e)}")
                
                # Salvar cartão se solicitado (e não estava usando um salvo)
                if save_card and not saved_payment_method_id:
                    try:
                        from app.models import PaymentMethod
                        # Buscar info do cartão no Stripe
                        stripe_pm = stripe.PaymentMethod.retrieve(payment_method_id)
                        card = stripe_pm.card
                        
                        new_pm = PaymentMethod(
                            user_id=user_id,
                            apelido=card_nickname,
                            stripe_payment_method_id=payment_method_id,
                            card_brand=card.brand,
                            card_last4=card.last4,
                            card_exp_month=card.exp_month,
                            card_exp_year=card.exp_year,
                            is_default=(PaymentMethod.query.filter_by(user_id=user_id).count() == 0)
                        )
                        db.session.add(new_pm)
                        db.session.commit()
                        logger.info(f"✅ Cartão salvo - User: {user_id}")
                    except Exception as e:
                        logger.error(f"Erro ao salvar cartão: {str(e)}")

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
