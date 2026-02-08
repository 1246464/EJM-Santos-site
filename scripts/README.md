# 🔧 Scripts - EJM Santos

Esta pasta contém todos os scripts utilitários e de manutenção do projeto.

## 📁 Estrutura

### 💾 Backup (`backup/`)
Scripts para gerenciamento de backups:
- **`backup_manager.py`** - Gerenciador principal de backups
- **`backup_scheduler.py`** - Agendador de backups automáticos
- **`restore_backup.py`** - Restauração interativa de backups

**Documentação:** [GUIA_BACKUPS.md](../docs/GUIA_BACKUPS.md)

**Uso:**
```bash
# Criar backup
python scripts/backup/backup_manager.py create

# Agendar backup diário
python scripts/backup/backup_scheduler.py --schedule daily

# Restaurar backup
python scripts/backup/restore_backup.py
```

### 🗄️ Database (`database/`)
Scripts para gerenciamento do banco de dados:
- **`init_db.py`** - Inicialização do banco de dados
- **`recriar_db.py`** - Recriação completa do banco
- **`verificar_db.py`** - Verificação de integridade

**Uso:**
```bash
# Inicializar banco
python scripts/database/init_db.py

# Verificar integridade
python scripts/database/verificar_db.py

# Recriar banco (cuidado!)
python scripts/database/recriar_db.py
```

### 🚀 Deployment (`deployment/`)
Scripts para preparação de deploy:
- **`preparar_commit.ps1`** - Preparação de commit (Windows PowerShell)
- **`preparar_commit.sh`** - Preparação de commit (Linux/Mac)

**Uso:**
```bash
# Windows
.\scripts\deployment\preparar_commit.ps1

# Linux/Mac
./scripts/deployment/preparar_commit.sh
```

### 🧹 Maintenance (`maintenance/`)
Scripts de manutenção do projeto:
- **`cleanup_project.py`** - Limpeza de arquivos temporários

**Uso:**
```bash
python scripts/maintenance/cleanup_project.py
```

## ⚠️ Importante

### Antes de Executar Scripts

1. **Ative o ambiente virtual:**
   ```bash
   # Windows
   .venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

2. **Verifique variáveis de ambiente:**
   - Configure `.env` conforme `.env.example`

3. **Faça backup antes de operações destrutivas:**
   - Use `backup_manager.py` antes de `recriar_db.py`

### Permissões

**Linux/Mac:**
```bash
chmod +x scripts/deployment/*.sh
```

## 🔄 Ordem Recomendada

### Setup Inicial
```bash
1. python scripts/database/init_db.py          # Criar banco
2. python scripts/backup/backup_manager.py create  # Primeiro backup
```

### Manutenção Regular
```bash
1. python scripts/backup/backup_manager.py create  # Backup diário
2. python scripts/database/verificar_db.py         # Verificar integridade
3. python scripts/maintenance/cleanup_project.py   # Limpeza semanal
```

### Deploy
```bash
1. python scripts/backup/backup_manager.py create   # Backup pré-deploy
2. ./scripts/deployment/preparar_commit.sh          # Preparar código
3. git push                                         # Deploy
```

## 📝 Adicionar Novos Scripts

Ao criar um novo script:

1. **Coloque na categoria apropriada** (backup, database, etc.)
2. **Adicione docstring** no início do arquivo
3. **Inclua help** com `--help` argument
4. **Atualize este README**
5. **Adicione testes** em `tests/`

**Template básico:**
```python
#!/usr/bin/env python3
"""
Nome do Script - Descrição breve

Uso:
    python script.py [opções]

Exemplos:
    python script.py --help
"""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Descrição")
    # ... argumentos
    args = parser.parse_args()
    # ... lógica

if __name__ == '__main__':
    main()
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
# Verifique se está no ambiente virtual
pip install -r requirements.txt
```

### "Permission denied"
```bash
# Linux/Mac - adicione permissão de execução
chmod +x scripts/categoria/script.py
```

### "Database locked"
```bash
# Pare a aplicação antes de executar scripts de database
Ctrl+C  # no terminal da aplicação
```

---

**🍯 EJM Santos - Scripts Naturalmente Organizados**
