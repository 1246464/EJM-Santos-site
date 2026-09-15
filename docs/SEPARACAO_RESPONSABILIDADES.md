# ============================================
# DOCUMENTAÇÃO: SEPARAÇÃO DE RESPONSABILIDADES
# ============================================

# 📂 Estrutura do Projeto Refatorado

## 🎯 Objetivo
Separar responsabilidades do app.py monolítico (1037 linhas) em módulos especializados.

## 📁 Nova Estrutura

```
ejm-santos/
├── app.py                      # ⚙️ Configuração e inicialização (150 linhas)
├── app/
│   ├── models/                # 📊 Modelos de Banco de Dados
│   │   ├── __init__.py       # Exportações
│   │   ├── user.py           # Modelo User
│   │   ├── product.py        # Modelo Product
│   │   ├── order.py          # Modelos Order e OrderItem
│   │   ├── review.py         # Modelo Review
│   │   └── cart.py           # Modelo CartItem
│   │
│   ├── routes/                # 🛣️ Rotas (Blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py           # Autenticação (login, registro)
│   │   ├── admin.py          # Administração (produtos, pedidos)
│   │   ├── products.py       # Produtos (listagem, detalhes, API)
│   │   └── payment.py        # 💳 Pagamento (checkout, Stripe)
│   │
│   ├── helpers/               # 🔧 Funções Auxiliares
│   │   ├── __init__.py
│   │   ├── cart_helper.py    # Lógica do carrinho
│   │   └── order_helper.py   # Lógica de pedidos
│   │
│   └── utils/                 # 🛠️ Utilidades
│       ├── logger.py          # Sistema de logging
│       ├── validators.py      # Validações
│       ├── exceptions.py      # Exceções customizadas
│       └── error_handlers.py  # Tratamento de erros
│
├── email_service.py           # 📧 Serviço de email
├── templates/                 # 🎨 Templates HTML
└── static/                    # 📦 Arquivos estáticos
```

## 📊 Comparação: Antes vs Depois

### Antes (Monolítico)
- **app.py**: 1037 linhas
  - Modelos: ~120 linhas
  - Helpers: ~80 linhas
  - Rotas de Auth: ~50 linhas
  - Rotas de Admin: ~150 linhas
  - Rotas de Produtos: ~200 linhas
  - Rotas de Carrinho: ~100 linhas
  - Rotas de Pagamento: ~150 linhas
  - APIs: ~187 linhas

### Depois (Modular)
- **application.py**: configuração, extensões e registro dos blueprints
- **models/**: 6 arquivos (~40 linhas cada)
- **routes/**: 4 blueprints (auth, admin, products, payment)
- **helpers/**: 2 helpers (cart, order)
- **utils/**: já existentes (logger, validators, etc.)

## 🎯 Benefícios da Refatoração

### 1. **Manutenibilidade** 📝
- ✅ Arquivos pequenos e focados
- ✅ Fácil encontrar código específico
- ✅ Mudanças isoladas não afetam todo o sistema

### 2. **Escalabilidade** 📈
- ✅ Fácil adicionar novos recursos
- ✅ Novos blueprints sem impacto
- ✅ Modelos independentes

### 3. **Testabilidade** 🧪
- ✅ Testes unitários por módulo
- ✅ Mocks mais fáceis
- ✅ Cobertura de código clara

### 4. **Trabalho em Equipe** 👥
- ✅ Menos conflitos no Git
- ✅ Cada dev em um módulo
- ✅ Code review mais fácil

### 5. **Organização** 🗂️
- ✅ Responsabilidades claras
- ✅ Single Responsibility Principle
- ✅ Código mais limpo

## 🔄 Estado Atual

A migração modular está concluída. Use `python application.py` em desenvolvimento
e `gunicorn wsgi:app` em produção.

## 📋 Checklist de Migração

- [x] ✅ Modelos separados em `app/models/`
- [x] ✅ Helpers criados em `app/helpers/`
- [x] ✅ Blueprint de pagamento em `app/routes/payment.py`
- [x] ✅ `application.py` criado e configurado
- [ ] ⏳ Testar todas as rotas
- [ ] ⏳ Verificar autenticação
- [ ] ⏳ Testar carrinho e checkout
- [ ] ⏳ Testar área admin
- [ ] ⏳ Verificar emails
- [x] ✅ Ponto de entrada de produção definido em `wsgi.py`

## 🎓 Padrões Utilizados

### 1. **Blueprint Pattern**
Rotas organizadas em módulos independentes que são registrados na aplicação principal.

### 2. **Factory Pattern**
Funções `init_*()` para inicializar blueprints com dependências.

### 3. **Helper/Service Pattern**
Lógica de negócio separada das rotas (CartHelper, OrderHelper).

### 4. **Repository Pattern**
Modelos encapsulam acesso aos dados.

### 5. **Dependency Injection**
Blueprints recebem dependências via `init_*()`.

## 🚀 Próximos Passos

1. **Expandir os testes de `application.py`**
2. **Criar testes automatizados** para cada módulo
3. **Documentar APIs** (Swagger/OpenAPI)
4. **Adicionar type hints** (Python 3.10+)
5. **CI/CD Pipeline** com testes automáticos

## 📖 Exemplos de Uso

### Adicionar Nova Rota de Produto

```python
# Em app/routes/products.py

@products_bp.route("/api/produtos/destaque")
def produtos_destaque():
    """Retorna produtos em destaque"""
    produtos = Product.query.filter_by(destaque=True).all()
    return jsonify([p.to_dict() for p in produtos])
```

### Criar Novo Helper

```python
# Em app/helpers/discount_helper.py

class DiscountHelper:
    @staticmethod
    def apply_discount(order, discount_code):
        # Lógica de desconto
        pass
```

### Adicionar Novo Modelo

```python
# Em app/models/coupon.py

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    discount = db.Column(db.Float)
```

## 🔗 Documentação Relacionada

- `TRATAMENTO_ERROS.md` - Sistema de erros
- `RESUMO_TRATAMENTO_ERROS.md` - Guia rápido de erros
- `README.md` - Documentação geral do projeto

---

**Data**: 04/02/2026  
**Status**: ✅ Implementado e Documentado  
**Autor**: Sistema de Refatoração
