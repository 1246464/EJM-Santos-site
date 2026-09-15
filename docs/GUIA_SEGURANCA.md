# ============================================
# GUIA DE SEGURANÇA - EJM Santos
# ============================================

## 🔒 Melhorias Implementadas

### 1. **Sistema de Configuração Seguro**
- ✅ Arquivo `config.py` com ambientes separados (dev/test/prod)
- ✅ Validação de SECRET_KEY forte (mínimo 32 caracteres)
- ✅ Sem fallbacks inseguros
- ✅ Configurações específicas por ambiente

### 2. **CSRF Protection**
- ✅ Flask-WTF ativado globalmente
- ✅ Tokens CSRF em todos os formulários
- ✅ Validação automática de requisições POST
- ✅ Exceção para webhooks do Stripe (se necessário)

### 3. **Rate Limiting**
- ✅ Flask-Limiter configurado
- ✅ Limites gerais: 200/dia, 50/hora
- ✅ Login: 10 tentativas/minuto
- ✅ Admin login: 5 tentativas/minuto
- ✅ Cadastro: 3 tentativas/hora

### 4. **Headers de Segurança**
```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: (configurado para Stripe)
```

### 5. **Validação de Entrada**
- ✅ Regex para email
- ✅ Senha forte: mín 8 chars, maiúscula, minúscula, número
- ✅ Sanitização de nome (sem caracteres perigosos)
- ✅ Validação de comprimento

### 6. **Sessões Seguras**
```python
SESSION_COOKIE_SECURE = True      # Apenas HTTPS
SESSION_COOKIE_HTTPONLY = True    # Não acessível via JS
SESSION_COOKIE_SAMESITE = 'Lax'   # Proteção CSRF
PERMANENT_SESSION_LIFETIME = 24h  # Expiração
```

---

## 🚀 Como Usar

### Gerar SECRET_KEY Segura
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Configurar Ambiente
```bash
# Copiar exemplo
cp .env.example .env

# Editar com valores reais
nano .env

# Configurar ambiente
export FLASK_ENV=development  # ou production
```

### Executar com Configuração Correta
```bash
# Development
FLASK_ENV=development python application.py

# Production (valida configurações)
FLASK_ENV=production python application.py
```

---

## 🔐 Checklist de Segurança

### Antes de Deploy em Produção

- [ ] **SECRET_KEY gerada aleatoriamente** (64+ chars)
- [ ] **Chaves Stripe de produção** (não test!)
- [ ] **HTTPS ativado** (PUBLIC_BASE_URL)
- [ ] **Banco de dados de produção** (não SQLite)
- [ ] **Redis configurado** para rate limiting
- [ ] **Logs estruturados** (JSON)
- [ ] **Sentry ou monitor** de erros
- [ ] **Backup automatizado** do banco
- [ ] **Firewall configurado** (apenas 443/80)
- [ ] **SSL/TLS válido** (Let's Encrypt)

### Segurança de Credenciais

- [ ] `.env` no `.gitignore`
- [ ] Chaves revogadas se commitadas
- [ ] Senha de app do Gmail (não senha real)
- [ ] Variáveis de ambiente no servidor (não .env em prod)
- [ ] Rotação de chaves a cada 90 dias

### Monitoramento

- [ ] Alertas de login falho (>10 tentativas)
- [ ] Monitor de rate limit excedido
- [ ] Logs de acessos admin
- [ ] Alertas de erros 500
- [ ] Dashboard de métricas

---

## 🛡️ Proteções Implementadas

### Contra Ataques Comuns

| Ataque | Proteção |
|--------|----------|
| **SQL Injection** | ✅ SQLAlchemy ORM (queries parametrizadas) |
| **XSS** | ✅ Jinja2 auto-escape + CSP headers |
| **CSRF** | ✅ Flask-WTF tokens |
| **Brute Force** | ✅ Rate limiting + account lockout |
| **Session Hijacking** | ✅ HttpOnly + Secure + SameSite cookies |
| **Clickjacking** | ✅ X-Frame-Options: SAMEORIGIN |
| **MIME Sniffing** | ✅ X-Content-Type-Options: nosniff |
| **Man-in-Middle** | ✅ HSTS + HTTPS obrigatório |

---

## 📋 Próximos Passos

### Segurança Adicional (Opcional)

1. **OAuth2 Login** (Google/Facebook)
2. **2FA (Two-Factor Auth)** via SMS/TOTP
3. **Password Complexity Meter** no frontend
4. **Account Lockout** após 5 tentativas falhas
5. **Email de Alerta** em login de novo IP
6. **Honeypot Fields** em formulários
7. **IP Whitelist** para admin
8. **Audit Log** de todas as ações admin

### Compliance

- **LGPD**: Implementar termos de uso e política de privacidade
- **PCI-DSS**: Stripe já lida com cartões (não armazenar dados)
- **GDPR**: Opção de exportar/deletar dados do usuário

---

## ⚠️ AVISOS IMPORTANTES

### EM PRODUÇÃO
```bash
# ❌ NUNCA
DEBUG = True
SESSION_COOKIE_SECURE = False
SQLALCHEMY_ECHO = True

# ✅ SEMPRE
DEBUG = False
SESSION_COOKIE_SECURE = True
FLASK_ENV = production
```

### CREDENCIAIS
- **Revogar imediatamente** chaves commitadas no Git
- **Nunca** logar senhas ou tokens
- **Usar** variáveis de ambiente (não hardcode)

---

## 📞 Suporte

Em caso de incidente de segurança:
1. Revogar credenciais comprometidas
2. Alterar SECRET_KEY
3. Forçar logout de todos os usuários
4. Investigar logs de acesso
5. Notificar usuários afetados (se aplicável)
