# PolyGen Gradio Launcher
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " POLYGEN – Gradio Multimodal 3D Studio" -ForegroundColor White
Write-Host " Running at http://127.0.0.1:7860" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $CurrentDir

& "$CurrentDir\venv\Scripts\python.exe" "$CurrentDir\dashboard\gradio_app.py"
