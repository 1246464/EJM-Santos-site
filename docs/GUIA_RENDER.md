# 🚀 Configuração no Render

## ⚠️ IMPORTANTE: SQLite não funciona no Render!

O Render tem sistema de arquivos **efêmero** (apaga a cada deploy).  
**Você PRECISA usar PostgreSQL** para dados persistentes.

## ✅ Passo 1: Adicionar PostgreSQL no Render

### 1.1 No Dashboard do Render:
1. Clique em **"New +"** → **"PostgreSQL"**
2. Preencha:
   - **Name**: `ejm-santos-db`
   - **Database**: `ejm_santos`
   - **User**: `ejm_santos_user`
   - **Region**: Mesma do seu web service
   - **Plan**: Free (adequado para começar)
3. Clique em **"Create Database"**

### 1.2 Aguarde a criação (~2min):
- Status ficará **"Available"**
- Copie a **"Internal Database URL"** (começa com `postgres://`)

### 1.3 Conectar ao Web Service:
1. Vá no seu web service (`ejm-santos-site`)
2. **Environment** → **Add Environment Variable**
3. Nome: `DATABASE_URL`
4. Valor: Cole a Internal Database URL
5. **Save Changes**

O formato será:
```
postgres://ejm_santos_user:senha@dpg-xxxxx/ejm_santos
```

## ✅ Passo 2: Configurar SECRET_KEY (Opcional mas Recomendado)

Para **persistir sessões** entre restarts:

### Dashboard Render → Web Service → Environment

```bash
EJM_SECRET=<cole_a_chave_abaixo>
```

**Gere uma chave segura:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Exemplo:
```
EJM_SECRET=5043a2b89a10c3d4b15a5858c566194ce3fee12d5f045103f1f0bb828ec78936
```

## 4. Testar o Login

Acesse: `https://seu-app.onrender.com/login`

Use os valores seguros definidos em `EJM_ADMIN_EMAIL` e
`EJM_ADMIN_PASSWORD`. Nunca registre a senha no repositório ou neste guia.

**⚠5. Diagnóstico

Acesse: `https://seu-app.onrender.com/diagnostico`

**Deve mostrar:**
```json
{
  "sistema": "EJM Santos",
  "status": "OK",
  "checks": {
    "database": {
      "status": "✅ conectado",
      "usuarios": 1,
      "admin_cadastrado": "✅ sim",
      "produtos": 0
    }
  }
}
```

## 6. Troubleshooting

### ❌ "unable to open database file"

**Causa**: Tentando usar SQLite (não funciona no Render)

**Solução**: 
1. Adicione PostgreSQL (Passo 1)
2. Configure `DATABASE_URL` (Passo 1.3)
3. Faça novo deploy

### ❌ "Erro ao processar login" após adicionar PostgreSQL

**Causa**: Banco vazio, admin não existe

**Solução**: Aguarde o build terminar. O `init_render.py` cria o admin automaticamente.

### ⚠️ Logs mostram "SQLite" ao invés de "PostgreSQL"

**Causa**: `DATABASE_URL` não foi configurada corretamente

**Verificar**:
1. Environment → Variável `DATABASE_URL` existe?
2. Valor começa com `postgres://` ou `postgresql://`?
3. Fez novo deploy após adicionar?

### ⚠️ Sessão não mantém login

**Causa**: `EJM_SECRET` não configurada

**Solução**: Configure `EJM_SECRET` no Passo 2

## 📋 Resumo Rápido

1. ✅ Criar PostgreSQL no Render
2. ✅ Copiar Internal Database URL  
3. ✅ Adicionar `DATABASE_URL` no web service
4. ✅ (Opcional) Adicionar `EJM_SECRET`
5. ✅ Deploy
6. ✅ Aguardar build (~3min)
7. ✅ Testar login
8. ✅ Verificar `/diagnostico`

---

## 📊 Variáveis de Ambiente CompletasgreSQL
✅ PostgreSQL configurado
✅ Tabelas criadas/verificadas
✅ Administrador configurado pelas variáveis de ambiente
```

## 4. Testar o Login

Após o deploy, entre com as credenciais definidas nas variáveis de ambiente.
Use uma senha exclusiva com pelo menos 12 caracteres e remova
`EJM_ADMIN_PASSWORD` do ambiente depois de confirmar o primeiro acesso.

## 4. Verificar Status

Acesse o endpoint de diagnóstico:
```
https://seu-app.onrender.com/diagnostico
```

Mostra:
- ✅ Status do banco de dados
- ✅ Variáveis de ambiente configuradas
- ✅ Quantidade de usuários e produtos
- ✅ Se admin existe

## 5. Comandos Úteis (Shell do Render)

### Resetar senha do admin
```bash
python resetar_senha_admin.py
```

### Verificar banco
```bash
python testar_banco.py
```

### Criar admin manualmente (se necessário)
```bash
python garantir_admin.py
```

## 📋 Variáveis de Ambiente Opcionais

### Email (para notificações)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app
EMAIL_FROM_NAME=EJM Santos - Mel Natural
```

### Stripe (pagamentos)
```bash
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

### URL Pública (já configurada no render.yaml)
```bash
PUBLIC_BASE_URL=https://seu-app.onrender.com
```

## 🐛 Troubleshooting

### "Erro ao processar login"

**Causa**: Banco não inicializado ou SECRET_KEY mudando

**Solução**:
1. Acesse `/diagnostico`
2. Se admin não existe, execute no Shell: `python garantir_admin.py`
3. Configure `EJM_SECRET` para persistir sessões

### "Email ou senha inválidos"

**Causa**: Admin não existe ou senha incorreta

**Solução**:
```bash
python garantir_admin.py
```

### Sessão não mantém login após restart

**Causa**: SECRET_KEY não configurada (gera nova a cada restart)

**Solução**: Configure variável `EJM_SECRET`

## 📊 Monitoramento

### Ver logs em tempo real
Dashboard Render → **Logs**

### Reiniciar app
Dashboard Render → **Manual Deploy** → **Clear build cache & deploy**
