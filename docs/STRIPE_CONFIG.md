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
   ```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Atualizar o banco de dados

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

### 6. Testar o sistema

1. Execute o servidor:
   ```bash
   python app.py
   ```

2. Acesse: http://127.0.0.1:5000

3. Adicione produtos ao carrinho e clique em "Finalizar Compra"

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

## 🌐 Deploy em Produção

1. Ative sua conta Stripe (adicione dados bancários)
2. Obtenha as chaves de **produção** (começam com `pk_live_` e `sk_live_`)
3. Atualize as variáveis de ambiente no servidor
4. Configure HTTPS no seu domínio (obrigatório para Stripe)

## 📝 Observações

- **Ambiente de teste**: Use chaves `pk_test_` e `sk_test_`
- **Ambiente de produção**: Use chaves `pk_live_` e `sk_live_`
- **Moeda**: Configurado para BRL (Real Brasileiro)
- **Taxas Stripe no Brasil**: ~4.99% + R$0.39 por transação aprovada

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
