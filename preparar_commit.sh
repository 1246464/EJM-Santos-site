# ============================================
# preparar_commit.sh — Preparar Commit Git
# ============================================

# Este script prepara o commit com todas as mudanças

echo "======================================================================"
echo "📦 PREPARANDO COMMIT - EJM SANTOS"
echo "======================================================================"
echo ""

# 1. Remover arquivos deletados do Git
echo "🗑️  Removendo arquivos deletados do índice Git..."
git rm --cached __pycache__/api.cpython-313.pyc 2>/dev/null
git rm --cached __pycache__/app.cpython-313.pyc 2>/dev/null
git rm --cached __pycache__/email_service.cpython-313.pyc 2>/dev/null
git rm --cached app_refatorado.py 2>/dev/null
echo ""

# 2. Adicionar .gitignore atualizado
echo "📝 Adicionando .gitignore atualizado..."
git add .gitignore
echo ""

# 3. Adicionar novos arquivos importantes
echo "➕ Adicionando novos arquivos..."
git add app_new.py
git add app/models/
git add app/helpers/
git add app/routes/payment.py
git add app/routes/__init__.py
git add app/utils/exceptions.py
git add app/utils/error_handlers.py
git add app/utils/__init__.py
git add templates/erro.html
git add *.md
git add test_*.py
git add cleanup_project.py
echo ""

# 4. Adicionar modificações no app.py e outros
echo "✏️  Adicionando modificações..."
git add app.py
git add email_service.py
echo ""

# 5. Mostrar status
echo "======================================================================"
echo "📊 STATUS DO GIT"
echo "======================================================================"
git status
echo ""

echo "======================================================================"
echo "✅ PRONTO PARA COMMIT"
echo "======================================================================"
echo ""
echo "Próximos comandos sugeridos:"
echo ""
echo "1. Commit das mudanças:"
echo '   git commit -m "Refatoração: separação de responsabilidades e tratamento de erros"'
echo ""
echo "2. Push para GitHub:"
echo "   git push"
echo ""
echo "Ou criar commits separados:"
echo ""
echo '   git commit -m "Adicionar sistema de tratamento de erros"'
echo '   git commit -m "Implementar separação de responsabilidades"'
echo '   git commit -m "Atualizar .gitignore e limpar arquivos desnecessários"'
echo ""
