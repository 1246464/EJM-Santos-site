# 🧪 Testes - EJM Santos

Esta pasta contém todos os testes automatizados do projeto.

## 📁 Arquivos de Teste

### Testes de Sistema
- **`test_backups.py`** - Testes do sistema de backup
- **`test_security.py`** - Testes de segurança (HTTPS, CSRF, Headers)
- **`test_error_handling.py`** - Testes de tratamento de erros
- **`test_structure.py`** - Testes de estrutura do projeto
- **`test_refactoring.py`** - Validação de refatoração

## 🚀 Como Executar

### Executar Todos os Testes

```bash
# Do diretório raiz do projeto
python tests/test_backups.py
python tests/test_security.py
python tests/test_error_handling.py
python tests/test_structure.py
python tests/test_refactoring.py
```

### Executar Teste Específico

```bash
# Teste de backups
python tests/test_backups.py

# Teste de segurança
python tests/test_security.py
```

## 📊 Cobertura de Testes

### ✅ Sistema de Backup
- [x] Criação de backup
- [x] Listagem de backups
- [x] Restauração de backup
- [x] Validação de integridade
- [x] Limpeza de backups antigos
- [x] Manifesto de backup

### 🔒 Segurança
- [x] Configurações HTTPS
- [x] Configurações CSRF
- [x] Headers de segurança
- [x] Content Security Policy
- [x] Middleware HTTPS
- [x] Meta tags CSRF
- [x] Helpers JavaScript

### 🛡️ Tratamento de Erros
- [x] Handlers customizados
- [x] Logging
- [x] Exceções personalizadas
- [x] Validadores

### 🏗️ Estrutura
- [x] Separação de responsabilidades
- [x] Organização de arquivos
- [x] Imports corretos
- [x] Configurações por ambiente

## 📝 Convenções de Teste

### Nomenclatura

```python
def test_nome_descritivo():
    """Descrição do que está sendo testado"""
    # Arrange - Preparar
    # Act - Executar
    # Assert - Verificar
```

### Estrutura de Teste

```python
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_funcionalidade():
    """Testa funcionalidade X"""
    try:
        # Setup
        # Teste
        # Verificação
        print("  ✅ Teste passou")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False
```

## 🔧 Adicionar Novos Testes

1. **Crie arquivo `test_*.py`** na pasta `tests/`
2. **Siga o padrão** dos testes existentes
3. **Documente** o que está testando
4. **Atualize este README**
5. **Execute** antes de commit

## ⚙️ Configuração de Ambiente

### Variáveis de Ambiente

Testes usam valores mock quando necessário:

```python
# Configurar antes de importar módulos
if 'EJM_SECRET' not in os.environ:
    os.environ['EJM_SECRET'] = 'test_secret_minimum_32_chars'
```

### Arquivos Temporários

Use `tempfile` para testes que criam arquivos:

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    # Testes aqui
    pass
```

## 📊 Executar com Coverage (Futuro)

```bash
# Instalar coverage
pip install coverage

# Executar com coverage
coverage run -m pytest tests/

# Ver relatório
coverage report
coverage html  # Relatório HTML em htmlcov/
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"

```python
# Adicione ao início do teste
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

### "Database locked" em testes

```python
# Use diretórios temporários
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    # Testes aqui
```

### Testes lentos

```python
# Use mocks para operações pesadas
from unittest.mock import Mock, patch

@patch('module.heavy_function')
def test_something(mock_func):
    mock_func.return_value = "resultado mock"
    # Teste
```

## ✅ Checklist Pré-Commit

- [ ] Todos os testes passam
- [ ] Nenhum teste ignorado sem justificativa
- [ ] Código novo tem testes
- [ ] Testes estão documentados
- [ ] Sem warnings durante execução

## 📚 Referências

- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [pytest](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**🍯 EJM Santos - Testes Naturalmente Confiáveis**
