# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para CloudBrowser (Windows x64)
# Genera una carpeta self-contained: dist\CloudBrowser\CloudBrowser.exe
# No requiere Python ni ninguna dependencia en el equipo destino.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Módulos locales
        'window',
        'interceptor',
        'dns_setup',
        # Qt / WebEngine — PyInstaller no los detecta automáticamente
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebChannel',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtNetwork',
        'PyQt5.sip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Excluir módulos innecesarios para reducir tamaño
    excludes=[
        'tkinter', '_tkinter',
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'Pillow',
        'IPython', 'jupyter',
        'PyQt5.Qt3DAnimation', 'PyQt5.Qt3DCore', 'PyQt5.Qt3DExtras',
        'PyQt5.Qt3DInput', 'PyQt5.Qt3DLogic', 'PyQt5.Qt3DRender',
        'PyQt5.QtCharts', 'PyQt5.QtDataVisualization',
        'PyQt5.QtDesigner', 'PyQt5.QtHelp',
        'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtRemoteObjects', 'PyQt5.QtSensors', 'PyQt5.QtSerialPort',
        'PyQt5.QtSql', 'PyQt5.QtTest', 'PyQt5.QtTextToSpeech',
        'PyQt5.QtVirtualKeyboard',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CloudBrowser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # UPX puede corromper DLLs de Qt — mantener en False
    console=False,    # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CloudBrowser',
)
