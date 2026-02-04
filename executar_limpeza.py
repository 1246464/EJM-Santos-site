# ============================================
# executar_limpeza.py — Limpeza Automática
# ============================================

"""
Executa a limpeza de forma automática.
Todos os arquivos removidos estão no .gitignore.
"""

import os
import shutil
import sys

def main():
    print("=" * 70)
    print("🧹 EXECUTANDO LIMPEZA AUTOMÁTICA")
    print("=" * 70)
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    removed_count = 0
    freed_space = 0
    
    # 1. Remover __pycache__
    pycache = os.path.join(base_dir, "__pycache__")
    if os.path.exists(pycache):
        try:
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(pycache)
                for filename in filenames
            )
            shutil.rmtree(pycache)
            freed_space += size
            removed_count += 1
            print(f"✅ Removido: __pycache__/ ({size/1024:.1f} KB)")
        except Exception as e:
            print(f"❌ Erro ao remover __pycache__: {e}")
    
    # 2. Remover app_refatorado.py
    app_refatorado = os.path.join(base_dir, "app_refatorado.py")
    if os.path.exists(app_refatorado):
        try:
            size = os.path.getsize(app_refatorado)
            os.remove(app_refatorado)
            freed_space += size
            removed_count += 1
            print(f"✅ Removido: app_refatorado.py ({size/1024:.1f} KB)")
        except Exception as e:
            print(f"❌ Erro ao remover app_refatorado.py: {e}")
    
    # 3. Remover outros arquivos .pyc se existirem
    for root, dirs, files in os.walk(base_dir):
        # Pular .venv e .git
        if '.venv' in root or '.git' in root:
            continue
        
        for file in files:
            if file.endswith('.pyc'):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    freed_space += size
                    removed_count += 1
                    print(f"✅ Removido: {os.path.relpath(filepath, base_dir)} ({size/1024:.1f} KB)")
                except Exception as e:
                    print(f"❌ Erro ao remover {file}: {e}")
    
    print()
    print("=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)
    print(f"Arquivos removidos: {removed_count}")
    print(f"Espaço liberado: {freed_space/1024:.1f} KB")
    print()
    
    if removed_count > 0:
        print("✅ Limpeza concluída com sucesso!")
        print()
        print("📋 Arquivos removidos estão no .gitignore")
        print("   Não afetarão o repositório GitHub")
    else:
        print("✅ Projeto já estava limpo!")
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
