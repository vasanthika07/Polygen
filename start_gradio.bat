@echo off
title PolyGen - Gradio Multimodal 3D Studio
echo ===================================================================
echo  POLYGEN - GRADIO MULTIMODAL 3D STUDIO
echo  Image-to-3D, Text-to-3D, and Native 3D Model Viewport
echo ===================================================================
cd /d "%~dp0"
call .\venv\Scripts\activate
python dashboard/gradio_app.py
pause
