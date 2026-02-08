# 🛡️ Sistema de Tratamento de Erros - EJM Santos

## Visão Geral

Este documento descreve o sistema completo de tratamento de erros implementado no projeto EJM Santos. O sistema foi projetado para:

- ✅ Capturar e registrar todos os erros
- ✅ Fornecer mensagens amigáveis aos usuários
- ✅ Facilitar debugging e manutenção
- ✅ Prevenir vazamento de informações sensíveis
- ✅ Manter a aplicação estável mesmo em caso de erros

---

## 📁 Estrutura de Arquivos

### 1. `app/utils/exceptions.py`
**Exceções customizadas da aplicação**

```python
EJMBaseException         # Exceção base
├── ValidationError      # Erro de validação (400)
├── AuthenticationError  # Erro de autenticação (401)
├── AuthorizationError   # Erro de autorização (403)
├── NotFoundError        # Recurso não encontrado (404)
├── DatabaseError        # Erro de banco de dados (500)
├── EmailError           # Erro ao enviar email (500)
├── PaymentError         # Erro de pagamento (500)
├── StockError           # Erro de estoque (400)
└── FileUploadError      # Erro de upload (400)
```

### 2. `app/utils/error_handlers.py`
**Handlers globais de erro**

Registra handlers para:
- Erros HTTP (400, 401, 403, 404, 405, 413, 500)
- Erros SQLAlchemy (IntegrityError, SQLAlchemyError)
- Exceções customizadas da aplicação
- Exceções genéricas não tratadas

### 3. `templates/erro.html`
**Template genérico para exibir erros**

Exibe mensagens de erro de forma amigável com:
- Ícone de alerta
- Mensagem principal
- Detalhes (opcional)
- Botões para voltar

---

## 🔧 Como Funciona

### Fluxo de Tratamento de Erros

```
1. Erro ocorre na aplicação
   ↓
2. Try-catch local captura (se houver)
   ↓
3. Logging do erro
   ↓
4. Error handler global (se não tratado)
   ↓
5. Resposta apropriada ao usuário
   - HTML: template erro.html
   - JSON: objeto de erro
```

### Exemplo de Uso

#### Em Rotas HTML
```python
@app.route("/minha-rota")
def minha_rota():
    try:
        # Código que pode gerar erro
        resultado = operacao_perigosa()
        return render_template("sucesso.html", dados=resultado)
    
    except ValueError as e:
        logger.warning(f"Valor inválido: {str(e)}")
        return render_template("erro.html", 
                             mensagem="Dados inválidos",
                             detalhes=str(e)), 400
    
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return render_template("erro.html", 
                             mensagem="Erro ao processar solicitação"), 500
```

#### Em APIs JSON
```python
@app.route("/api/minha-rota")
def api_minha_rota():
    try:
        resultado = operacao_perigosa()
        return jsonify({"success": True, "data": resultado})
    
    except ValidationError as e:
        logger.warning(f"Validação falhou: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        logger.error(f"Erro na API: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno"}), 500
```

---

## 📋 Boas Práticas Implementadas

### 1. **Sempre Use Try-Catch em Operações Críticas**
- ✅ Acesso ao banco de dados
- ✅ Requisições externas (Stripe, Email)
- ✅ Processamento de arquivos
- ✅ Operações com sessão
- ✅ Parsing de dados do usuário

### 2. **Faça Rollback em Caso de Erro no DB**
```python
try:
    db.session.add(objeto)
    db.session.commit()
except Exception as e:
    db.session.rollback()  # ⚠️ IMPORTANTE
    logger.error(f"Erro: {e}")
    raise
```

### 3. **Log Apropriado por Severidade**
```python
logger.debug("Info detalhada para debug")
logger.info("Operação bem-sucedida")
logger.warning("Algo inesperado mas não crítico")
logger.error("Erro que precisa atenção")
logger.critical("Erro grave que afeta sistema")
```

### 4. **Mensagens de Erro Amigáveis**
❌ Não mostre ao usuário:
```python
return "KeyError: 'user_id' not found in session dict"
```

✅ Mostre mensagens claras:
```python
return render_template("erro.html", 
                     mensagem="Sessão expirada",
                     detalhes="Por favor, faça login novamente")
```

### 5. **Validação de Dados**
```python
from app.utils import Validator

# Validar antes de processar
is_valid, errors = Validator.validate_user_registration(data)
if not is_valid:
    return jsonify({"errors": errors}), 400
```

---

## 📊 Sistema de Logging

### Localização dos Logs
```
logs/
├── ejm-santos.log         # Log geral
└── ejm-santos-errors.log  # Apenas erros
```

### Configuração
- Rotação automática a cada 10MB
- Mantém 10 backups
- Formato: `[YYYY-MM-DD HH:MM:SS] LEVEL in module: message`

### Exemplos de Logs
```
[2026-02-04 10:30:15] INFO in auth: Login bem-sucedido - User ID: 5 (user@example.com)
[2026-02-04 10:45:22] WARNING in products: Estoque insuficiente para produto 3 - User: 5
[2026-02-04 11:00:00] ERROR in payment: Erro do Stripe - User: 5: Card declined
```

---

## 🚨 Handlers de Erro Globais

### Erros HTTP Tratados

| Código | Nome | Quando Ocorre |
|--------|------|---------------|
| 400 | Bad Request | Dados inválidos na requisição |
| 401 | Unauthorized | Usuário não autenticado |
| 403 | Forbidden | Sem permissão para acessar |
| 404 | Not Found | Página/recurso não encontrado |
| 405 | Method Not Allowed | Método HTTP incorreto |
| 413 | Request Entity Too Large | Arquivo muito grande |
| 500 | Internal Server Error | Erro interno do servidor |

### Erros de Banco de Dados

- **IntegrityError**: Violação de constraint (duplicação, FK)
  - Faz rollback automático
  - Retorna mensagem amigável

- **SQLAlchemyError**: Outros erros do banco
  - Faz rollback automático
  - Registra erro completo no log

---

## 🔍 Debugging

### Ver Logs em Tempo Real
```bash
# PowerShell
Get-Content logs\ejm-santos.log -Tail 50 -Wait

# Ver apenas erros
Get-Content logs\ejm-santos-errors.log -Tail 50 -Wait
```

### Informações nos Logs
Cada erro registra:
- ✅ Timestamp
- ✅ Nível de severidade
- ✅ Módulo onde ocorreu
- ✅ Mensagem do erro
- ✅ Stack trace completo (em erros)
- ✅ IP do usuário (quando relevante)
- ✅ User ID (quando disponível)

---

## 🎯 Checklist de Implementação

Ao adicionar novas funcionalidades, certifique-se de:

- [ ] Envolver operações de DB em try-catch
- [ ] Fazer rollback em caso de erro
- [ ] Registrar logs apropriados
- [ ] Retornar mensagens amigáveis
- [ ] Validar dados de entrada
- [ ] Testar cenários de erro
- [ ] Verificar se emails/APIs externas têm fallback
- [ ] Não expor stack traces ao usuário
- [ ] Usar os status codes HTTP corretos

---

## 📞 Suporte

Se encontrar erros não tratados:

1. **Verifique os logs**: `logs/ejm-santos-errors.log`
2. **Identifique o módulo**: procure pelo nome do arquivo
3. **Analise o stack trace**: linha exata do erro
4. **Adicione tratamento**: implemente try-catch apropriado
5. **Teste**: reproduza o erro e verifique a correção

---

## 🔄 Manutenção

### Rotina Recomendada

**Diário**:
- Verificar logs de erro
- Investigar erros recorrentes

**Semanal**:
- Analisar padrões de erro
- Otimizar handlers se necessário

**Mensal**:
- Revisar e limpar logs antigos
- Atualizar documentação se houver mudanças

---

## ✅ Resumo

O sistema de tratamento de erros implementado garante:

1. ✅ **Estabilidade**: Aplicação não quebra com erros
2. ✅ **Rastreabilidade**: Todos os erros são registrados
3. ✅ **UX**: Usuários veem mensagens amigáveis
4. ✅ **Segurança**: Informações sensíveis não vazam
5. ✅ **Manutenibilidade**: Fácil debug e correção

---

**Última atualização**: 04/02/2026
**Versão**: 1.0
