@echo off
title PointList v13.5
echo ===================================================
echo   Iniciando PointList v13.5 desde USB...
echo ===================================================
echo.

if exist dist\PointList\PointList.exe (
    start "" dist\PointList\PointList.exe
) else (
    echo [AVISO] No se encontro la version compilada en dist\PointList\PointList.exe.
    echo Ejecutando mediante Python local...
    python main.py
)
