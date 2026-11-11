# PolyGen Interactive Launcher Script
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " POLYGEN – Generative Text-to-3D Asset Pipeline" -ForegroundColor White
Write-Host " Spatial Computing | 3D Graphics | Generative AI" -ForegroundColor DarkGray
Write-Host "===================================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $CurrentDir

# Check virtual environment
if (-not (Test-Path "$CurrentDir\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found at .\venv. Please run setup first." -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/2] Verifying FastAPI backend & static assets..." -ForegroundColor Green
Write-Host "Starting Unified PolyGen Service at http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host " - 3D Web Studio:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host " - REST API Docs:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host " - WebSocket Hub:   ws://127.0.0.1:8000/ws/jobs/{id}" -ForegroundColor White
Write-Host "`nPress Ctrl+C to terminate the server.`n" -ForegroundColor DarkGray

& "$CurrentDir\venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
