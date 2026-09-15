# 🔧 Guia de Configuração do Stripe

## O que mudou?

✅ **Removido**: Sistema de pagamento com Mercado Pago  
✅ **Adicionado**: Sistema de pagamento direto com cartão de crédito usando Stripe

## Como configurar o Stripe

### 1. Criar conta no Stripe

1. Acesse: https://dashboard.stripe.com/register
2. Crie sua conta gratuita
3. Complete o cadastro básico

### 2. Obter as chaves de API

1. Acesse o Dashboard: https://dashboard.stripe.com/test/apikeys
2. Você verá duas chaves:
   - **Publishable key** (começa com `pk_test_...`)
   - **Secret key** (começa com `sk_test_...`)

### 3. Configurar o projeto

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas chaves do Stripe:
   ```
   STRIPE_PUBLIC_KEY=pk_test_sua_chave_aqui
   STRIPE_SECRET_KEY=sk_test_sua_chave_aqui
   STRIPE_WEBHOOK_SECRET=whsec_seu_segredo_aqui
   ```

### 4. Configurar o webhook do aplicativo

No Workbench/Dashboard do Stripe, crie um endpoint apontando para:

```text
https://SEU-DOMINIO/api/mobile/payments/stripe/webhook
```

Marque estes eventos:

- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.canceled`

Copie o segredo de assinatura desse endpoint, iniciado por `whsec_`, para
`STRIPE_WEBHOOK_SECRET`. O segredo do webhook criado pelo Stripe CLI é diferente
do segredo do endpoint de produção.

### 5. Instalar dependências

```bash
pip install -r requirements.txt
```

### 6. Atualizar o banco de dados

Como removemos o campo `mercado_pago_link` da tabela `Product`, você precisa atualizar o banco:

**Opção 1 - Recriar o banco (apaga todos os dados):**
```bash
# Delete o banco existente
rm instance/ejm.db

# Recrie o banco
python init_db.py
```

**Opção 2 - Migração manual (preserva dados):**
```sql
-- Execute no SQLite
ALTER TABLE product DROP COLUMN mercado_pago_link;
```

### 7. Testar o sistema

1. Execute o servidor:
   ```bash
   python application.py
   ```

2. Acesse: http://127.0.0.1:5000

3. No aplicativo, adicione produtos ao carrinho, selecione "Cartão pelo Stripe"
   e toque em "Pagar com cartão"

4. Use cartões de teste do Stripe:
   - **Sucesso**: `4242 4242 4242 4242`
   - **Falha**: `4000 0000 0000 0002`
   - **CVV**: Qualquer 3 dígitos (ex: 123)
   - **Data**: Qualquer data futura (ex: 12/25)

## 📋 Cartões de teste completos

| Cenário | Número do Cartão | Resultado |
|---------|------------------|-----------|
| Pagamento aprovado | 4242 4242 4242 4242 | ✅ Sucesso |
| Cartão recusado | 4000 0000 0000 0002 | ❌ Recusado |
| Fundos insuficientes | 4000 0000 0000 9995 | ❌ Sem fundos |
| CVC incorreto | 4000 0000 0000 0127 | ❌ Erro CVC |

Mais cartões de teste: https://stripe.com/docs/testing#cards

## 🔒 Segurança

- ✅ O Stripe tokeniza os dados do cartão no navegador
- ✅ Os dados sensíveis nunca passam pelo seu servidor
- ✅ Conformidade PCI DSS automática
- ✅ Criptografia SSL/TLS em todas as transações
- ✅ O backend recalcula preço, frete e estoque antes de criar o PaymentIntent
- ✅ Apenas o webhook com assinatura válida altera o pedido para `Pago`
- ✅ A chave secreta e o segredo do webhook nunca são enviados ao aplicativo

## 🌐 Deploy em Produção

1. Ative sua conta Stripe (adicione dados bancários)
2. Obtenha as chaves de **produção** (começam com `pk_live_` e `sk_live_`)
3. Atualize as variáveis de ambiente no servidor
4. Crie um webhook de produção e configure seu novo `whsec_`
5. Configure HTTPS no seu domínio
6. Faça uma compra real de valor baixo e confirme o pedido no painel administrativo

## 📝 Observações

- **Ambiente de teste**: Use chaves `pk_test_` e `sk_test_`
- **Ambiente de produção**: Use chaves `pk_live_` e `sk_live_`
- **Moeda**: Configurado para BRL (Real Brasileiro)
- **Taxas**: consulte a página de preços da sua conta Stripe; elas podem mudar

## 🆘 Problemas comuns

**Erro "No such token"**
- Verifique se a chave pública está correta no template

**Erro "Invalid API Key"**
- Verifique se a chave secreta está correta no `.env`

**Cartão não é aceito**
- No modo teste, use apenas os cartões de teste do Stripe

**Página de checkout não carrega**
- Verifique se instalou a biblioteca: `pip install stripe`
- Confira se as chaves estão no arquivo `.env`

## 📚 Documentação Stripe

- Documentação oficial: https://stripe.com/docs
- API Reference: https://stripe.com/docs/api
- Dashboard: https://dashboard.stripe.com
