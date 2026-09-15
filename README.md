# 🍯 EJM Santos — Mel Puro e Natural

Site institucional e e-commerce desenvolvido em **Flask**, representando a marca **EJM Santos**, produtora de mel artesanal e natural.

## 🌿 Sobre o Projeto

Projeto completo de e-commerce com arquitetura modular, sistema de segurança robusto, backups automáticos e documentação profissional.

## 📁 Estrutura do Projeto

```
ejm-santos/
├── app/                       # Código da aplicação
│   ├── models/               # Modelos do banco de dados
│   ├── routes/               # Rotas (blueprints)
│   ├── helpers/              # Helpers de carrinho e pedidos
│   └── utils/                # Utilitários (logger, erros, segurança)
│
├── docs/                     # 📚 Documentação completa
│   ├── README.md            # Índice da documentação
│   ├── INSTALACAO.md        # Guia de instalação
│   ├── GUIA_BACKUPS.md      # Sistema de backups
│   ├── SEGURANCA_HTTPS_CSRF.md  # Segurança
│   └── arquivos-de-analise/ # Análises técnicas
│
├── scripts/                  # 🔧 Scripts utilitários
│   ├── backup/              # Gestão de backups
│   ├── database/            # Gestão do banco
│   ├── deployment/          # Scripts de deploy
│   └── maintenance/         # Manutenção
│
├── tests/                    # 🧪 Testes automatizados
│
├── static/                   # Arquivos estáticos (CSS, JS, imagens)
├── templates/                # Templates HTML
├── instance/                 # Banco de dados
├── logs/                     # Logs da aplicação
├── backups/                  # Backups automáticos
│
├── application.py           # 🚀 Aplicação principal
├── wsgi.py                  # Entrada do servidor de produção
├── config.py                # Configurações por ambiente
└── requirements.txt         # Dependências
```

## ✨ Funcionalidades

### Para Clientes
- 🛒 Carrinho de compras persistente
- 💳 Pagamento via Stripe
- 📧 Confirmação de pedido por email
- 👤 Perfil de usuário
- ⭐ Avaliações de produtos

### Para Administradores
- 📊 Dashboard administrativo
- 📦 Gestão de produtos
- 🔍 Gestão de pedidos
- 📸 Upload de imagens
- 📈 Análise de vendas

### Sistema
- 🔒 Segurança HTTPS + CSRF
- 💾 Backups automáticos
- 📝 Sistema de logs
- 🛡️ Tratamento de erros
- ⚡ Rate limiting

## 🚀 Quick Start

### 1. Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ejm-santos.git
cd ejm-santos

# Crie ambiente virtual
python -m venv .venv

# Ative o ambiente
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite .env com suas configurações
```

**Variáveis principais:**
```env
EJM_SECRET=sua_chave_secreta_32_chars
EJM_ADMIN_EMAIL=admin@seu-dominio.com
EJM_ADMIN_PASSWORD=uma_senha_inicial_forte
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
EMAIL_USER=seu@email.com
EMAIL_PASSWORD=senha_de_app
PUBLIC_BASE_URL=https://seu-dominio.com
```

As variáveis `EJM_ADMIN_EMAIL` e `EJM_ADMIN_PASSWORD` são usadas somente
quando ainda não existe administrador. Remova-as do ambiente após o primeiro acesso.

### 3. Inicializar Banco de Dados

```bash
python scripts/database/init_db.py
```

### 4. Executar

```bash
# Desenvolvimento
python application.py

# Produção
gunicorn wsgi:app
```

Acesse: http://localhost:5000

## 💳 Sistema de Pagamento

Integração completa com **Stripe**:

- 🔒 **Seguro**: Tokenização PCI DSS compliant
- ✅ **Validação**: Automática de dados do cartão
- 🌐 **Moedas**: Suporte a Real Brasileiro (BRL)

**Teste com cartão Stripe:**
- Número: `4242 4242 4242 4242`
- CVV: `123`
- Validade: Qualquer data futura

## 📚 Documentação

Toda a documentação está na pasta **[docs/](docs/)**:

- **[INSTALACAO.md](docs/INSTALACAO.md)** - Instalação completa
- **[GUIA_BACKUPS.md](docs/GUIA_BACKUPS.md)** - Sistema de backups
- **[SEGURANCA_HTTPS_CSRF.md](docs/SEGURANCA_HTTPS_CSRF.md)** - Segurança
- **[EMAIL_CONFIG.md](docs/EMAIL_CONFIG.md)** - Configuração de email
- **[STRIPE_CONFIG.md](docs/STRIPE_CONFIG.md)** - Pagamentos

## 🔧 Scripts Úteis

```bash
# Backups
python scripts/backup/backup_manager.py create
python scripts/backup/backup_manager.py list
python scripts/backup/restore_backup.py

# Database
python scripts/database/verificar_db.py
python scripts/database/recriar_db.py

# Testes
python tests/test_security.py
python tests/test_backups.py
```

## 🛡️ Segurança

- ✅ HTTPS Force (produção)
- ✅ Proteção CSRF
- ✅ Rate Limiting
- ✅ Headers de segurança (HSTS, CSP)
- ✅ Validação de inputs
- ✅ Senhas hasheadas
- ✅ Sessões seguras

Veja [docs/SEGURANCA_HTTPS_CSRF.md](docs/SEGURANCA_HTTPS_CSRF.md).

## 💾 Backups

Sistema automatizado:
- Backup de banco de dados SQLite
- Backup de imagens de produtos
- Compressão ZIP
- Rotação automática
- Agendamento diário/semanal
- Restauração interativa

Veja [docs/GUIA_BACKUPS.md](docs/GUIA_BACKUPS.md).

## 🌍 Deploy

### Render (Recomendado)

```yaml
# render.yaml já configurado
services:
  - type: web
    name: ejm-santos
    env: python
    startCommand: "gunicorn wsgi:app"
```

### VPS (Nginx + Gunicorn)

Veja [docs/INSTALACAO.md](docs/INSTALACAO.md) seção de produção.

## 🧪 Testes

```bash
python -m unittest discover -s tests -p "test_*.py"

# Verificações legadas completas
python tests/test_security.py
python tests/test_backups.py
python tests/test_structure.py
```

## 🚀 Tecnologias

- **Flask 2.3.3** - Framework web
- **SQLAlchemy 3.0.3** - ORM
- **Stripe 5.4.0** - Pagamentos
- **Flask-WTF 1.2.1** - CSRF Protection
- **Flask-Limiter 3.5.0** - Rate Limiting
- **Schedule 1.2.0** - Backups automáticos

## 📝 Licença

Este projeto é privado. Todos os direitos reservados.

## 📧 Contato

- Website: https://ejm-santos.com
- Email: contato@ejm-santos.com

---

**🍯 EJM Santos - Mel Natural com Código Natural**

*Desenvolvido com ❤️ e Flask*
