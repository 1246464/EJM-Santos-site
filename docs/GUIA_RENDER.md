# 🚀 Configuração no Render

## ✅ Inicialização Automática

O sistema agora **inicializa automaticamente** no primeiro deploy:
- ✅ Cria todas as tabelas do banco
- ✅ Cria usuário admin (admin@ejmsantos.com / admin123)
- ✅ Gera SECRET_KEY temporária se não configurada

## 1. Deploy Básico (Funcional)

Apenas faça o deploy normalmente! O app vai:
1. Instalar dependências
2. Executar `init_render.py` automaticamente
3. Criar banco e admin
4. Iniciar servidor

**⚠️ Limitação**: Sessões não persistem entre restarts sem SECRET_KEY configurada.

## 2. Configuração Recomendada (Produção)

Para **persistir sessões** entre restarts, configure:

### Dashboard Render → Environment → Add Environment Variable

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

## 3. Credenciais Padrão

Após o deploy, use:
- **Email**: admin@ejmsantos.com
- **Senha**: admin123

**⚠️ IMPORTANTE**: Altere a senha após primeiro login!

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
