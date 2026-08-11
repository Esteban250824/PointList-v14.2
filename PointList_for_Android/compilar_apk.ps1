# Script para compilar PointList a APK de Android en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Compilando PointList v13 a APK de Android" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Agregar Git al PATH si está instalado en rutas estándar
if (Test-Path "C:\Program Files\Git\cmd") { $env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH }
if (Test-Path "$env:LOCALAPPDATA\Programs\Git\cmd") { $env:PATH = "$env:LOCALAPPDATA\Programs\Git\cmd;" + $env:PATH }

$flet_path = "$env:APPDATA\Python\Python313\Scripts\flet.exe"
$template_path = "$env:USERPROFILE\.cookiecutters\flet-build-template"

if (Test-Path $flet_path) {
    Write-Host "Flet CLI detectado:" -ForegroundColor Green
    & $flet_path --version
    Write-Host ""
    Write-Host "Iniciando compilacion de paquete APK (incluyendo .env y assets)..." -ForegroundColor Yellow
    & $flet_path build apk ./ --icon assets/icon.png --project PointList --org com.pointlist.app --product "PointList" --build-version "1.0.0" --build-number 1 --template $template_path --no-rich-output --exclude .venv __pycache__ .git .idea .vscode
    
    if (Test-Path "build\apk\app-release.apk") {
        Write-Host ""
        Write-Host "===================================================" -ForegroundColor Green
        Write-Host "  ¡Compilación APK completada con éxito!" -ForegroundColor Green
        Write-Host "  Ubicación del APK: build\apk\app-release.apk" -ForegroundColor Green
        Write-Host "===================================================" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] No se encontró Flet CLI en $flet_path" -ForegroundColor Red
}
