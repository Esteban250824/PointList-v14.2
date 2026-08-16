@echo off
echo ===================================================
echo   Compilando PointList v13.5 a ejecutable Windows .exe
echo ===================================================
echo.
%APPDATA%\Python\Python313\Scripts\pyinstaller.exe pointlist.spec --noconfirm
echo.
if exist dist\PointList\PointList.exe (
    echo ===================================================
    echo   Compilacion exitosa! 
    echo   El ejecutable esta en: dist\PointList\PointList.exe
    echo ===================================================
) else (
    echo [ERROR] Ocurrio un error durante la compilacion.
)
pause
