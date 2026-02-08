# ============================================
# routes/profile.py — Blueprint de Perfil e Dados Salvos
# ============================================

from flask import Blueprint, request, jsonify, session
import stripe

profile_bp = Blueprint('profile', __name__)

# Variáveis globais (serão injetadas)
db = None
User = None
Address = None
PaymentMethod = None
logger = None


def init_profile(database, models_dict, log):
    """Inicializa o blueprint com dependências"""
    global db, User, Address, PaymentMethod, logger
    db = database
    User = models_dict.get('User')
    Address = models_dict.get('Address')
    PaymentMethod = models_dict.get('PaymentMethod')
    logger = log


# ============================================
# ROTAS DE ENDEREÇOS
# ============================================

@profile_bp.route('/api/addresses', methods=['GET'])
def get_addresses():
    """Retorna todos os endereços do usuário"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    try:
        addresses = Address.query.filter_by(user_id=user_id).order_by(
            Address.is_default.desc(), 
            Address.created_at.desc()
        ).all()
        
        return jsonify({
            "addresses": [addr.to_dict() for addr in addresses]
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao buscar endereços - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao buscar endereços"}), 500


@profile_bp.route('/api/addresses', methods=['POST'])
def add_address():
    """Adiciona um novo endereço"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    # Validar campos obrigatórios
    required_fields = ['apelido', 'rua', 'numero', 'bairro', 'cidade', 'telefone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Campo '{field}' é obrigatório"}), 400
    
    try:
        # Se é o primeiro endereço ou marcado como padrão, setar como default
        is_default = data.get('is_default', False)
        existing_count = Address.query.filter_by(user_id=user_id).count()
        
        if existing_count == 0:
            is_default = True
        elif is_default:
            # Remover default de outros endereços
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        # Criar novo endereço
        address = Address(
            user_id=user_id,
            apelido=data['apelido'].strip(),
            rua=data['rua'].strip(),
            numero=data['numero'].strip(),
            complemento=data.get('complemento', '').strip(),
            bairro=data['bairro'].strip(),
            cidade=data['cidade'].strip(),
            estado=data.get('estado', '').strip()[:2],  # Máx 2 chars
            cep=data.get('cep', '').strip(),
            telefone=data['telefone'].strip(),
            is_default=is_default
        )
        
        db.session.add(address)
        db.session.commit()
        
        logger.info(f"✅ Endereço adicionado - User: {user_id} - ID: {address.id}")
        
        return jsonify({
            "message": "Endereço salvo com sucesso",
            "address": address.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar endereço - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao salvar endereço"}), 500


@profile_bp.route('/api/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """Atualiza um endereço existente"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify({"error": "Endereço não encontrado"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    try:
        # Atualizar campos
        if 'apelido' in data:
            address.apelido = data['apelido'].strip()
        if 'rua' in data:
            address.rua = data['rua'].strip()
        if 'numero' in data:
            address.numero = data['numero'].strip()
        if 'complemento' in data:
            address.complemento = data['complemento'].strip()
        if 'bairro' in data:
            address.bairro = data['bairro'].strip()
        if 'cidade' in data:
            address.cidade = data['cidade'].strip()
        if 'estado' in data:
            address.estado = data['estado'].strip()[:2]
        if 'cep' in data:
            address.cep = data['cep'].strip()
        if 'telefone' in data:
            address.telefone = data['telefone'].strip()
        
        # Se marcou como padrão, desmarcar outros
        if data.get('is_default') and not address.is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
            address.is_default = True
        
        db.session.commit()
        
        logger.info(f"✅ Endereço atualizado - User: {user_id} - ID: {address_id}")
        
        return jsonify({
            "message": "Endereço atualizado com sucesso",
            "address": address.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar endereço - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao atualizar endereço"}), 500


@profile_bp.route('/api/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """Remove um endereço"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify({"error": "Endereço não encontrado"}), 404
    
    try:
        was_default = address.is_default
        db.session.delete(address)
        db.session.commit()
        
        # Se era o padrão, marcar o próximo como padrão
        if was_default:
            next_address = Address.query.filter_by(user_id=user_id).first()
            if next_address:
                next_address.is_default = True
                db.session.commit()
        
        logger.info(f"✅ Endereço removido - User: {user_id} - ID: {address_id}")
        
        return jsonify({"message": "Endereço removido com sucesso"}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover endereço - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao remover endereço"}), 500


@profile_bp.route('/api/addresses/<int:address_id>/set-default', methods=['POST'])
def set_default_address(address_id):
    """Define um endereço como padrão"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify({"error": "Endereço não encontrado"}), 404
    
    try:
        # Remover default de todos
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        # Marcar este como default
        address.is_default = True
        db.session.commit()
        
        logger.info(f"✅ Endereço padrão atualizado - User: {user_id} - ID: {address_id}")
        
        return jsonify({
            "message": "Endereço padrão atualizado",
            "address": address.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao definir endereço padrão - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao atualizar endereço"}), 500


# ============================================
# ROTAS DE MÉTODOS DE PAGAMENTO
# ============================================

@profile_bp.route('/api/payment-methods', methods=['GET'])
def get_payment_methods():
    """Retorna todos os métodos de pagamento do usuário"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    try:
        methods = PaymentMethod.query.filter_by(user_id=user_id).order_by(
            PaymentMethod.is_default.desc(), 
            PaymentMethod.created_at.desc()
        ).all()
        
        return jsonify({
            "payment_methods": [pm.to_dict() for pm in methods]
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao buscar métodos de pagamento - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao buscar métodos de pagamento"}), 500


@profile_bp.route('/api/payment-methods', methods=['POST'])
def add_payment_method():
    """Adiciona um novo método de pagamento (cartão)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    stripe_pm_id = data.get('stripe_payment_method_id')
    apelido = data.get('apelido', '').strip()
    
    if not stripe_pm_id:
        return jsonify({"error": "ID do método de pagamento é obrigatório"}), 400
    
    if not apelido:
        return jsonify({"error": "Apelido é obrigatório"}), 400
    
    try:
        # Buscar informações do cartão no Stripe
        try:
            stripe_pm = stripe.PaymentMethod.retrieve(stripe_pm_id)
            card = stripe_pm.card
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao buscar payment method no Stripe: {str(e)}")
            return jsonify({"error": "Cartão inválido ou não encontrado"}), 400
        
        # Verificar se já existe
        existing = PaymentMethod.query.filter_by(stripe_payment_method_id=stripe_pm_id).first()
        if existing:
            return jsonify({"error": "Este cartão já está salvo"}), 409
        
        # Se é o primeiro cartão ou marcado como padrão, setar como default
        is_default = data.get('is_default', False)
        existing_count = PaymentMethod.query.filter_by(user_id=user_id).count()
        
        if existing_count == 0:
            is_default = True
        elif is_default:
            # Remover default de outros cartões
            PaymentMethod.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        # Criar novo método de pagamento
        payment_method = PaymentMethod(
            user_id=user_id,
            apelido=apelido,
            stripe_payment_method_id=stripe_pm_id,
            card_brand=card.brand,
            card_last4=card.last4,
            card_exp_month=card.exp_month,
            card_exp_year=card.exp_year,
            is_default=is_default
        )
        
        db.session.add(payment_method)
        db.session.commit()
        
        logger.info(f"✅ Método de pagamento adicionado - User: {user_id} - ID: {payment_method.id}")
        
        return jsonify({
            "message": "Cartão salvo com sucesso",
            "payment_method": payment_method.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar método de pagamento - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao salvar cartão"}), 500


@profile_bp.route('/api/payment-methods/<int:pm_id>', methods=['DELETE'])
def delete_payment_method(pm_id):
    """Remove um método de pagamento"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    pm = PaymentMethod.query.filter_by(id=pm_id, user_id=user_id).first()
    if not pm:
        return jsonify({"error": "Método de pagamento não encontrado"}), 404
    
    try:
        was_default = pm.is_default
        stripe_pm_id = pm.stripe_payment_method_id
        
        # Remover do banco
        db.session.delete(pm)
        db.session.commit()
        
        # Se era o padrão, marcar o próximo como padrão
        if was_default:
            next_pm = PaymentMethod.query.filter_by(user_id=user_id).first()
            if next_pm:
                next_pm.is_default = True
                db.session.commit()
        
        # Tentar desanexar do Stripe (opcional - não bloqueia se falhar)
        try:
            stripe.PaymentMethod.detach(stripe_pm_id)
        except Exception as e:
            logger.warning(f"Não foi possível desanexar payment method do Stripe: {str(e)}")
        
        logger.info(f"✅ Método de pagamento removido - User: {user_id} - ID: {pm_id}")
        
        return jsonify({"message": "Cartão removido com sucesso"}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover método de pagamento - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao remover cartão"}), 500


@profile_bp.route('/api/payment-methods/<int:pm_id>/set-default', methods=['POST'])
def set_default_payment_method(pm_id):
    """Define um método de pagamento como padrão"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Não autenticado"}), 401
    
    pm = PaymentMethod.query.filter_by(id=pm_id, user_id=user_id).first()
    if not pm:
        return jsonify({"error": "Método de pagamento não encontrado"}), 404
    
    try:
        # Remover default de todos
        PaymentMethod.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        # Marcar este como default
        pm.is_default = True
        db.session.commit()
        
        logger.info(f"✅ Método de pagamento padrão atualizado - User: {user_id} - ID: {pm_id}")
        
        return jsonify({
            "message": "Cartão padrão atualizado",
            "payment_method": pm.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao definir método de pagamento padrão - User: {user_id}: {str(e)}")
        return jsonify({"error": "Erro ao atualizar cartão"}), 500
