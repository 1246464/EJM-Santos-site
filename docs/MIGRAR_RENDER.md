# 🔄 Como Executar a Migração no Render

## Problema

Após adicionar novas funcionalidades (taxa de entrega e agendamento), o banco de dados de produção precisa ser atualizado com as novas colunas.

**Erro:** "Erro no banco de dados" ao fazer login

**Causa:** As novas colunas (`subtotal`, `delivery_fee`, `delivery_date`, etc.) não existem no PostgreSQL do Render.

## ✅ Solução: Executar Migração no Render

### Método 1: Via Console do Render (Recomendado)

1. **Acesse o Dashboard do Render:**
   - Vá para: https://dashboard.render.com/
   - Selecione seu serviço web **ejm-santos-site**

2. **Abra o Shell:**
   - No menu lateral, clique em **"Shell"**
   - Ou acesse: https://dashboard.render.com/web/[SEU-SERVICE-ID]/shell

3. **Execute o script de migração:**
   ```bash
   python migrate_database.py
   ```

4. **Aguarde a confirmação:**
   ```
   ✅ 6 novas colunas adicionadas com sucesso!
   ✅ Migração concluída com sucesso!
   ```

5. **Teste o site:**
   - Faça login novamente
   - O erro deve ter desaparecido

---

### Método 2: Via Comandos SQL Diretos

Se o Método 1 não funcionar, você pode executar SQL diretamente:

1. **Acesse o banco de dados no Render:**
   - Dashboard → Databases → **ejm-santos-db**
   - Copie a **External Database URL**

2. **Execute os comandos SQL:**

```sql
-- Adicionar colunas de entrega
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS subtotal FLOAT DEFAULT 0;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS delivery_fee FLOAT DEFAULT 0;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS delivery_distance_km FLOAT;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMP;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS delivery_scheduled_at TIMESTAMP;
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS delivery_notes TEXT;

-- Atualizar pedidos existentes
UPDATE "order" SET subtotal = total, delivery_fee = 0 WHERE subtotal IS NULL OR subtotal = 0;
```

3. **Via psql (se tiver instalado localmente):**
   ```bash
   psql [EXTERNAL_DATABASE_URL]
   ```
   Então cole os comandos SQL acima.

4. **Via Render Shell:**
   ```bash
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS subtotal FLOAT DEFAULT 0;"
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS delivery_fee FLOAT DEFAULT 0;"
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS delivery_distance_km FLOAT;"
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMP;"
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS delivery_scheduled_at TIMESTAMP;"
   psql $DATABASE_URL -c "ALTER TABLE \"order\" ADD COLUMN IF NOT EXISTS delivery_notes TEXT;"
   psql $DATABASE_URL -c "UPDATE \"order\" SET subtotal = total, delivery_fee = 0 WHERE subtotal IS NULL OR subtotal = 0;"
   ```

---

### Método 3: Forçar Redeploy com Migração Automática

Podemos modificar o script de inicialização para executar a migração automaticamente no deploy.

**Editar `init_render.py`:**

```python
# Executar migração antes de iniciar
try:
    from migrate_database import migrate_database
    migrate_database()
except Exception as e:
    print(f"⚠️ Erro na migração automática: {e}")
```

---

## 🔍 Verificar se Funcionou

Após executar a migração:

1. **Tente fazer login no site**
   - Admin: `/admin/login`
   - Usuário: `/login`

2. **Verifique no Shell do Render:**
   ```bash
   python -c "from application import app, db; from app.models import Order; app.app_context().push(); print([c.name for c in Order.__table__.columns])"
   ```

   Deve mostrar todas as colunas incluindo as novas:
   ```
   [..., 'subtotal', 'delivery_fee', 'delivery_distance_km', 'delivery_date', 'delivery_scheduled_at', 'delivery_notes']
   ```

---

## ⚠️ Troubleshooting

### Erro: "permission denied"
- Certifique-se de estar no Shell do serviço web (não do banco)
- O usuário do banco precisa ter permissão de ALTER TABLE

### Erro: "column already exists"
- Ótimo! Significa que a coluna já foi adicionada
- Execute apenas as colunas faltantes

### Erro: "comando não encontrado"
- Use `python3` ao invés de `python`:
  ```bash
  python3 migrate_database.py
  ```

### Site ainda com erro após migração
1. **Reinicie o serviço:**
   - Dashboard → Settings → Manual Deploy → "Clear build cache & deploy"

2. **Verifique os logs:**
   - Dashboard → Logs
   - Procure por erros relacionados ao banco

---

## 📝 Notas

- **A migração é segura:** Usa `ADD COLUMN IF NOT EXISTS` (PostgreSQL)
- **Não perde dados:** Apenas adiciona colunas novas
- **Pedidos antigos:** Serão atualizados automaticamente com `subtotal = total`

---

## 🆘 Se nada funcionar

1. **Backup do banco:**
   - Dashboard → Database → Backups

2. **Recriar tabelas (⚠️ APAGA TODOS OS DADOS):**
   ```bash
   python inicializar_db.py
   ```
   **ATENÇÃO:** Isso apaga todos os pedidos, usuários e produtos!

3. **Contato:**
   - Verifique os logs completos no Render
   - Entre em contato com suporte se necessário
