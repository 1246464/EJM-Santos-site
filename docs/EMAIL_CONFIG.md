# 📧 Configuração de Email - EJM Santos

## Sistema de Emails Implementado

O sistema agora envia emails automáticos para:

1. **✅ Cadastro** - Email de boas-vindas quando um novo usuário se registra
2. **📦 Pedido Criado** - Confirmação quando um pedido é realizado
3. **🔄 Status Atualizado** - Notificação quando o admin muda o status do pedido (Pago, Enviado, Entregue, etc)

---

## Como Configurar

### 1. Usando Gmail (Recomendado)

#### Passo 1: Ativar Verificação em Duas Etapas
1. Acesse: https://myaccount.google.com/security
2. Role até "Verificação em duas etapas"
3. Clique em "Começar" e siga as instruções
4. Configure um método de verificação (SMS ou app)

#### Passo 2: Gerar Senha de App
1. Acesse: https://myaccount.google.com/apppasswords
2. No campo "Selecione o app", escolha **"Email"**
3. No campo "Selecione o dispositivo", escolha **"Outro (nome personalizado)"**
4. Digite: **"EJM Santos Loja"**
5. Clique em **"Gerar"**
6. **Copie a senha de 16 caracteres** que aparecer

#### Passo 3: Configurar no .env
Abra seu arquivo `.env` e adicione:

```env
# Configurações de Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Cole a senha de app gerada (sem espaços)
EMAIL_FROM_NAME=EJM Santos - Mel Natural
```

**⚠️ IMPORTANTE:** Use a senha de APP gerada, NÃO sua senha normal do Gmail!

---

### 2. Usando Outlook/Hotmail

Adicione no seu `.env`:

```env
# Configurações de Email
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USER=seu_email@outlook.com
EMAIL_PASSWORD=sua_senha_normal_outlook
EMAIL_FROM_NAME=EJM Santos - Mel Natural
```

**Obs:** Com Outlook, você pode usar sua senha normal (não precisa senha de app).

---

### 3. Usando Outro Provedor

Para outros provedores (Yahoo, iCloud, etc), você precisa descobrir:
- Endereço do servidor SMTP
- Porta (geralmente 587)
- Se requer senha de app ou não

---

## Testando o Sistema

### 1. Testar Email de Cadastro
```bash
# Inicie o servidor
python application.py

# Acesse http://127.0.0.1:5000/login
# Clique em "Criar conta"
# Preencha o formulário com um email válido
# Verifique sua caixa de entrada
```

### 2. Testar Email de Pedido
```bash
# Faça login
# Adicione produtos ao carrinho
# Finalize a compra
# Verifique o email de confirmação
```

### 3. Testar Atualização de Status
```bash
# Faça login como admin (http://127.0.0.1:5000/admin/login)
# Vá em "Pedidos"
# Selecione um pedido
# Mude o status (ex: Pendente → Pago)
# O cliente receberá um email notificando
```

---

## Verificando se Está Funcionando

Ao iniciar o servidor, você verá mensagens no console:

```
✅ Email enviado com sucesso para usuario@email.com
```

Ou, se não configurado:

```
⚠️ Configuração de email não encontrada. Email não enviado.
```

---

## Personalização dos Emails

Os templates de email estão em `email_service.py`. Você pode editar:

- **Layout HTML** - Cores, estilos, logos
- **Mensagens** - Textos de cada tipo de email
- **Links** - Ajuste os links para apontar para seu domínio em produção

### Exemplo: Mudar a Cor Principal

Em `email_service.py`, procure por `background: #f6b800` e mude para sua cor preferida.

---

## Problemas Comuns

### ❌ "Erro ao enviar email: (535) Username and Password not accepted"
**Solução:** 
- Verifique se ativou verificação em duas etapas (Gmail)
- Certifique-se de usar a senha de APP, não a senha normal
- Confira se copiou toda a senha (16 caracteres)

### ❌ "Erro ao enviar email: Connection refused"
**Solução:**
- Verifique o servidor SMTP e porta
- Teste sua conexão de internet
- Alguns antivírus bloqueiam porta 587

### ❌ "Configuração de email não encontrada"
**Solução:**
- Verifique se o arquivo `.env` existe
- Confirme que as variáveis EMAIL_USER e EMAIL_PASSWORD estão definidas
- Reinicie o servidor após editar o `.env`

### ⚠️ Email vai para Spam
**Solução:**
- Use um email profissional (não @gmail.com pessoal)
- Configure SPF, DKIM, DMARC no seu domínio (avançado)
- Peça aos clientes para adicionar seu email aos contatos

---

## Produção (Render/Heroku)

Ao fazer deploy, adicione as variáveis de ambiente no painel:

**Render:**
1. Vá em "Environment"
2. Adicione cada variável (EMAIL_USER, EMAIL_PASSWORD, etc)
3. Clique em "Save Changes"

**Heroku:**
```bash
heroku config:set EMAIL_USER=seu_email@gmail.com
heroku config:set EMAIL_PASSWORD=sua_senha_app
heroku config:set SMTP_SERVER=smtp.gmail.com
heroku config:set SMTP_PORT=587
```

---

## Recursos Avançados (Futuro)

- 📧 **Templates profissionais** - Usar serviços como SendGrid, Mailgun
- 📊 **Analytics** - Rastrear abertura e cliques
- 🔔 **Notificações** - SMS, WhatsApp
- 📝 **Newsletters** - Campanhas de marketing

---

## Suporte

Se tiver problemas, verifique:
1. ✅ Arquivo `.env` está configurado corretamente
2. ✅ Servidor SMTP está correto para seu provedor
3. ✅ Senha de app foi gerada (para Gmail)
4. ✅ Console mostra mensagens de log
5. ✅ Firewall/Antivírus não está bloqueando

**Logs úteis:**
- `✅ Email enviado com sucesso` - Funcionou!
- `⚠️ Configuração não encontrada` - Falta configurar .env
- `❌ Erro ao enviar` - Problema de credenciais ou conexão
