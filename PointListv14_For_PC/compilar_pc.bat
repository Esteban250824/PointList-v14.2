@echo off
echo ===================================================
echo   Compilando PointList v13.5 a ejecutable Windows .exe
echo ===================================================
echo.
%APPDATA%\Python\Python313\Scripts\pyinstaller.exe pointlist.spec --noconfirm
echo.
if exist dist\PointList\PointList.exe (
    REM Eliminar .env suelto en dist si existiera para mantener las credenciales seguras y protegidas dentro del ejecutable
    if exist dist\PointList\.env del /f /q dist\PointList\.env
    echo ===================================================
    echo   ¡Compilacion exitosa y segura! 
    echo   El ejecutable esta en: dist\PointList\PointList.exe
    echo   (Las variables de entorno han sido empaquetadas internamente)
    echo ===================================================
) else (
    echo [ERROR] Ocurrio un error durante la compilacion.
)
pause
