# Script para reiniciar o servidor Flask
Write-Host "`n🔄 REINICIANDO SERVIDOR FLASK...`n" -ForegroundColor Yellow

# 1. Matar processos Python que estão rodando application.py
Write-Host "1️⃣ Parando servidor..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*ejm-santos*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# 2. Limpar cache Python
Write-Host "2️⃣ Limpando cache Python..." -ForegroundColor Cyan
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force | Remove-Item -Force -ErrorAction SilentlyContinue

# 3. Ativar ambiente virtual e iniciar servidor
Write-Host "3️⃣ Iniciando servidor...`n" -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1
Start-Process python -ArgumentList "application.py" -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "`n✅ Servidor reiniciado!" -ForegroundColor Green
Write-Host "📡 Acesse: http://localhost:5000" -ForegroundColor Green
Write-Host "`n💡 Abra o navegador em modo anônimo (Ctrl+Shift+N) para limpar cache`n" -ForegroundColor Yellow
