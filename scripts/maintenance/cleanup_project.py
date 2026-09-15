# ============================================
# cleanup_project.py — Limpeza Segura do Projeto
# ============================================

"""
Script para identificar e limpar arquivos desnecessários do projeto.
CUIDADO: Conectado ao GitHub - cria backup antes de excluir!
"""

import os
import shutil
import sys
from datetime import datetime

class ProjectCleanup:
    """Gerenciador de limpeza do projeto"""
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.to_remove = []
        self.to_keep = []
        self.backup_dir = None
        
    def analyze(self):
        """Analisa o projeto e identifica arquivos para remover"""
        print("=" * 70)
        print("🔍 ANÁLISE DO PROJETO")
        print("=" * 70)
        print()
        
        # 1. Cache Python (__pycache__ e .pyc)
        self._check_python_cache()
        
        # 2. Arquivos duplicados/obsoletos
        self._check_duplicate_files()
        
        # 3. Arquivos de banco de desenvolvimento
        self._check_database_files()
        
        # 4. Logs antigos
        self._check_log_files()
        
        # 5. Arquivos de teste temporários
        self._check_test_files()
        
        # 6. Environments virtuais (opcional)
        self._check_virtual_env()
        
        return self.to_remove
    
    def _check_python_cache(self):
        """Verifica cache Python"""
        print("📦 Cache Python (__pycache__ e .pyc)")
        
        # __pycache__ directories
        pycache_dir = os.path.join(self.base_dir, "__pycache__")
        if os.path.exists(pycache_dir):
            self.to_remove.append({
                'path': pycache_dir,
                'type': 'directory',
                'reason': 'Cache Python (gerado automaticamente)',
                'safe': True,
                'gitignored': True
            })
            print(f"   ⚠️  __pycache__/ (será recriado automaticamente)")
        
        # .pyc files
        for root, dirs, files in os.walk(self.base_dir):
            if '.venv' in root or 'venv' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith('.pyc'):
                    filepath = os.path.join(root, file)
                    self.to_remove.append({
                        'path': filepath,
                        'type': 'file',
                        'reason': 'Arquivo compilado Python',
                        'safe': True,
                        'gitignored': True
                    })
                    print(f"   ⚠️  {os.path.relpath(filepath, self.base_dir)}")
        print()
    
    def _check_duplicate_files(self):
        """Verifica arquivos duplicados"""
        print("📄 Arquivos Duplicados/Obsoletos")
        
        # app_refatorado.py (substituído por application.py)
        app_refatorado = os.path.join(self.base_dir, "app_refatorado.py")
        if os.path.exists(app_refatorado):
            self.to_remove.append({
                'path': app_refatorado,
                'type': 'file',
                'reason': 'Versão antiga - substituída por application.py',
                'safe': True,
                'gitignored': False
            })
            print(f"   ⚠️  app_refatorado.py (versão antiga)")
        
        # Verificar se existe app_old.py
        app_old = os.path.join(self.base_dir, "app_old.py")
        if os.path.exists(app_old):
            self.to_remove.append({
                'path': app_old,
                'type': 'file',
                'reason': 'Backup antigo do app.py',
                'safe': False,  # Pode conter código útil
                'gitignored': False
            })
            print(f"   ⚠️  app_old.py (backup - VERIFICAR antes de excluir)")
        
        print()
    
    def _check_database_files(self):
        """Verifica arquivos de banco de dados"""
        print("🗄️  Banco de Dados")
        
        # instance/ejm.db (desenvolvimento)
        db_file = os.path.join(self.base_dir, "instance", "ejm.db")
        if os.path.exists(db_file):
            size = os.path.getsize(db_file) / 1024  # KB
            self.to_keep.append({
                'path': db_file,
                'reason': f'Banco de dados atual ({size:.1f} KB) - MANTER',
                'gitignored': True
            })
            print(f"   ✅ instance/ejm.db (banco atual - MANTIDO)")
        
        # Verificar backups de banco
        instance_dir = os.path.join(self.base_dir, "instance")
        if os.path.exists(instance_dir):
            for file in os.listdir(instance_dir):
                if file.endswith('.db') and file != 'ejm.db':
                    filepath = os.path.join(instance_dir, file)
                    self.to_remove.append({
                        'path': filepath,
                        'type': 'file',
                        'reason': 'Backup de banco de dados',
                        'safe': False,  # Pode ter dados importantes
                        'gitignored': True
                    })
                    print(f"   ⚠️  instance/{file} (backup)")
        
        print()
    
    def _check_log_files(self):
        """Verifica arquivos de log"""
        print("📋 Arquivos de Log")
        
        logs_dir = os.path.join(self.base_dir, "logs")
        if os.path.exists(logs_dir):
            for file in os.listdir(logs_dir):
                if file.endswith('.log'):
                    filepath = os.path.join(logs_dir, file)
                    size = os.path.getsize(filepath) / 1024  # KB
                    
                    # Logs maiores que 1MB podem ser limpos
                    if size > 1024:
                        self.to_remove.append({
                            'path': filepath,
                            'type': 'file',
                            'reason': f'Log grande ({size/1024:.1f} MB)',
                            'safe': True,
                            'gitignored': True
                        })
                        print(f"   ⚠️  logs/{file} ({size/1024:.1f} MB)")
                    else:
                        print(f"   ✅ logs/{file} ({size:.1f} KB - MANTIDO)")
        else:
            print(f"   ℹ️  Diretório logs/ não existe ainda")
        
        print()
    
    def _check_test_files(self):
        """Verifica arquivos de teste"""
        print("🧪 Arquivos de Teste")
        
        test_files = [
            'test_error_handling.py',
            'test_refactoring.py',
            'test_structure.py'
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.base_dir, filename)
            if os.path.exists(filepath):
                self.to_keep.append({
                    'path': filepath,
                    'reason': 'Script de teste útil - MANTER',
                    'gitignored': False
                })
                print(f"   ✅ {filename} (útil - MANTIDO)")
        
        print()
    
    def _check_virtual_env(self):
        """Verifica environment virtual"""
        print("🐍 Environment Virtual")
        
        venv_dir = os.path.join(self.base_dir, ".venv")
        if os.path.exists(venv_dir):
            try:
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(venv_dir)
                    for filename in filenames
                ) / (1024 * 1024)  # MB
                
                print(f"   ℹ️  .venv/ ({size:.1f} MB)")
                print(f"   ✅ MANTIDO (necessário para desenvolvimento)")
                print(f"   ℹ️  Já está no .gitignore")
            except:
                print(f"   ℹ️  .venv/ existe mas não pode calcular tamanho")
        else:
            print(f"   ℹ️  .venv/ não encontrado")
        
        print()
    
    def create_backup(self):
        """Cria backup antes de remover arquivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = os.path.join(self.base_dir, f"_backup_{timestamp}")
        
        print(f"📦 Criando backup em: {os.path.basename(self.backup_dir)}")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        for item in self.to_remove:
            if not item.get('safe', False):
                # Fazer backup de itens não seguros
                src = item['path']
                rel_path = os.path.relpath(src, self.base_dir)
                dst = os.path.join(self.backup_dir, rel_path)
                
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                if item['type'] == 'directory':
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                
                print(f"   ✅ Backup: {rel_path}")
        
        print()
    
    def remove_files(self, dry_run=True):
        """Remove arquivos identificados"""
        if dry_run:
            print("🔍 MODO SIMULAÇÃO (nenhum arquivo será excluído)")
            print()
        
        # Separar por segurança
        safe_items = [item for item in self.to_remove if item.get('safe', False)]
        unsafe_items = [item for item in self.to_remove if not item.get('safe', False)]
        
        print("=" * 70)
        print("✅ ARQUIVOS SEGUROS PARA REMOVER")
        print("=" * 70)
        for item in safe_items:
            rel_path = os.path.relpath(item['path'], self.base_dir)
            print(f"   {rel_path}")
            print(f"      Motivo: {item['reason']}")
        
        print()
        print("=" * 70)
        print("⚠️  ARQUIVOS QUE REQUEREM VERIFICAÇÃO MANUAL")
        print("=" * 70)
        for item in unsafe_items:
            rel_path = os.path.relpath(item['path'], self.base_dir)
            print(f"   {rel_path}")
            print(f"      Motivo: {item['reason']}")
            print(f"      ⚠️  VERIFICAR antes de excluir!")
        
        if not dry_run:
            print()
            print("Removendo arquivos seguros...")
            for item in safe_items:
                try:
                    if item['type'] == 'directory':
                        shutil.rmtree(item['path'])
                    else:
                        os.remove(item['path'])
                    print(f"   ✅ Removido: {os.path.relpath(item['path'], self.base_dir)}")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
        
        print()
    
    def update_gitignore(self):
        """Atualiza .gitignore com boas práticas"""
        print("=" * 70)
        print("📝 RECOMENDAÇÕES PARA .gitignore")
        print("=" * 70)
        
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        
        recommended = [
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            "",
            "# Environment",
            ".env",
            ".venv/",
            "venv/",
            "ENV/",
            "",
            "# Database",
            "*.db",
            "*.sqlite3",
            "instance/",
            "",
            "# Logs",
            "logs/",
            "*.log",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# Backups",
            "_backup_*/",
            "*.bak",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                current = f.read()
            
            missing = []
            for line in recommended:
                if line and not line.startswith('#') and line not in current:
                    missing.append(line)
            
            if missing:
                print("Adicionar ao .gitignore:")
                for item in missing:
                    print(f"   + {item}")
            else:
                print("✅ .gitignore está completo!")
        
        except FileNotFoundError:
            print("⚠️  .gitignore não encontrado!")
            print("Criar com:")
            for line in recommended:
                print(f"   {line}")
        
        print()


def main():
    """Executa a limpeza do projeto"""
    print("=" * 70)
    print("🧹 LIMPEZA SEGURA DO PROJETO EJM SANTOS")
    print("=" * 70)
    print()
    print("⚠️  ATENÇÃO: Projeto conectado ao GitHub")
    print("✅ Este script faz backup antes de excluir")
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cleaner = ProjectCleanup(base_dir)
    
    # 1. Análise
    items = cleaner.analyze()
    
    # 2. Resumo
    print("=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    safe_count = sum(1 for item in items if item.get('safe', False))
    unsafe_count = len(items) - safe_count
    
    print(f"Total de itens identificados: {len(items)}")
    print(f"   ✅ Seguros para remover: {safe_count}")
    print(f"   ⚠️  Requerem verificação: {unsafe_count}")
    print()
    
    # 3. Simulação (dry run)
    cleaner.remove_files(dry_run=True)
    
    # 4. Recomendações para .gitignore
    cleaner.update_gitignore()
    
    # 5. Instruções
    print("=" * 70)
    print("📋 PRÓXIMOS PASSOS")
    print("=" * 70)
    print()
    print("Para executar a limpeza:")
    print()
    print("1. REVISAR a lista de arquivos acima")
    print("2. CONFIRMAR que é seguro remover")
    print("3. Editar este script e mudar dry_run=False na linha 328")
    print("4. Executar novamente: python cleanup_project.py")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Backup será criado automaticamente")
    print("   - Apenas arquivos SEGUROS serão removidos automaticamente")
    print("   - Arquivos marcados ⚠️  requerem decisão manual")
    print()
    print("💡 DICA: Faça commit no Git antes de limpar!")
    print("   git add .")
    print("   git commit -m \"Backup antes da limpeza\"")
    print()


if __name__ == "__main__":
    sys.exit(main())
