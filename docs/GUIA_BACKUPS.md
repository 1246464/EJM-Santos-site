# 💾 Guia de Backups Automáticos
**EJM Santos - Loja de Mel Natural**

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Criação de Backups](#criação-de-backups)
4. [Restauração de Backups](#restauração-de-backups)
5. [Agendamento Automático](#agendamento-automático)
6. [Gerenciamento de Backups](#gerenciamento-de-backups)
7. [Configuração Avançada](#configuração-avançada)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O sistema de backups do EJM Santos oferece **proteção completa dos dados** com:

### ✅ Recursos

| Recurso | Descrição |
|---------|-----------|
| **Backup Completo** | Banco de dados + Imagens + Logs |
| **Compressão ZIP** | Reduz tamanho dos arquivos |
| **Validação Automática** | Verifica integridade do banco |
| **Rotação Automática** | Remove backups antigos |
| **Agendamento** | Backups diários/semanais |
| **Restauração Segura** | Backup de segurança antes de restaurar |
| **Modo Interativo** | Interface amigável para restauração |

### 📦 O que é incluído no backup?

- ✅ **Banco de dados SQLite** (`instance/*.db`)
- ✅ **Imagens de produtos** (`static/imagens/*.jpg|png|webp`)
- ⚙️ **Logs** (opcional, desabilitado por padrão)

### 📊 Estrutura do Backup

```
ejm_backup_20260208_120000.zip
├── MANIFEST.json          # Metadados do backup
├── database/
│   ├── ejm.db            # Banco de dados principal
│   └── ejm_dev.db        # Banco de desenvolvimento
└── static/
    └── imagens/
        ├── produto_1.jpg
        ├── produto_2.webp
        └── ...
```

---

## 📥 Instalação

### 1. Dependência Adicional

O agendador automático requer a biblioteca `schedule`:

```bash
pip install schedule
```

**Ou adicione ao [requirements.txt](requirements.txt):**
```txt
schedule>=1.2.0
```

### 2. Verificar Estrutura

Certifique-se que os diretórios existem:

```bash
# Criar diretórios necessários
mkdir backups
mkdir logs
```

### 3. Permissões

Garanta que o script tem permissão de escrita:

**Linux/Mac:**
```bash
chmod +x backup_manager.py
chmod +x backup_scheduler.py
chmod +x restore_backup.py
```

---

## 🔧 Criação de Backups

### Backup Completo (Recomendado)

```bash
python backup_manager.py create
```

**Saída:**
```
============================================================
🔄 Iniciando backup: ejm_backup_20260208_120000.zip
============================================================
📊 Fazendo backup do banco de dados...
  ✅ ejm.db (2.45 MB)
🖼️  Fazendo backup das imagens...
  ✅ 23 imagens adicionadas
============================================================
✅ Backup criado com sucesso!
📦 Arquivo: ejm_backup_20260208_120000.zip
📊 24 arquivos (15.32 MB)
💾 Tamanho comprimido: 8.76 MB
📉 Compressão: 42.8%
============================================================
```

### Opções de Backup

**Apenas banco de dados:**
```bash
python backup_manager.py create --no-images
```

**Apenas imagens:**
```bash
python backup_manager.py create --no-db
```

**Incluir logs:**
```bash
python backup_manager.py create --logs
```

**Com descrição:**
```bash
python backup_manager.py create --description "Backup antes de atualização v2.0"
```

**Combinando opções:**
```bash
python backup_manager.py create --logs --description "Backup completo mensal"
```

---

## 🔄 Restauração de Backups

### Modo Interativo (Recomendado)

```bash
python restore_backup.py
```

**Fluxo interativo:**
1. Lista todos os backups disponíveis
2. Selecione o backup desejado
3. Confirme a restauração
4. Escolha o que restaurar (DB/Imagens/Logs)
5. Aguarde a conclusão

### Restaurar Backup Mais Recente

```bash
python restore_backup.py --latest
```

### Restaurar Arquivo Específico

```bash
python restore_backup.py --file ejm_backup_20260208_120000.zip
```

### ⚠️ Importante sobre Restauração

- ✅ **Backup de segurança automático** antes de restaurar
- ✅ **Pode reverter** usando o backup de segurança
- ⚠️ **Reinicie a aplicação** após restaurar
- ⚠️ **Fecha conexões** com o banco antes de restaurar

---

## ⏰ Agendamento Automático

### Backup Diário

**Às 03:00 (padrão):**
```bash
python backup_scheduler.py --schedule daily
```

**Em horário personalizado:**
```bash
python backup_scheduler.py --schedule daily --time 02:30
```

### Backup Semanal

**Domingo às 03:00 (padrão):**
```bash
python backup_scheduler.py --schedule weekly
```

**Dia personalizado:**
```bash
python backup_scheduler.py --schedule weekly --day friday --time 23:00
```

### Backup a Cada Hora (Testes)

```bash
python backup_scheduler.py --schedule hourly
```

### Configurar Retenção

```bash
# Manter apenas 5 backups ou 15 dias
python backup_scheduler.py --schedule daily --keep 5 --days 15
```

### Executar Backup Único (Sem Agendar)

```bash
python backup_scheduler.py
```

---

## 🗂️ Gerenciamento de Backups

### Listar Todos os Backups

```bash
python backup_manager.py list
```

**Saída:**
```
📦 Backups disponíveis (8):
============================================================
📄 ejm_backup_20260208_120000.zip
   📅 Data: 2026-02-08T12:00:00
   💾 Tamanho: 8.76 MB
   📊 Arquivos: 24
   📦 Inclui: BD, Imagens
   📝 Backup antes de atualização

📄 ejm_backup_20260207_030000.zip
   📅 Data: 2026-02-07T03:00:00
   💾 Tamanho: 8.54 MB
   📊 Arquivos: 23
   📦 Inclui: BD, Imagens
   📝 Backup automático agendado
...
```

### Listar Últimos N Backups

```bash
python backup_manager.py list --limit 5
```

### Ver Detalhes de um Backup

```bash
python backup_manager.py info ejm_backup_20260208_120000.zip
```

**Saída:**
```
📦 Informações do Backup
============================================================
📄 Arquivo: ejm_backup_20260208_120000.zip
📅 Data: 2026-02-08T12:00:00
💾 Tamanho: 8.76 MB
📊 Total de arquivos: 24
📝 Descrição: Backup antes de atualização

📦 Conteúdo:
   Tipo            Arquivos   Tamanho        
   --------------- ---------- ---------------
   Database        1          2.45 MB        
   Image           23         12.87 MB       
```

### Remover Backups Antigos

**Manter últimos 10 backups ou 30 dias (padrão):**
```bash
python backup_manager.py cleanup
```

**Customizar retenção:**
```bash
# Manter apenas 5 backups ou 15 dias
python backup_manager.py cleanup --keep 5 --days 15
```

**Manter apenas os mais recentes:**
```bash
python backup_manager.py cleanup --keep 3
```

---

## ⚙️ Configuração Avançada

### Configurações no [config.py](config.py)

```python
# Backups
BACKUP_ENABLED = True              # Habilitar sistema de backups
BACKUP_DIR = BASE_DIR / "backups"  # Diretório de backups
BACKUP_KEEP_COUNT = 10             # Manter últimos N backups
BACKUP_KEEP_DAYS = 30              # Manter backups dos últimos N dias
BACKUP_INCLUDE_DB = True           # Incluir banco de dados
BACKUP_INCLUDE_IMAGES = True       # Incluir imagens
BACKUP_INCLUDE_LOGS = False        # Incluir logs
BACKUP_AUTO_CLEANUP = True         # Limpeza automática
```

### Programação via Cron (Linux)

**Editar crontab:**
```bash
crontab -e
```

**Backup diário às 3h:**
```cron
0 3 * * * cd /caminho/para/ejm-santos && python3 backup_scheduler.py
```

**Backup semanal aos domingos às 2h:**
```cron
0 2 * * 0 cd /caminho/para/ejm-santos && python3 backup_scheduler.py
```

**Limpeza semanal:**
```cron
0 4 * * 0 cd /caminho/para/ejm-santos && python3 backup_manager.py cleanup
```

### Agendamento via Task Scheduler (Windows)

1. Abrir **Agendador de Tarefas** (Task Scheduler)
2. **Criar Tarefa Básica**
3. Nome: "EJM Santos Backup Diário"
4. Gatilho: Diariamente às 03:00
5. Ação: Iniciar programa
   - Programa: `python`
   - Argumentos: `backup_scheduler.py`
   - Iniciar em: `C:\caminho\para\ejm-santos`
6. Concluir

### Backup para Nuvem

**Sincronizar com Google Drive:**
```bash
# Instalar rclone (https://rclone.org/)
# Configurar Google Drive
rclone config

# Script de sincronização (sync_backup.sh)
#!/bin/bash
cd /caminho/para/ejm-santos
python3 backup_scheduler.py
rclone copy backups/ gdrive:EJM_Santos_Backups/ --max-age 30d
```

**Sincronizar com Dropbox/OneDrive:**
```bash
# Mover diretório de backups para pasta sincronizada
ln -s /caminho/para/Dropbox/EJM_Backups backups
```

### Verificação Automática de Integridade

```python
# Script: verify_backups.py
from backup_manager import BackupManager
import sys

manager = BackupManager()
backups = manager.list_backups()

for backup in backups:
    info = manager.get_backup_info(backup['path'])
    if not info:
        print(f"❌ Backup corrompido: {backup['filename']}")
        sys.exit(1)

print(f"✅ Todos os {len(backups)} backups estão íntegros")
```

---

## 🔧 Troubleshooting

### Problema: "Permission denied ao criar backup"

**Causa:** Sem permissão de escrita no diretório.

**Solução:**
```bash
# Linux/Mac
chmod -R 755 backups/
chmod -R 755 logs/

# Windows (executar como administrador)
icacls backups /grant Users:F /T
```

### Problema: "Database is locked"

**Causa:** Aplicação está usando o banco de dados.

**Solução:**
```bash
# 1. Parar a aplicação
Ctrl+C

# 2. Executar backup
python backup_manager.py create

# 3. Reiniciar aplicação
python app_new.py
```

### Problema: Backup muito grande

**Causa:** Muitas imagens ou logs acumulados.

**Solução:**
```bash
# Criar backup apenas do banco
python backup_manager.py create --no-images --no-logs

# Limpar logs antigos
rm logs/*.log

# Otimizar imagens (redimensionar/comprimir)
# Usar ferramentas como ImageMagick ou Pillow
```

### Problema: Restauração falha

**Causa:** Backup corrompido ou incompatível.

**Solução:**
```bash
# 1. Verificar integridade
python backup_manager.py info ejm_backup_XXX.zip

# 2. Se corrompido, usar backup anterior
python restore_backup.py  # Modo interativo

# 3. Restaurar do backup de segurança
# (criado automaticamente antes da tentativa)
ls -lt backups/ | head -5
```

### Problema: Agendador não executa

**Causa:** Script não está rodando em background.

**Solução (Linux/Mac com systemd):**

```ini
# /etc/systemd/system/ejm-backup.service
[Unit]
Description=EJM Santos Backup Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ejm-santos
ExecStart=/usr/bin/python3 backup_scheduler.py --schedule daily
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ejm-backup
sudo systemctl start ejm-backup
sudo systemctl status ejm-backup
```

### Problema: Backup não inclui todos os arquivos

**Causa:** Arquivos em formato não reconhecido.

**Solução:**
```python
# Editar backup_manager.py (linha ~140)
# Adicionar extensões personalizadas
image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
```

---

## 📊 Estratégias de Backup

### Backup 3-2-1

Regra de ouro para proteção de dados:

- **3 cópias** dos dados
- **2 tipos** de mídia diferentes
- **1 cópia** offsite (fora do local)

**Exemplo para EJM Santos:**
```
1. Backup local (backups/) - Diário
2. Backup em disco externo - Semanal
3. Backup na nuvem (Google Drive) - Diário sincronizado
```

### Frequência Recomendada

| Tipo | Frequência | Retenção |
|------|-----------|----------|
| **Produção** | Diário às 03:00 | 30 dias / 10 backups |
| **Desenvolvimento** | Manual | 7 dias / 5 backups |
| **Antes de Updates** | Manual | Manter permanente |
| **Mensal** | 1º dia do mês | 1 ano |

### Script de Backup Completo

```bash
#!/bin/bash
# backup_production.sh - Script completo de backup

set -e  # Parar em caso de erro

echo "🔄 Iniciando rotina de backup..."

# 1. Backup local
echo "📦 Criando backup local..."
python3 backup_manager.py create --description "Backup automático $(date +%Y-%m-%d)"

# 2. Limpeza de backups antigos
echo "🧹 Limpando backups antigos..."
python3 backup_manager.py cleanup --keep 10 --days 30

# 3. Sincronizar com nuvem
echo "☁️  Sincronizando com Google Drive..."
rclone sync backups/ gdrive:EJM_Santos_Backups/ --max-age 30d

# 4. Notificar sucesso
echo "✅ Backup concluído com sucesso!"
```

---

## 🔒 Segurança dos Backups

### Criptografia (Opcional)

**Criptografar backup:**
```bash
# Criar backup
python backup_manager.py create

# Criptografar com GPG
gpg --symmetric --cipher-algo AES256 backups/ejm_backup_20260208_120000.zip

# Remover backup não criptografado
rm backups/ejm_backup_20260208_120000.zip
```

**Descriptografar:**
```bash
gpg --decrypt backups/ejm_backup_20260208_120000.zip.gpg > backup_decrypted.zip
```

### Verificação de Hash

```bash
# Gerar hash SHA256
sha256sum backups/ejm_backup_20260208_120000.zip > backup.sha256

# Verificar integridade
sha256sum -c backup.sha256
```

---

## 📚 Referências

- [SQLite Backup API](https://www.sqlite.org/backup.html)
- [Python zipfile](https://docs.python.org/3/library/zipfile.html)
- [Schedule Library](https://schedule.readthedocs.io/)
- [Rclone (Sync Cloud)](https://rclone.org/)

---

## ✅ Checklist de Backup

### Configuração Inicial
- [ ] Instalar dependência `schedule`
- [ ] Criar diretório `backups/`
- [ ] Testar criação de backup manual
- [ ] Testar restauração
- [ ] Configurar agendamento automático

### Manutenção Regular
- [ ] Verificar backups semanalmente
- [ ] Testar restauração mensalmente
- [ ] Limpar backups antigos
- [ ] Sincronizar com nuvem
- [ ] Verificar logs de backup

### Antes de Updates
- [ ] Criar backup manual com descrição
- [ ] Verificar integridade do backup
- [ ] Fazer cópia de segurança adicional
- [ ] Testar restauração em ambiente de teste

---

**🍯 EJM Santos - Seus dados protegidos naturalmente**
