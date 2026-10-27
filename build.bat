@echo off
setlocal EnableDelayedExpansion
title Compilacion de CloudBrowser

echo ============================================
echo  CloudBrowser - Script de compilacion
echo ============================================
echo.

:: Verificar que Python este instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.9+ desde https://python.org
    pause
    exit /b 1
)

echo [1/4] Instalando dependencias...
pip install --upgrade pip -q
pip install PyQt5>=5.15.0 PyQtWebEngine>=5.15.0 pyinstaller -q
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

echo [2/4] Limpiando compilaciones anteriores...
if exist build\ rmdir /s /q build
if exist dist\ rmdir /s /q dist
if exist CloudBrowser.spec del /q CloudBrowser.spec

echo [3/4] Compilando ejecutable...
pyinstaller ^
    --name "CloudBrowser" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "requirements.txt;." ^
    --hidden-import PyQt5.QtWebEngineWidgets ^
    --hidden-import PyQt5.QtWebEngineCore ^
    --hidden-import PyQt5.QtWebEngineQuick ^
    --collect-all PyQt5 ^
    main.py

if errorlevel 1 (
    echo [ERROR] La compilacion fallo. Revisa los errores arriba.
    pause
    exit /b 1
)

echo [4/4] Verificando resultado...
if exist "dist\CloudBrowser\CloudBrowser.exe" (
    echo.
    echo ============================================
    echo  COMPILACION EXITOSA
    echo ============================================
    echo  Ejecutable: dist\CloudBrowser\CloudBrowser.exe
    echo  Carpeta:    dist\CloudBrowser\
    echo.
    echo  Puedes comprimir la carpeta dist\CloudBrowser\
    echo  y distribuirla en cualquier PC con Windows.
    echo ============================================
) else (
    echo [ERROR] El ejecutable no fue creado correctamente.
)

echo.
pause
