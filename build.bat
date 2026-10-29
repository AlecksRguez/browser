@echo off
setlocal EnableDelayedExpansion
title Compilacion de CloudBrowser

echo ============================================
echo  CloudBrowser - Script de compilacion
echo  Genera un .exe sin necesidad de instalar
echo  Python en el equipo destino.
echo ============================================
echo.

:: Verificar que Python este instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo Descargalo desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [1/4] Instalando dependencias de compilacion...
pip install --upgrade pip -q
pip install "PyQt5==5.15.11" "PyQtWebEngine==5.15.7" "pyinstaller==6.11.1" -q
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

echo [2/4] Limpiando compilaciones anteriores...
if exist build\ rmdir /s /q build
if exist dist\  rmdir /s /q dist

echo [3/4] Compilando con PyInstaller (puede tardar 2-5 minutos)...
pyinstaller CloudBrowser.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] La compilacion fallo. Revisa los errores arriba.
    pause
    exit /b 1
)

echo [4/4] Verificando y empaquetando...
if not exist "dist\CloudBrowser\CloudBrowser.exe" (
    echo [ERROR] El ejecutable no fue creado correctamente.
    pause
    exit /b 1
)

:: Crear ZIP listo para distribuir
powershell -Command "Compress-Archive -Path 'dist\CloudBrowser\*' -DestinationPath 'CloudBrowser-Windows-x64.zip' -Force"

echo.
echo ============================================
echo  COMPILACION EXITOSA
echo ============================================
echo.
echo  Para ejecutar directamente:
echo    dist\CloudBrowser\CloudBrowser.exe
echo.
echo  Para distribuir (sin instalar nada):
echo    CloudBrowser-Windows-x64.zip
echo    - Descomprime en cualquier carpeta
echo    - Ejecuta CloudBrowser.exe
echo.
echo  El equipo destino NO necesita Python.
echo ============================================
echo.
pause
