# 🚀 Configuração no Render

## 1. Variáveis de Ambiente Obrigatórias

Acesse: **Dashboard > Environment > Environment Variables**

### SECRET_KEY
```bash
EJM_SECRET=<gere com: python -c "import secrets; print(secrets.token_hex(32))">
```

### Banco de Dados
```bash
FLASK_ENV=production
DATABASE_URL=<automático do Render>
```

### Email (opcional)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app
EMAIL_FROM_NAME=EJM Santos - Mel Natural
```

### Stripe (opcional)
```bash
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

### URL Pública
```bash
PUBLIC_BASE_URL=https://ejm-santos-site.onrender.com
```

## 2. Comandos de Build

```bash
Build Command: pip install -r requirements.txt
Start Command: gunicorn application:app
```

## 3. Criar Usuário Admin

Após deploy, execute no Render Shell:

```bash
python garantir_admin.py
```

Isso criará o usuário admin se não existir:
- Email: admin@ejmsantos.com
- Senha: admin123

## 4. Ver Logs

```bash
# No Render Dashboard > Logs
# Procure por erros de:
# - SECRET_KEY não configurada
# - Banco de dados não encontrado
# - Erro ao criar tabelas
```

## 5. Resetar Banco de Dados

Se precisar resetar o banco:

```bash
python scripts/database/init_db.py
python garantir_admin.py
```

## 6. Testar Login

1. Acesse: https://ejm-santos-site.onrender.com/login
2. Use: admin@ejmsantos.com / admin123
3. Deve redirecionar para /admin

## Troubleshooting

### "Erro ao processar login"

**Causa**: SECRET_KEY não configurada ou banco não inicializado

**Solução**:
1. Verificar variável `EJM_SECRET` no Render
2. Executar `python garantir_admin.py` no Shell
3. Ver logs para erro específico

### "Email ou senha inválidos"

**Causa**: Usuário admin não existe no banco

**Solução**:
```bash
python garantir_admin.py
```

### Sessão não mantém login

**Causa**: SECRET_KEY mudando a cada deploy

**Solução**: Definir SECRET_KEY fixa como variável de ambiente
