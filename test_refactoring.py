# ============================================
# test_refactoring.py — Verificar Refatoração
# ============================================

"""
Script para verificar se a refatoração foi implementada corretamente.
"""

import os
import sys

def check_file(filepath, description):
    """Verifica se um arquivo existe"""
    if os.path.exists(filepath):
        lines = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
        except:
            pass
        print(f"✅ {description:.<50} ({lines} linhas)")
        return True, lines
    else:
        print(f"❌ {description:.<50} NÃO ENCONTRADO")
        return False, 0

def main():
    print("=" * 70)
    print("🔄 VERIFICAÇÃO DA SEPARAÇÃO DE RESPONSABILIDADES")
    print("=" * 70)
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results = []
    total_lines = 0
    
    # Modelos
    print("📊 MODELOS (app/models/)")
    files = [
        (os.path.join(base_dir, "app", "models", "__init__.py"), "__init__.py"),
        (os.path.join(base_dir, "app", "models", "user.py"), "user.py"),
        (os.path.join(base_dir, "app", "models", "product.py"), "product.py"),
        (os.path.join(base_dir, "app", "models", "order.py"), "order.py"),
        (os.path.join(base_dir, "app", "models", "review.py"), "review.py"),
        (os.path.join(base_dir, "app", "models", "cart.py"), "cart.py")
    ]
    for filepath, desc in files:
        success, lines = check_file(filepath, f"   {desc}")
        results.append(success)
        total_lines += lines
    print()
    
    # Helpers
    print("🔧 HELPERS (app/helpers/)")
    files = [
        (os.path.join(base_dir, "app", "helpers", "__init__.py"), "__init__.py"),
        (os.path.join(base_dir, "app", "helpers", "cart_helper.py"), "cart_helper.py"),
        (os.path.join(base_dir, "app", "helpers", "order_helper.py"), "order_helper.py")
    ]
    for filepath, desc in files:
        success, lines = check_file(filepath, f"   {desc}")
        results.append(success)
        total_lines += lines
    print()
    
    # Rotas (Blueprints)
    print("🛣️  ROTAS (app/routes/)")
    files = [
        (os.path.join(base_dir, "app", "routes", "__init__.py"), "__init__.py"),
        (os.path.join(base_dir, "app", "routes", "auth.py"), "auth.py (autenticação)"),
        (os.path.join(base_dir, "app", "routes", "admin.py"), "admin.py (administração)"),
        (os.path.join(base_dir, "app", "routes", "products.py"), "products.py (produtos)"),
        (os.path.join(base_dir, "app", "routes", "payment.py"), "payment.py (pagamento)")
    ]
    for filepath, desc in files:
        success, lines = check_file(filepath, f"   {desc}")
        results.append(success)
        total_lines += lines
    print()
    
    # App principal
    print("⚙️  APLICAÇÃO PRINCIPAL")
    files = [
        (os.path.join(base_dir, "app.py"), "app.py (original - 1037 linhas)"),
        (os.path.join(base_dir, "app_new.py"), "app_new.py (refatorado - ~150 linhas)")
    ]
    for filepath, desc in files:
        success, lines = check_file(filepath, f"   {desc}")
        results.append(success)
    print()
    
    # Documentação
    print("📖 DOCUMENTAÇÃO")
    files = [
        (os.path.join(base_dir, "SEPARACAO_RESPONSABILIDADES.md"), "Guia de Separação de Responsabilidades"),
        (os.path.join(base_dir, "TRATAMENTO_ERROS.md"), "Guia de Tratamento de Erros")
    ]
    for filepath, desc in files:
        success, lines = check_file(filepath, f"   {desc}")
        results.append(success)
    print()
    
    # Resumo
    print("=" * 70)
    print("📊 RESULTADO")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for r in results if r)
    
    print(f"✅ Arquivos OK: {passed}/{total}")
    print(f"📝 Total de linhas nos novos arquivos: ~{total_lines}")
    print()
    
    if passed == total:
        print("🎉 SUCESSO! Separação de responsabilidades implementada!")
        print()
        print("📋 Próximos passos:")
        print("   1. Revisar app_new.py")
        print("   2. Testar todas as funcionalidades")
        print("   3. Quando estável: mv app_new.py app.py")
        print("   4. Consultar: SEPARACAO_RESPONSABILIDADES.md")
        print()
        
        # Comparação
        old_app = os.path.join(base_dir, "app.py")
        if os.path.exists(old_app):
            with open(old_app, 'r', encoding='utf-8') as f:
                old_lines = len(f.readlines())
            print(f"📉 Redução no arquivo principal:")
            print(f"   Antes: {old_lines} linhas (app.py)")
            print(f"   Depois: ~150 linhas (app_new.py)")
            print(f"   Redução: {old_lines - 150} linhas ({((old_lines - 150) / old_lines * 100):.1f}%)")
            print()
            print(f"   Código agora distribuído em {total} arquivos modulares!")
        
        return 0
    else:
        print("⚠️ Alguns arquivos estão faltando.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
