# PolyGen Streamlit Launcher
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " POLYGEN – Streamlit Multimodal 3D Analytics Studio" -ForegroundColor White
Write-Host " Running at http://localhost:8501" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $CurrentDir

& "$CurrentDir\venv\Scripts\streamlit.exe" run "$CurrentDir\dashboard\streamlit_app.py" --server.port 8501
