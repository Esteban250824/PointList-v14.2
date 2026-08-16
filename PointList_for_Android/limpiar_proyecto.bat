@echo off
echo ===================================================
echo   Limpiando proyecto PointList para transporte USB
echo ===================================================
echo.
echo Eliminando archivos de compilacion y temporales...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist .venv rmdir /s /q .venv

for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo.
echo ===================================================
echo   ¡Limpieza completada! 
echo   El proyecto esta ligero y listo para copiar a tu USB.
echo ===================================================
pause
