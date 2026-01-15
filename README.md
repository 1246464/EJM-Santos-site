# 🍯 EJM Santos — Mel Puro e Natural

Site institucional e e-commerce desenvolvido em **Flask**, representando a marca **EJM Santos**, produtora de mel artesanal e natural.

## 🌿 Sobre o Projeto
O projeto foi criado com o objetivo de apresentar os produtos da marca **EJM Santos** de forma clara e moderna, transmitindo a identidade natural e artesanal do mel produzido.

A estrutura do site inclui uma página inicial com destaque visual, catálogo de produtos, carrinho de compras e **sistema de pagamento direto com cartão de crédito** via Stripe.

## 🧩 Estrutura do Site
- **Home (index.html):** Apresentação da marca e chamada para ação "Ver Produtos".  
- **Produtos:** Catálogo completo de tipos de mel com imagem, descrição e preços.  
- **Carrinho de Compras:** Gestão de itens antes da finalização.  
- **Checkout:** Formulário seguro para pagamento com cartão de crédito.  
- **Painel Admin:** Gerenciamento de produtos e pedidos.  
- **Banco de dados:** SQLite via Flask SQLAlchemy para produtos, usuários e pedidos.  
- **Pagamento:** Integração com **Stripe** para processar cartões de crédito.

## 🚀 Tecnologias Utilizadas
- **Python + Flask**
- **HTML5 e Jinja2**
- **CSS3**
- **SQLite** (banco de dados)
- **Stripe** (processamento de pagamentos)
- **JWT** (autenticação)

## 🧾 Funcionalidades Principais
- ✅ Catálogo de produtos com sistema de avaliações
- ✅ Carrinho de compras persistente  
- ✅ Sistema de login e cadastro de usuários
- ✅ **Pagamento direto com cartão de crédito** (Stripe)
- ✅ Validação automática de dados do cartão
- ✅ Painel administrativo para gestão
- ✅ Histórico de pedidos do usuário
- ✅ Design responsivo e moderno

## 💳 Sistema de Pagamento

O site agora possui integração completa com **Stripe** para processar pagamentos com cartão:

- 🔒 **Seguro**: Tokenização no lado do cliente (PCI DSS compliant)
- ✅ **Fácil**: Interface intuitiva para inserir dados do cartão
- 🌐 **Moedas**: Suporte a Real Brasileiro (BRL)
- 🎯 **Validação**: Verificação automática de dados do cartão

## ⚙️ Como Rodar Localmente

### 1. Clonar e Configurar Ambiente
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Stripe
1. Crie conta gratuita: https://dashboard.stripe.com/register
2. Pegue suas chaves de teste: https://dashboard.stripe.com/test/apikeys
3. Copie `.env.example` para `.env`
4. Adicione suas chaves no `.env`:
```env
STRIPE_PUBLIC_KEY=pk_test_sua_chave
STRIPE_SECRET_KEY=sk_test_sua_chave
```

### 3. Inicializar Banco de Dados
```bash
python init_db.py
```

### 4. Executar
```bash
python app.py
```

### 5. Testar Pagamento
Use o cartão de teste do Stripe:
- **Número**: 4242 4242 4242 4242
- **CVV**: 123
- **Validade**: Qualquer data futura

## 📚 Documentação Adicional

- **[INSTALACAO.md](INSTALACAO.md)** - Guia rápido de instalação
- **[STRIPE_CONFIG.md](STRIPE_CONFIG.md)** - Documentação completa do Stripe
- **[LEIA_ME_PRIMEIRO.py](LEIA_ME_PRIMEIRO.py)** - Próximos passos após clone

## 🔄 Migrando do Mercado Pago

Se você tinha uma versão anterior com Mercado Pago, execute:
```bash
python migrar_db.py
```

Isso removerá o campo `mercado_pago_link` do banco de dados.

## 🌐 Deploy

O projeto está configurado para deploy no **Render** ou similar. Não esqueça de:
1. Configurar as variáveis de ambiente (chaves do Stripe)
2. Usar chaves de **produção** (`pk_live_` e `sk_live_`)
3. Habilitar HTTPS (obrigatório para Stripe)

## 📝 Licença

Este projeto foi desenvolvido para **EJM Santos** como exemplo educacional.

---

**Desenvolvido com 🍯 e Python**
