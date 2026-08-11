@echo off
echo ===================================================
echo   Compilando PointList v13 a APK de Android
echo ===================================================
echo.
REM Configurar codificacion UTF-8 para la consola de Windows
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM Agregar Git al PATH si esta instalado en ubicaciones comunes
if exist "C:\Program Files\Git\cmd" set PATH=C:\Program Files\Git\cmd;%PATH%
if exist "%LOCALAPPDATA%\Programs\Git\cmd" set PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%

set TEMPLATE_PATH=%USERPROFILE%\.cookiecutters\flet-build-template

echo Verificando instalacion de Flet y Git...
"%APPDATA%\Python\Python313\Scripts\flet.exe" --version
git --version
echo.
echo Iniciando compilacion de paquete APK (incluyendo .env y assets)...
"%APPDATA%\Python\Python313\Scripts\flet.exe" build apk ./ --icon assets/icon.png --project PointList --org com.pointlist.app --product "PointList" --build-version "1.0.0" --build-number 1 --template "%TEMPLATE_PATH%" --no-rich-output --exclude .venv __pycache__ .git .idea .vscode
echo.
if exist build\apk\app-release.apk (
    echo ===================================================
    echo   ¡Compilacion APK completada con exito!
    echo   Ubicacion del archivo APK: build\apk\app-release.apk
    echo ===================================================
) else (
    echo [INFORMACION] Si la compilacion finalizo, revisa la carpeta build\apk.
)
pause
