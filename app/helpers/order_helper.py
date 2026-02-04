# ============================================
# helpers/order_helper.py — Helper de Pedidos
# ============================================


class OrderHelper:
    """Helper para operações de pedidos"""
    
    @staticmethod
    def create_order_from_items(db, Order, OrderItem, User, user_id, itens, email_service, logger):
        """
        Cria Order + OrderItems a partir dos itens do carrinho.
        
        Args:
            user_id: ID do usuário
            itens: Lista de dicionários com dados dos itens
            
        Returns:
            Order: Objeto do pedido criado
        """
        try:
            if not itens:
                raise ValueError("Carrinho vazio")
            
            if not user_id:
                raise ValueError("Usuário não identificado")
            
            # Calcular total
            total = sum(i["preco"] * i["quantidade"] for i in itens)
            
            # Criar pedido
            pedido = Order(user_id=user_id, total=total, status="Pendente")
            db.session.add(pedido)
            db.session.commit()  # gera pedido.id
            
            # Criar itens do pedido
            for it in itens:
                db.session.add(OrderItem(
                    order_id=pedido.id,
                    product_id=it["product_id"],
                    quantidade=it["quantidade"],
                    preco_unitario=it["preco"]
                ))
            db.session.commit()
            
            logger.info(f"Pedido criado - ID: {pedido.id} - User: {user_id} - Total: R$ {total:.2f}")
            
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
            logger.error(f"Erro ao criar pedido para user {user_id}: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def update_order_status(db, Order, User, order_id, new_status, email_service, logger):
        """
        Atualiza status de um pedido e envia email.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            pedido = Order.query.get(order_id)
            if not pedido:
                return False, "Pedido não encontrado"
            
            old_status = pedido.status
            pedido.status = new_status
            db.session.commit()
            
            # Enviar email se status mudou
            if old_status != new_status:
                try:
                    user = User.query.get(pedido.user_id)
                    if user:
                        email_service.send_order_status_update(
                            user_name=user.nome,
                            user_email=user.email,
                            order_id=pedido.id,
                            old_status=old_status,
                            new_status=new_status
                        )
                except Exception as e:
                    logger.error(f"Erro ao enviar email de atualização: {e}")
            
            logger.info(f"Status do pedido {order_id} atualizado: {old_status} -> {new_status}")
            return True, "Status atualizado"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar status do pedido {order_id}: {e}", exc_info=True)
            return False, "Erro ao atualizar status"
    
    @staticmethod
    def get_order_details(Order, OrderItem, Product, order_id):
        """
        Retorna detalhes completos de um pedido.
        
        Returns:
            dict: Dados do pedido com itens
        """
        pedido = Order.query.get(order_id)
        if not pedido:
            return None
        
        itens = OrderItem.query.filter_by(order_id=order_id).all()
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
        
        return {
            "pedido": pedido,
            "itens": detalhe_itens
        }
