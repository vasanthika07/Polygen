@echo off
echo ===================================================================
echo Starting PolyGen - Generative Text-to-3D Asset Pipeline
echo ===================================================================
echo.
echo Launching FastAPI backend server at http://127.0.0.1:8000 ...
echo Interactive 3D Web UI available at http://127.0.0.1:8000
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

pause
