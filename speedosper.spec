# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para app_speedosper v2
# Usa Motor Ayvu (Rust ONNX backend via ctypes FFI)

import os
import sys
from pathlib import Path

block_cipher = None

BASE = os.path.abspath('.')

# Path da DLL do motor ayvu
MOTOR_DLL = os.path.join(
    os.path.dirname(BASE), 'app_ayvu', 'motor', 'target', 'release', 'motor.dll'
)

# Dependencias ONNX Runtime que a DLL precisa
MOTOR_DIR = os.path.dirname(MOTOR_DLL)
ort_dlls = []
for f in os.listdir(MOTOR_DIR):
    if f.endswith('.dll') and f != 'motor.dll':
        ort_dlls.append((os.path.join(MOTOR_DIR, f), '.'))

a = Analysis(
    ['run.py'],
    pathex=[BASE],
    binaries=[
        (MOTOR_DLL, '.'),  # motor.dll na raiz do bundle
    ] + ort_dlls,
    datas=[],
    hiddenimports=[
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
        'faster_whisper',
        'ctranslate2',
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
    name='SpeedOsper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='SpeedOsper',
)
