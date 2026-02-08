# ============================================
# test_error_handling.py — Testes do Sistema de Erros
# ============================================

"""
Script para testar o sistema de tratamento de erros.
Execute: python test_error_handling.py
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_exceptions():
    """Testa as exceções customizadas"""
    print("🧪 Testando exceções customizadas...")
    
    try:
        from app.utils.exceptions import (
            EJMBaseException, ValidationError, AuthenticationError,
            AuthorizationError, NotFoundError, DatabaseError,
            EmailError, PaymentError, StockError, FileUploadError
        )
        print("✅ Todas as exceções foram importadas com sucesso")
        
        # Testar criação de exceção
        error = ValidationError("Teste de validação")
        assert error.status_code == 400
        assert error.message == "Teste de validação"
        print("✅ ValidationError funcionando corretamente")
        
        # Testar to_dict
        error_dict = error.to_dict()
        assert "message" in error_dict
        assert "status_code" in error_dict
        print("✅ Método to_dict() funcionando")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar exceções: {e}")
        return False


def test_logger():
    """Testa o sistema de logging"""
    print("\n🧪 Testando sistema de logging...")
    
    try:
        from app.utils.logger import setup_logger
        from flask import Flask
        
        app = Flask(__name__)
        logger = setup_logger(app)
        
        # Testar diferentes níveis de log
        logger.debug("Teste DEBUG")
        logger.info("Teste INFO")
        logger.warning("Teste WARNING")
        logger.error("Teste ERROR")
        
        print("✅ Sistema de logging funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar logger: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validators():
    """Testa os validadores"""
    print("\n🧪 Testando validadores...")
    
    try:
        from app.utils.validators import Validator
        
        # Testar validação de email
        valid, msg = Validator.validate_email("teste@example.com")
        assert valid == True
        print("✅ Validação de email válido")
        
        valid, msg = Validator.validate_email("email_invalido")
        assert valid == False
        print("✅ Rejeição de email inválido")
        
        # Testar validação de senha
        valid, msg = Validator.validate_password("senha123")
        assert valid == True
        print("✅ Validação de senha válida")
        
        valid, msg = Validator.validate_password("123")
        assert valid == False
        print("✅ Rejeição de senha curta")
        
        # Testar validação de nome
        valid, msg = Validator.validate_name("João Silva")
        assert valid == True
        print("✅ Validação de nome válido")
        
        valid, msg = Validator.validate_name("AB")
        assert valid == False
        print("✅ Rejeição de nome curto")
        
        # Testar validação de preço
        valid, msg = Validator.validate_price(29.90)
        assert valid == True
        print("✅ Validação de preço válido")
        
        valid, msg = Validator.validate_price(-10)
        assert valid == False
        print("✅ Rejeição de preço negativo")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar validadores: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_template():
    """Testa se o template de erro existe"""
    print("\n🧪 Testando template de erro...")
    
    try:
        template_path = os.path.join(
            os.path.dirname(__file__), 
            "templates", 
            "erro.html"
        )
        
        if os.path.exists(template_path):
            print(f"✅ Template de erro encontrado: {template_path}")
            
            # Verificar conteúdo básico
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "mensagem" in content
                assert "detalhes" in content
                print("✅ Template contém variáveis esperadas")
            
            return True
        else:
            print(f"❌ Template não encontrado: {template_path}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar template: {e}")
        return False


def test_documentation():
    """Verifica se a documentação existe"""
    print("\n🧪 Verificando documentação...")
    
    try:
        doc_path = os.path.join(
            os.path.dirname(__file__), 
            "TRATAMENTO_ERROS.md"
        )
        
        if os.path.exists(doc_path):
            print(f"✅ Documentação encontrada: {doc_path}")
            return True
        else:
            print(f"⚠️ Documentação não encontrada: {doc_path}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar documentação: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🛡️ TESTES DO SISTEMA DE TRATAMENTO DE ERROS")
    print("=" * 60)
    
    results = {
        "Exceções Customizadas": test_exceptions(),
        "Sistema de Logging": test_logger(),
        "Validadores": test_validators(),
        "Template de Erro": test_error_template(),
        "Documentação": test_documentation()
    }
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print("\n" + "=" * 60)
    print(f"Total: {passed}/{total} testes passaram")
    print("=" * 60)
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema funcionando corretamente.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
