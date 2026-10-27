@echo off
title CloudBrowser - Instalacion rapida

echo ============================================
echo  CloudBrowser - Instalacion rapida
echo  Solo ejecutar en modo desarrollo (sin .exe)
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo Descargalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Instalando dependencias de Python...
pip install PyQt5>=5.15.0 PyQtWebEngine>=5.15.0

echo.
echo Instalacion completada.
echo Para ejecutar el navegador:
echo   python main.py
echo.
pause
