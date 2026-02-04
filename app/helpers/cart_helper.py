# ============================================
# helpers/cart_helper.py — Helper do Carrinho
# ============================================

from flask import session


class CartHelper:
    """Helper para operações de carrinho"""
    
    @staticmethod
    def snapshot_cart_for_checkout(db, CartItem, Product):
        """
        Retorna itens do carrinho atual em formato padrão.
        
        Returns:
            list: [{"titulo": str, "quantidade": int, "preco": float, "product_id": int}]
        """
        itens = []
        
        if session.get('user_id'):
            # Usuário logado: busca do banco
            user_id = session['user_id']
            for it in CartItem.query.filter_by(user_id=user_id).all():
                if it.product:
                    itens.append({
                        "titulo": it.product.titulo,
                        "quantidade": int(it.quantity),
                        "preco": float(it.product.preco),
                        "product_id": it.product.id
                    })
        else:
            # Visitante: busca da sessão
            cart = session.get('cart', {})
            for pid_str, qtd in cart.items():
                p = Product.query.get(int(pid_str))
                if p:
                    itens.append({
                        "titulo": p.titulo,
                        "quantidade": int(qtd),
                        "preco": float(p.preco),
                        "product_id": p.id
                    })
        
        return itens
    
    @staticmethod
    def clear_current_cart(db, CartItem):
        """Esvazia o carrinho (sessão e DB do usuário logado)"""
        session.pop('cart', None)
        
        if session.get('user_id'):
            CartItem.query.filter_by(user_id=session['user_id']).delete()
            db.session.commit()
    
    @staticmethod
    def get_cart_count(CartItem):
        """Retorna quantidade de itens no carrinho"""
        if session.get('user_id'):
            return CartItem.query.filter_by(user_id=session['user_id']).count()
        else:
            cart = session.get('cart', {})
            return sum(cart.values())
    
    @staticmethod
    def add_to_cart(db, CartItem, Product, product_id):
        """
        Adiciona produto ao carrinho.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        produto = Product.query.get(product_id)
        if not produto:
            return False, "Produto não encontrado"
        
        if produto.estoque <= 0:
            return False, "Produto esgotado"
        
        if session.get('user_id'):
            # Usuário logado
            user_id = session['user_id']
            item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
            
            quantidade_atual = item.quantity if item else 0
            if quantidade_atual + 1 > produto.estoque:
                return False, "Estoque insuficiente"
            
            if item:
                item.quantity += 1
            else:
                db.session.add(CartItem(user_id=user_id, product_id=product_id, quantity=1))
            
            db.session.commit()
            return True, "Produto adicionado (DB)"
        else:
            # Visitante
            carrinho = session.get('cart', {})
            quantidade_atual = carrinho.get(str(product_id), 0)
            
            if quantidade_atual + 1 > produto.estoque:
                return False, "Estoque insuficiente"
            
            carrinho[str(product_id)] = quantidade_atual + 1
            session['cart'] = carrinho
            session.modified = True
            return True, "Produto adicionado (sessão)"
    
    @staticmethod
    def update_quantity(db, CartItem, product_id, action):
        """
        Atualiza quantidade de um produto no carrinho.
        
        Args:
            action: 'add' ou 'sub'
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if session.get('user_id'):
            user_id = session['user_id']
            item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
            
            if action == 'add':
                if item:
                    item.quantity += 1
                else:
                    db.session.add(CartItem(user_id=user_id, product_id=product_id, quantity=1))
            elif action == 'sub' and item:
                item.quantity -= 1
                if item.quantity <= 0:
                    db.session.delete(item)
            
            db.session.commit()
            return True, "OK"
        else:
            carrinho = session.get('cart', {})
            key = str(product_id)
            
            if action == 'add':
                carrinho[key] = carrinho.get(key, 0) + 1
            elif action == 'sub' and key in carrinho:
                carrinho[key] -= 1
                if carrinho[key] <= 0:
                    del carrinho[key]
            
            session['cart'] = carrinho
            session.modified = True
            return True, "OK"
    
    @staticmethod
    def remove_from_cart(db, CartItem, product_id):
        """Remove produto do carrinho"""
        if session.get('user_id'):
            CartItem.query.filter_by(
                user_id=session['user_id'],
                product_id=product_id
            ).delete()
            db.session.commit()
        else:
            carrinho = session.get('cart', {})
            carrinho.pop(str(product_id), None)
            session['cart'] = carrinho
            session.modified = True
        
        return True, "Produto removido"
