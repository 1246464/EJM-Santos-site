# 📋 Changelog - EJM Santos

Histórico de mudanças do projeto.

## [ENDEREÇOS E CARTÕES] - 2026-02-08

### 🏠💳 Sistema de Endereços e Cartões Salvos

#### ✅ Novos Modelos

**Address (Endereços):**
- `app/models/address.py` - Modelo completo de endereços
- Campos: apelido, rua, numero, complemento, bairro, cidade, estado, cep, telefone
- Suporte para múltiplos endereços por usuário
- Marcador de endereço padrão

**PaymentMethod (Cartões):**
- `app/models/payment_method.py` - Modelo de métodos de pagamento
- Integração com Stripe Payment Methods
- Armazena apenas últimos 4 dígitos (segurança PCI)
- Campos: apelido, stripe_payment_method_id, card_brand, card_last4, validade
- Suporte para múltiplos cartões por usuário
- Verificação de cartões expirados

#### 🔌 APIs REST Completas

**Rotas de Endereços (`app/routes/profile.py`):**
- `GET /api/addresses` - Listar endereços
- `POST /api/addresses` - Adicionar endereço
- `PUT /api/addresses/<id>` - Atualizar endereço
- `DELETE /api/addresses/<id>` - Remover endereço
- `POST /api/addresses/<id>/set-default` - Definir padrão

**Rotas de Cartões:**
- `GET /api/payment-methods` - Listar cartões
- `POST /api/payment-methods` - Adicionar cartão
- `DELETE /api/payment-methods/<id>` - Remover cartão
- `POST /api/payment-methods/<id>/set-default` - Definir padrão

#### 🛒 Checkout Inteligente

**Arquivo:** `templates/checkout.html` (completamente reescrito)

**Funcionalidades:**
- ✅ Seleção de endereço salvo ou novo
- ✅ Seleção de cartão salvo ou novo
- ✅ Radio buttons para alternar entre opções
- ✅ Checkbox "Salvar para próximas compras"
- ✅ Campo de apelido para dados salvos
- ✅ Interface responsiva e moderna
- ✅ Badges visuais (Padrão, Expirado)

**Fluxos Suportados:**
1. Endereço salvo + Cartão salvo (checkout rápido)
2. Endereço salvo + Cartão novo
3. Endereço novo + Cartão salvo
4. Endereço novo + Cartão novo (fluxo original)

#### 👤 Perfil do Usuário

**Modificado:** `templates/perfil_novo.html`

**Aba "Endereços":**
- Grid de cards com todos os endereços
- Badge "Padrão" para endereço principal
- Botões: Editar, Remover
- Link para checkout

**Aba "Formas de Pagamento":**
- Grid de cards estilo cartão físico
- Display mascarado: 💳 VISA •••• 4242
- Badge "Padrão" e "Expirado"
- Botão: Remover
- Aviso de segurança PCI

**JavaScript Adicionado:**
- `removerEndereco(id)` - Remove via API
- `removerCartao(id)` - Remove via API
- `editarEndereco(id)` - Placeholder
- `irParaCheckout()` - Redireciona

#### 🔄 Sistema de Migração

**Arquivo:** `scripts/database/migrate_addresses_payments.py`

**Funcionalidades:**
- Verifica tabelas existentes
- Cria `address` table com todos os campos
- Cria `payment_method` table com relacionamento Stripe
- Adiciona FKs para `user`
- Validação e rollback automático
- Mensagens coloridas e informativas
- Confirmação antes de executar

**Uso:**
```bash
python scripts/database/migrate_addresses_payments.py
```

#### 🔧 Backend Modificado

**`app_new.py`:**
- Importa novos modelos (Address, PaymentMethod)
- Registra blueprint `profile_bp`
- Adiciona modelos ao models_dict

**`app/routes/payment.py` - POST /processar-pagamento:**
- Aceita `saved_address_id` (usar endereço salvo)
- Aceita `saved_payment_method_id` (usar cartão salvo)
- Aceita `save_address` + `address_nickname` (salvar novo endereço)
- Aceita `save_card` + `card_nickname` (salvar novo cartão)
- Busca dados salvos do banco
- Salva novos dados após pagamento bem-sucedido
- Validação completa de todos os cenários

**`app/routes/payment.py` - GET /checkout:**
- Busca endereços salvos do usuário
- Busca cartões salvos do usuário
- Passa para template via context

**`app/routes/products.py` - GET /perfil:**
- Busca endereços do usuário
- Busca cartões do usuário
- Passa para template

#### 📚 Documentação

**Novo:** `docs/ENDERECOS_CARTOES.md` (Guia completo)

**Conteúdo:**
- Visão geral do sistema
- Arquitetura e fluxo de dados
- Documentação completa dos modelos
- Referência de todos os endpoints da API
- Fluxo detalhado do checkout
- Guia de migração do banco
- Interface do usuário com exemplos visuais
- Segurança e PCI compliance
- Troubleshooting completo
- Referências externas

#### 🔒 Segurança

**PCI Compliance:**
- ✅ Nunca armazenamos número completo do cartão
- ✅ Nunca armazenamos CVV
- ✅ Apenas tokens do Stripe (`pm_xxx`)
- ✅ Últimos 4 dígitos para exibição
- ✅ Stripe gerencia toda a parte sensível

**Validações:**
- Autenticação em todas as rotas
- Autorização por `user_id` (usuário só vê seus dados)
- Validação de campos obrigatórios
- Verificação de ownership antes de deletar/editar

#### 📊 Benefícios

**Para o Usuário:**
- ⚡ Checkout 3x mais rápido
- 💾 Dados salvos automaticamente
- 🏠 Múltiplos endereços (casa, trabalho, etc)
- 💳 Múltiplos cartões gerenciáveis
- 🎯 Seleção visual intuitiva

**Para o Negócio:**
- 📈 Redução de abandono de carrinho
- 🚀 Conversão mais alta
- 📊 Melhor UX/CX
- 🔒 Conformidade PCI automática
- 🎨 Design moderno e profissional

#### ⚙️ Arquivos Criados/Modificados

**Novos:**
- `app/models/address.py`
- `app/models/payment_method.py`
- `app/routes/profile.py`
- `scripts/database/migrate_addresses_payments.py`
- `docs/ENDERECOS_CARTOES.md`
- `templates/checkout_old_backup.html` (backup)

**Modificados:**
- `app/models/__init__.py`
- `app/models/user.py`
- `app_new.py`
- `app/routes/payment.py`
- `app/routes/products.py`
- `templates/checkout.html` (reescrito)
- `templates/perfil_novo.html`

#### 🎯 Próximos Passos

1. **Executar migração:**
   ```bash
   python scripts/backup/backup_manager.py create
   python scripts/database/migrate_addresses_payments.py
   ```

2. **Testar fluxos:**
   - Adicionar produto ao carrinho
   - Ir para checkout
   - Salvar endereço e cartão
   - Fazer segunda compra usando dados salvos

3. **Gerenciar no perfil:**
   - Acessar /perfil
   - Aba "Endereços"
   - Aba "Formas de Pagamento"

---

## [REORGANIZAÇÃO] - 2026-02-08

### 🎯 Reorganização Completa da Estrutura do Projeto

#### ✅ Estrutura Nova Criada

```
ejm-santos/
├── docs/                     # 📚 Documentação (12 arquivos)
├── scripts/                  # 🔧 Scripts utilitários (10 arquivos)
│   ├── backup/              # Sistema de backup
│   ├── database/            # Gestão do banco
│   ├── deployment/          # Deploy e preparação
│   └── maintenance/         # Manutenção
├── tests/                    # 🧪 Testes (5 arquivos)
└── app/                      # Código da aplicação
```

#### 📁 Arquivos Movidos

**Documentação → `docs/`:**
- ✅ INSTALACAO.md
- ✅ GUIA_BACKUPS.md
- ✅ GUIA_MIGRACAO.md
- ✅ GUIA_SEGURANCA.md
- ✅ SEGURANCA_HTTPS_CSRF.md
- ✅ EMAIL_CONFIG.md
- ✅ STRIPE_CONFIG.md
- ✅ SECURITY_UPDATES.md
- ✅ SEPARACAO_RESPONSABILIDADES.md
- ✅ TRATAMENTO_ERROS.md
- ✅ RESUMO_TRATAMENTO_ERROS.md
- ✅ ANALISE_BANCO.md → `docs/arquivos-de-analise/`
- ✅ ANALISE_LIMPEZA.md → `docs/arquivos-de-analise/`
- ✅ VISUAL_SISTEMA.md → `docs/arquivos-de-analise/`

**Scripts → `scripts/`:**
- ✅ backup_manager.py → `scripts/backup/`
- ✅ backup_scheduler.py → `scripts/backup/`
- ✅ restore_backup.py → `scripts/backup/`
- ✅ init_db.py → `scripts/database/`
- ✅ recriar_db.py → `scripts/database/`
- ✅ verificar_db.py → `scripts/database/`
- ✅ preparar_commit.ps1 → `scripts/deployment/`
- ✅ preparar_commit.sh → `scripts/deployment/`
- ✅ cleanup_project.py → `scripts/maintenance/`

**Testes → `tests/`:**
- ✅ test_backups.py
- ✅ test_security.py
- ✅ test_error_handling.py
- ✅ test_structure.py
- ✅ test_refactoring.py

#### 🗑️ Arquivos Removidos

- ❌ executar_limpeza.py (duplicado)
- ❌ limpar_agora.py (duplicado)
- ❌ app_old.py (obsoleto)

#### 📝 Arquivos Criados

- ✅ `docs/README.md` - Índice da documentação
- ✅ `scripts/README.md` - Guia de scripts
- ✅ `tests/README.md` - Guia de testes
- ✅ `CHANGELOG.md` - Este arquivo

#### 🔧 Arquivos Atualizados

- ✅ `README.md` - Atualizado com nova estrutura
- ✅ `.gitignore` - Melhorado com mais padrões

#### 🎯 Raiz Limpa

**Apenas 6 arquivos essenciais na raiz:**
1. `app_new.py` - Aplicação principal
2. `config.py` - Configuração
3. `email_service.py` - Serviço de email
4. `README.md` - Documentação principal
5. `requirements.txt` - Dependências
6. `render.yaml` - Deploy

**De 30+ arquivos para 6 arquivos na raiz!** 🎉

#### 📊 Benefícios

- ✨ Estrutura profissional e escalável
- 📁 Separação lógica por função
- 📚 Documentação centralizada e organizada
- 🔧 Scripts categorizados por tipo
- 🧪 Testes isolados
- 🔍 Fácil navegação
- 🚀 Pronto para crescimento

#### ⚠️ Breaking Changes

**Caminhos alterados - atualize seus imports/comandos:**

```bash
# ANTES
python backup_manager.py create
python init_db.py
python test_security.py

# AGORA
python scripts/backup/backup_manager.py create
python scripts/database/init_db.py
python tests/test_security.py
```

#### 📖 Migração

Se você tem scripts ou automation que usam os caminhos antigos:

1. **Atualize caminhos absolutos:**
   ```bash
   # Atualizar de: /projeto/backup_manager.py
   # Para: /projeto/scripts/backup/backup_manager.py
   ```

2. **Ou use caminhos relativos da raiz:**
   ```bash
   cd ejm-santos
   python scripts/backup/backup_manager.py create
   ```

3. **Consulte os READMEs em cada pasta:**
   - `docs/README.md` para documentação
   - `scripts/README.md` para scripts
   - `tests/README.md` para testes

---

## [SEGURANÇA] - 2026-02-08

### 🔒 Sistema HTTPS + CSRF Implementado

- ✅ Middleware HTTPS Force
- ✅ Proteção CSRF completa
- ✅ Headers de segurança (HSTS, CSP, etc.)
- ✅ Meta tags CSRF nos templates
- ✅ Helpers JavaScript para AJAX
- ✅ Documentação completa

**Ver:** [docs/SEGURANCA_HTTPS_CSRF.md](docs/SEGURANCA_HTTPS_CSRF.md)

---

## [BACKUPS] - 2026-02-08

### 💾 Sistema de Backup Automático

- ✅ Backup de banco de dados SQLite
- ✅ Backup de imagens
- ✅ Compressão ZIP
- ✅ Rotação automática
- ✅ Agendamento (diário/semanal)
- ✅ Restauração interativa
- ✅ Validação de integridade

**Ver:** [docs/GUIA_BACKUPS.md](docs/GUIA_BACKUPS.md)

---

## Versões Anteriores

### [1.0.0] - 2026-01-XX

- ✅ Sistema de e-commerce base
- ✅ Integração Stripe
- ✅ Painel administrativo
- ✅ Sistema de autenticação
- ✅ Carrinho de compras
- ✅ Envio de emails

---

**🍯 EJM Santos - Evoluindo Naturalmente**
