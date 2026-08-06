# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Recopilar submódulos y datos necesarios de flet
datas = [
    ('.env', '.'),
    ('assets', 'assets'),
    ('models', 'models'),
    ('services', 'services'),
    ('storage', 'storage'),
    ('utils', 'utils'),
    ('views', 'views'),
]

datas += collect_data_files('flet')

hiddenimports = [
    'flet',
    'flet.canvas',
    'pg8000',
    'scramp',
    'requests',
    'dateutil',
    'openai',
    'dotenv',
] + collect_submodules('flet') + collect_submodules('pg8000')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PointList',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Oculta la consola negra de comandos al ejecutar en Windows PC
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PointList',
)
