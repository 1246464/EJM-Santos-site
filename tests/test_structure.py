# ============================================
# test_structure.py — Verificação de Estrutura
# ============================================

"""
Script para verificar se todos os arquivos do sistema de erros
foram criados corretamente.
"""

import os
import sys

def check_file_exists(filepath, description):
    """Verifica se um arquivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NÃO ENCONTRADO")
        return False

def check_file_content(filepath, keywords, description):
    """Verifica se um arquivo contém palavras-chave esperadas"""
    if not os.path.exists(filepath):
        print(f"❌ {description} - Arquivo não encontrado")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            missing = [k for k in keywords if k.lower() not in content]
            
            if not missing:
                print(f"✅ {description}")
                return True
            else:
                print(f"⚠️ {description} - Faltando: {', '.join(missing)}")
                return False
    except Exception as e:
        print(f"❌ {description} - Erro ao ler: {e}")
        return False

def main():
    """Executa todas as verificações"""
    print("=" * 70)
    print("🛡️ VERIFICAÇÃO DA ESTRUTURA DO SISTEMA DE TRATAMENTO DE ERROS")
    print("=" * 70)
    print()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results = []
    
    # 1. Verificar exceções customizadas
    print("📁 Exceções Customizadas")
    filepath = os.path.join(base_dir, "app", "utils", "exceptions.py")
    results.append(check_file_content(
        filepath,
        ["EJMBaseException", "ValidationError", "AuthenticationError", "NotFoundError"],
        "   Arquivo de exceções com todas as classes"
    ))
    print()
    
    # 2. Verificar error handlers
    print("📁 Error Handlers")
    filepath = os.path.join(base_dir, "app", "utils", "error_handlers.py")
    results.append(check_file_content(
        filepath,
        ["register_error_handlers", "errorhandler", "400", "404", "500"],
        "   Arquivo de handlers com funções principais"
    ))
    print()
    
    # 3. Verificar template de erro
    print("📁 Template de Erro")
    filepath = os.path.join(base_dir, "templates", "erro.html")
    results.append(check_file_content(
        filepath,
        ["mensagem", "detalhes", "extends", "base.html"],
        "   Template HTML com variáveis esperadas"
    ))
    print()
    
    # 4. Verificar documentação
    print("📁 Documentação")
    filepath = os.path.join(base_dir, "docs", "TRATAMENTO_ERROS.md")
    results.append(check_file_content(
        filepath,
        ["Sistema de Tratamento de Erros", "Exceções", "Logging", "Boas Práticas"],
        "   Documentação completa"
    ))
    print()
    
    filepath = os.path.join(base_dir, "docs", "RESUMO_TRATAMENTO_ERROS.md")
    results.append(check_file_exists(
        filepath,
        "   Resumo de implementação"
    ))
    print()
    
    # 5. Verificar integração na aplicação principal
    print("📁 Integração em application.py")
    filepath = os.path.join(base_dir, "application.py")
    results.append(check_file_content(
        filepath,
        ["setup_logger", "register_error_handlers", "try:", "except", "logger."],
        "   application.py com imports e tratamento de erros"
    ))
    print()
    
    # 6. Verificar modificações no email_service
    print("📁 Email Service")
    filepath = os.path.join(base_dir, "email_service.py")
    results.append(check_file_content(
        filepath,
        ["SMTPAuthenticationError", "SMTPException", "TimeoutError", "timeout=30"],
        "   email_service.py com tratamento de erros melhorado"
    ))
    print()
    
    # 7. Verificar __init__.py atualizado
    print("📁 Utils __init__.py")
    filepath = os.path.join(base_dir, "app", "utils", "__init__.py")
    results.append(check_file_content(
        filepath,
        ["register_error_handlers", "exceptions"],
        "   __init__.py com novos exports"
    ))
    print()
    
    # 8. Verificar estrutura de diretórios
    print("📁 Estrutura de Diretórios")
    dirs_to_check = [
        ("app", "Diretório app/"),
        (os.path.join("app", "utils"), "Diretório app/utils/"),
        ("templates", "Diretório templates/")
    ]
    
    for dir_path, desc in dirs_to_check:
        full_path = os.path.join(base_dir, dir_path)
        results.append(check_file_exists(full_path, f"   {desc}"))
    print()
    
    # Resumo
    print("=" * 70)
    print("📊 RESULTADO DA VERIFICAÇÃO")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for r in results if r)
    
    print(f"✅ Passou: {passed}/{total}")
    print(f"❌ Falhou: {total - passed}/{total}")
    print()
    
    if passed == total:
        print("🎉 SUCESSO! Todos os arquivos do sistema de erros estão presentes!")
        print()
        print("📝 Próximos passos:")
        print("   1. Instale as dependências: pip install -r requirements.txt")
        print("   2. Execute a aplicação: python application.py")
        print("   3. Teste as rotas e verifique os logs em: logs/")
        print("   4. Consulte docs/TRATAMENTO_ERROS.md para documentação completa")
        return 0
    else:
        print("⚠️ Alguns arquivos estão faltando ou incompletos.")
        print("   Verifique os itens marcados com ❌ acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
