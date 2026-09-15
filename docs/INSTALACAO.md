# 🚀 Instalação Rápida - Sistema de Pagamento com Cartão

## Passo a Passo

### 1️⃣ Instalar Dependências
```powershell
pip install -r requirements.txt
```

### 2️⃣ Configurar Stripe

1. **Criar conta**: https://dashboard.stripe.com/register
2. **Pegar as chaves**: https://dashboard.stripe.com/test/apikeys
3. **Criar arquivo .env** (copie do .env.example):

```env
EJM_SECRET=sua_chave_secreta_aqui
STRIPE_PUBLIC_KEY=pk_test_sua_chave_publica
STRIPE_SECRET_KEY=sk_test_sua_chave_secreta
```

### 3️⃣ Atualizar Banco de Dados

**Se você já tem um banco de dados:**
```powershell
python migrar_db.py
```

**Se é a primeira vez (banco novo):**
```powershell
# Delete o banco antigo (se existir)
rm instance/ejm.db

# Recrie
python init_db.py
```

### 4️⃣ Executar o Servidor
```powershell
python application.py
```

### 5️⃣ Testar

1. Acesse: http://127.0.0.1:5000
2. Adicione produtos ao carrinho
3. Clique em "Finalizar Compra"
4. Use o cartão de teste: **4242 4242 4242 4242**
   - CVV: 123
   - Validade: 12/25
   - Nome: Qualquer nome

## 🎯 Resumo das Mudanças

✅ **Removido**: Mercado Pago  
✅ **Adicionado**: Stripe (pagamento direto com cartão)  
✅ **Novo**: Página de checkout com formulário de cartão  
✅ **Novo**: Validação automática do cartão  
✅ **Novo**: Processamento seguro via Stripe  

## 📝 Principais Arquivos Modificados

- `app.py` - Endpoints de pagamento atualizados
- `requirements.txt` - Stripe ao invés de mercadopago
- `templates/checkout.html` - Nova página com formulário
- `templates/carrinho.html` - Botão atualizado
- `init_db.py` - Removido campo mercado_pago_link

## ❓ Problemas?

Consulte o arquivo **STRIPE_CONFIG.md** para documentação completa.
