# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Scribe4me
# Usa faster-whisper (CTranslate2) — sem PyTorch

import os
import sys
from pathlib import Path

block_cipher = None

BASE = os.path.abspath('.')
VENV = os.environ.get('VIRTUAL_ENV', os.path.join(BASE, 'venv'))

a = Analysis(
    ['run_scribe4me.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        (os.path.join(VENV, 'Lib', 'site-packages', 'faster_whisper', 'assets'), os.path.join('faster_whisper', 'assets')),
    ],
    hiddenimports=[
        'faster_whisper',
        'ctranslate2',
        'sounddevice',
        'numpy',
        'pystray',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'torch',
        'torchaudio',
        'torchvision',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Scribe4me',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(BASE, 'assets', 'scribe4me.ico'),
    version=os.path.join(BASE, 'version_info.py'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Scribe4me',
)
