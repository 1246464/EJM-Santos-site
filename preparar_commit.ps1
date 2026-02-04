# ============================================
# preparar_commit.ps1 — Preparar Commit Git (PowerShell)
# ============================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "📦 PREPARANDO COMMIT - EJM SANTOS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Remover arquivos deletados do Git
Write-Host "🗑️  Removendo arquivos deletados do índice Git..." -ForegroundColor Yellow
git rm --cached app_refatorado.py 2>$null
Write-Host ""

# 2. Adicionar .gitignore atualizado
Write-Host "📝 Adicionando .gitignore atualizado..." -ForegroundColor Green
git add .gitignore
Write-Host ""

# 3. Adicionar novos arquivos importantes
Write-Host "➕ Adicionando novos arquivos e diretórios..." -ForegroundColor Green
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
git add executar_limpeza.py
git add limpar_agora.py
Write-Host ""

# 4. Adicionar modificações
Write-Host "✏️  Adicionando modificações..." -ForegroundColor Green
git add app.py
git add email_service.py
Write-Host ""

# 5. Mostrar status
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "📊 STATUS DO GIT" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
git status
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "✅ PRONTO PARA COMMIT" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos comandos sugeridos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Commit único com todas as mudanças:" -ForegroundColor White
Write-Host '   git commit -m "Refatoração completa: separação de responsabilidades e tratamento de erros"' -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Ou fazer commits separados:" -ForegroundColor White
Write-Host '   git commit -m "Adicionar sistema completo de tratamento de erros"' -ForegroundColor Cyan
Write-Host '   Arquivos: app/utils/exceptions.py, error_handlers.py, templates/erro.html' -ForegroundColor DarkGray
Write-Host ""
Write-Host '   git commit -m "Implementar separação de responsabilidades"' -ForegroundColor Cyan
Write-Host '   Arquivos: app/models/, app/helpers/, app/routes/payment.py, app_new.py' -ForegroundColor DarkGray
Write-Host ""
Write-Host '   git commit -m "Melhorias e limpeza: .gitignore e documentação"' -ForegroundColor Cyan
Write-Host '   Arquivos: .gitignore, *.md, scripts de limpeza' -ForegroundColor DarkGray
Write-Host ""
Write-Host "3. Push para GitHub:" -ForegroundColor White
Write-Host "   git push" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Resumo das mudanças:" -ForegroundColor Yellow
Write-Host "   ✅ Sistema de tratamento de erros implementado" -ForegroundColor Green
Write-Host "   ✅ Separação de responsabilidades (app.py: 1050 → 155 linhas)" -ForegroundColor Green
Write-Host "   ✅ .gitignore atualizado com boas práticas" -ForegroundColor Green
Write-Host "   ✅ Arquivos desnecessários removidos" -ForegroundColor Green
Write-Host "   ✅ Documentação completa criada" -ForegroundColor Green
Write-Host ""
