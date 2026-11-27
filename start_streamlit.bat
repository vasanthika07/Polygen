@echo off
title PolyGen - Streamlit Multimodal 3D Analytics Studio
echo ===================================================================
echo  POLYGEN - STREAMLIT MULTIMODAL 3D STUDIO
echo  Interactive Analytics, 3D WebGL Viewer, and Telemetry Dashboard
echo ===================================================================
cd /d "%~dp0"
call .\venv\Scripts\activate
streamlit run dashboard/streamlit_app.py --server.port 8501
pause
