# 🔐 Guia de Segurança HTTPS + CSRF
**EJM Santos - Loja de Mel Natural**

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Proteção HTTPS](#proteção-https)
3. [Proteção CSRF](#proteção-csrf)
4. [Headers de Segurança](#headers-de-segurança)
5. [Configuração por Ambiente](#configuração-por-ambiente)
6. [Como Usar](#como-usar)
7. [Testes](#testes)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este projeto implementa **múltiplas camadas de segurança** para proteger contra ataques comuns:

### ✅ Implementado

| Proteção | Status | Descrição |
|----------|--------|-----------|
| **HTTPS Force** | ✅ | Redireciona HTTP → HTTPS automaticamente em produção |
| **CSRF Protection** | ✅ | Proteção contra Cross-Site Request Forgery |
| **Security Headers** | ✅ | CSP, HSTS, X-Frame-Options, etc. |
| **Secure Cookies** | ✅ | HttpOnly, Secure, SameSite |
| **Rate Limiting** | ✅ | Proteção contra brute force |
| **Proxy Detection** | ✅ | Suporte a Nginx, Apache, Cloudflare, Render |

---

## 🔒 Proteção HTTPS

### Como Funciona

O middleware `HTTPSRedirectMiddleware` detecta automaticamente se a requisição veio via HTTP e redireciona para HTTPS.

```python
# Detecta proxies reversos (Nginx, Apache, Render, Heroku)
X-Forwarded-Proto: https
X-Forwarded-Ssl: on
X-Real-IP: xxx.xxx.xxx.xxx
CF-Connecting-IP: xxx.xxx.xxx.xxx (Cloudflare)
```

### Configuração

**config.py:**
```python
class ProductionConfig(Config):
    FORCE_HTTPS = True  # ✅ Redirecionar HTTP → HTTPS
    PREFERRED_URL_SCHEME = 'https'
    TRUST_PROXY_HEADERS = True  # Detectar proxies
```

### Exceções Automáticas

Rotas **isentas** de redirecionamento HTTPS:
- `/health` - Health checks
- `/webhook/*` - Webhooks externos (Stripe, etc.)
- `OPTIONS` - CORS preflight

### Decorator Manual

Para proteger rotas específicas:

```python
from app.utils.security import require_https

@app.route('/checkout')
@require_https
def checkout():
    return render_template('checkout.html')
```

---

## 🛡️ Proteção CSRF

### O que é CSRF?

**Cross-Site Request Forgery** é um ataque que força o usuário autenticado a executar ações não intencionais.

**Exemplo de ataque:**
```html
<!-- Site malicioso -->
<form action="https://ejm-santos.com/conta/deletar" method="POST">
  <input type="hidden" name="confirmar" value="sim">
</form>
<script>document.forms[0].submit();</script>
```

### Como Protegemos

1. **Token único** por sessão
2. **Validação automática** em POST/PUT/PATCH/DELETE
3. **Cookie + Header** para AJAX

### Uso em Templates

**Formulários HTML:**
```html
<form method="POST" action="/login">
  {{ csrf_token() }}
  <input type="text" name="email">
  <button type="submit">Entrar</button>
</form>

<!-- Ou com hidden field explícito -->
<form method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

**Meta Tag (já no base.html):**
```html
<head>
  <meta name="csrf-token" content="{{ csrf_token() }}" />
</head>
```

### Uso em JavaScript/AJAX

**Vanilla JavaScript (Fetch API):**
```javascript
// Usar a função csrfFetch() do main.js
fetch('/api/carrinho/adicionar', csrfFetch({
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ produto_id: 123 })
}));
```

**jQuery (configuração automática):**
```javascript
// O token é adicionado automaticamente!
$.post('/api/carrinho/adicionar', { produto_id: 123 });
```

**Axios:**
```javascript
const token = document.querySelector('meta[name="csrf-token"]').content;

axios.post('/api/carrinho/adicionar', data, {
  headers: {
    'X-CSRFToken': token
  }
});
```

### Exceções CSRF

Rotas **isentas** de validação CSRF:
```python
# app/utils/security.py → csrf_exempt_routes()
[
    '/webhook/stripe',    # Webhooks Stripe
    '/api/webhook/',      # Outros webhooks
    '/health',            # Health checks
]
```

### Configuração Avançada

**config.py:**
```python
WTF_CSRF_ENABLED = True              # Ativar proteção
WTF_CSRF_TIME_LIMIT = None           # Token não expira
WTF_CSRF_CHECK_DEFAULT = True        # Validar por padrão
WTF_CSRF_HEADERS = ['X-CSRFToken']   # Headers aceitos
WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
WTF_CSRF_COOKIE_HTTPONLY = False     # Acessível via JS
WTF_CSRF_COOKIE_SECURE = True        # HTTPS only (prod)
WTF_CSRF_COOKIE_SAMESITE = 'Lax'     # Anti-CSRF adicional
```

---

## 🛡️ Headers de Segurança

### Headers Implementados

| Header | Valor | Proteção |
|--------|-------|----------|
| **Strict-Transport-Security** | `max-age=31536000; includeSubDomains; preload` | Force HTTPS por 1 ano |
| **X-Content-Type-Options** | `nosniff` | Previne MIME sniffing |
| **X-Frame-Options** | `SAMEORIGIN` | Anti-clickjacking |
| **X-XSS-Protection** | `1; mode=block` | Filtro XSS do browser |
| **Referrer-Policy** | `strict-origin-when-cross-origin` | Controle de referrer |
| **Permissions-Policy** | `geolocation=(), camera=(), ...` | Desabilita APIs desnecessárias |
| **Content-Security-Policy** | *(ver abaixo)* | Política de conteúdo |

### Content Security Policy (CSP)

**Produção:**
```
default-src 'self';
script-src 'self' https://js.stripe.com https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https://api.stripe.com;
frame-src https://js.stripe.com https://hooks.stripe.com;
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'self';
```

**Permite:**
- ✅ Scripts do Stripe e Chart.js
- ✅ Estilos inline (necessário)
- ✅ Imagens de qualquer HTTPS
- ✅ Conexões com API do Stripe

**Bloqueia:**
- ❌ Scripts inline (`<script>alert('xss')</script>`)
- ❌ Plugins Flash/Java
- ❌ Frames de outros domínios

---

## ⚙️ Configuração por Ambiente

### Development (dev)

```python
# HTTPS desabilitado para localhost
FORCE_HTTPS = False
PREFERRED_URL_SCHEME = 'http'

# CSRF desabilitado para facilitar testes
WTF_CSRF_ENABLED = False

# Cookies menos restritivos
SESSION_COOKIE_SECURE = False  # HTTP permitido
WTF_CSRF_COOKIE_SECURE = False
```

**Executar:**
```bash
$env:FLASK_ENV="development"
python app_new.py
```

### Production (prod)

```python
# HTTPS obrigatório
FORCE_HTTPS = True
PREFERRED_URL_SCHEME = 'https'

# CSRF ativo
WTF_CSRF_ENABLED = True
WTF_CSRF_SSL_STRICT = True

# Cookies seguros
SESSION_COOKIE_SECURE = True   # HTTPS only
WTF_CSRF_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'
```

**Executar:**
```bash
$env:FLASK_ENV="production"
gunicorn app_new:app
```

### Testing

```python
# Tudo desabilitado para testes
FORCE_HTTPS = False
WTF_CSRF_ENABLED = False
RATELIMIT_ENABLED = False
```

---

## 🚀 Como Usar

### 1. Variáveis de Ambiente

Crie `.env`:
```bash
# Ambiente
FLASK_ENV=production

# Segurança
EJM_SECRET=sua_chave_super_secreta_de_32_chars_ou_mais

# URL Base (HTTPS em produção!)
PUBLIC_BASE_URL=https://ejm-santos.com

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...

# Email
EMAIL_USER=seu@email.com
EMAIL_PASSWORD=sua_senha
```

### 2. Deploy com Proxy Reverso

**Nginx:**
```nginx
server {
    listen 443 ssl http2;
    server_name ejm-santos.com;

    ssl_certificate /etc/letsencrypt/live/ejm-santos.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ejm-santos.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirecionar HTTP → HTTPS
server {
    listen 80;
    server_name ejm-santos.com;
    return 301 https://$host$request_uri;
}
```

**Apache:**
```apache
<VirtualHost *:443>
    ServerName ejm-santos.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/ejm-santos.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/ejm-santos.com/privkey.pem
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    
    RequestHeader set X-Forwarded-Proto "https"
</VirtualHost>
```

### 3. Certificado SSL/TLS

**Let's Encrypt (gratuito):**
```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d ejm-santos.com -d www.ejm-santos.com

# Renovação automática
sudo certbot renew --dry-run
```

### 4. Render/Heroku

Essas plataformas **gerenciam HTTPS automaticamente**!

```yaml
# render.yaml
services:
  - type: web
    name: ejm-santos
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app_new:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PUBLIC_BASE_URL
        value: https://ejm-santos.onrender.com
```

---

## 🧪 Testes

### Testar HTTPS Force

**Desenvolvimento (não redireciona):**
```bash
curl http://localhost:5000/
# Resposta: 200 OK
```

**Produção (redireciona):**
```bash
curl -I http://ejm-santos.com/
# HTTP/1.1 301 Moved Permanently
# Location: https://ejm-santos.com/
```

### Testar CSRF Protection

**Sem token (403 Forbidden):**
```bash
curl -X POST http://localhost:5000/login \
  -d "email=test@email.com&senha=123456"
# 400 Bad Request - CSRF token missing
```

**Com token (200 OK):**
```bash
# 1. Obter token
TOKEN=$(curl -s http://localhost:5000/login | grep csrf_token | cut -d'"' -f6)

# 2. Enviar com token
curl -X POST http://localhost:5000/login \
  -d "csrf_token=$TOKEN&email=test@email.com&senha=123456"
# 200 OK ou redirect
```

### Testar Headers de Segurança

```bash
curl -I https://ejm-santos.com/

# Deve retornar:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN
# Content-Security-Policy: default-src 'self'; ...
```

### Testar com Browser DevTools

1. Abrir **DevTools** (F12)
2. Aba **Network**
3. Acessar site
4. Clicar em request
5. Ver **Response Headers**

---

## 🔧 Troubleshooting

### Problema: "CSRF token missing or invalid"

**Causa:** Token não foi enviado no formulário.

**Solução:**
```html
<!-- Adicionar no formulário -->
<form method="POST">
  {{ csrf_token() }}
  ...
</form>
```

### Problema: AJAX retorna 400 CSRF Error

**Causa:** Token não está sendo enviado no header.

**Solução:**
```javascript
// Usar csrfFetch() do main.js
fetch('/api/rota', csrfFetch({
  method: 'POST',
  body: JSON.stringify(data)
}));
```

### Problema: Redirect loop infinito

**Causa:** Proxy não está enviando `X-Forwarded-Proto`.

**Solução Nginx:**
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
```

**Solução Apache:**
```apache
RequestHeader set X-Forwarded-Proto "https"
```

### Problema: "Mixed content blocked"

**Causa:** Página HTTPS carregando recursos HTTP.

**Solução:**
```html
<!-- ❌ Errado -->
<script src="http://exemplo.com/script.js"></script>

<!-- ✅ Correto -->
<script src="https://exemplo.com/script.js"></script>

<!-- ✅ Ou usar protocol-relative -->
<script src="//exemplo.com/script.js"></script>
```

### Problema: HSTS muito agressivo

**Causa:** `max-age` muito alto durante desenvolvimento.

**Solução:**
```python
# Development
FORCE_HTTPS = False  # Não adicionar HSTS

# Production
FORCE_HTTPS = True
```

### Problema: Stripe não carrega

**Causa:** CSP bloqueando scripts do Stripe.

**Solução (já configurado):**
```python
script-src 'self' https://js.stripe.com;
frame-src https://js.stripe.com https://hooks.stripe.com;
connect-src 'self' https://api.stripe.com;
```

---

## 📚 Referências

- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Secure Headers](https://owasp.org/www-project-secure-headers/)
- [MDN Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Let's Encrypt](https://letsencrypt.org/)
- [Flask-WTF CSRF](https://flask-wtf.readthedocs.io/en/stable/csrf.html)

---

## ✅ Checklist de Segurança

### Antes do Deploy

- [ ] `EJM_SECRET` tem 32+ caracteres
- [ ] `PUBLIC_BASE_URL` usa HTTPS
- [ ] `FLASK_ENV=production`
- [ ] `FORCE_HTTPS=True` em production
- [ ] `WTF_CSRF_ENABLED=True` em production
- [ ] Certificado SSL/TLS configurado
- [ ] Proxy reverso com headers corretos
- [ ] Webhooks em rotas isentas de CSRF
- [ ] Todos os formulários têm `{{ csrf_token() }}`
- [ ] AJAX usa `X-CSRFToken` header
- [ ] Testar em staging antes de produção

### Monitoramento

- [ ] Logs de erro CSRF
- [ ] Logs de redirect HTTPS
- [ ] Rate limiting funcionando
- [ ] Renovação automática de SSL

---

**🍯 EJM Santos - Mel Natural com Segurança Natural**
