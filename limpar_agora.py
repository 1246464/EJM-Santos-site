# ============================================
# limpar_agora.py — Execução da Limpeza
# ============================================

"""
Script simplificado para executar a limpeza com segurança.
Versão pronta para uso.
"""

import os
import shutil
import sys

def confirm(message):
    """Pede confirmação do usuário"""
    response = input(f"{message} (s/N): ").strip().lower()
    return response == 's'

def main():
    print("=" * 70)
    print("🧹 LIMPEZA DO PROJETO")
    print("=" * 70)
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lista de itens a remover
    to_remove = []
    
    # 1. __pycache__
    pycache = os.path.join(base_dir, "__pycache__")
    if os.path.exists(pycache):
        to_remove.append(("__pycache__/", pycache, "directory"))
    
    # 2. app_refatorado.py
    app_refatorado = os.path.join(base_dir, "app_refatorado.py")
    if os.path.exists(app_refatorado):
        to_remove.append(("app_refatorado.py", app_refatorado, "file"))
    
    if not to_remove:
        print("✅ Projeto já está limpo!")
        return 0
    
    # Mostrar o que será removido
    print("Os seguintes itens serão REMOVIDOS:")
    print()
    for name, path, type_item in to_remove:
        if type_item == "directory":
            try:
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(path)
                    for filename in filenames
                ) / 1024  # KB
                print(f"   📁 {name} ({size:.1f} KB)")
            except:
                print(f"   📁 {name}")
        else:
            size = os.path.getsize(path) / 1024  # KB
            print(f"   📄 {name} ({size:.1f} KB)")
    
    print()
    print("⚠️  Estes arquivos estão no .gitignore e não afetarão o repositório")
    print()
    
    # Confirmar
    if not confirm("Deseja continuar com a limpeza?"):
        print("❌ Operação cancelada")
        return 1
    
    # Executar limpeza
    print()
    print("Removendo arquivos...")
    print()
    
    for name, path, type_item in to_remove:
        try:
            if type_item == "directory":
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"   ✅ Removido: {name}")
        except Exception as e:
            print(f"   ❌ Erro ao remover {name}: {e}")
    
    print()
    print("=" * 70)
    print("✅ LIMPEZA CONCLUÍDA!")
    print("=" * 70)
    print()
    print("📋 Próximos passos:")
    print("   1. Verificar que tudo está funcionando: python app.py")
    print("   2. Fazer commit das mudanças no .gitignore")
    print("   3. Os arquivos removidos estão no .gitignore")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
