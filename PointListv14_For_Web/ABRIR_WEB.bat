@echo off
title PointList v14 Web - Servidor Backend
echo ========================================================
echo   Iniciando PointList v14 - Version Web (HTML5/Flask)
echo ========================================================
echo.

cd /d "%~dp0"

echo Verificando entorno de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no se encuentra en el PATH.
    pause
    exit /b
)

echo Instalando/verificando dependencias necesarias...
pip install -r requirements.txt --quiet

echo.
echo Lanzando el servidor web en http://localhost:5000 ...
start http://localhost:5000

python app.py

pause
