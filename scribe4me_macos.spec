# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Scribe4me — macOS
# Usa faster-whisper (CTranslate2) — sem PyTorch

import os
import sys
from pathlib import Path

block_cipher = None

BASE = os.path.abspath('.')

# Detecta o diretorio do faster_whisper (funciona com ou sem venv)
import faster_whisper as _fw
_FW_DIR = os.path.dirname(_fw.__file__)

a = Analysis(
    ['run_scribe4me.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        (os.path.join(_FW_DIR, 'assets'), os.path.join('faster_whisper', 'assets')),
        (os.path.join(BASE, 'assets', 'scribe4me_256.png'), 'assets'),
    ],
    hiddenimports=[
        'faster_whisper',
        'ctranslate2',
        'sounddevice',
        'numpy',
        'pystray',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'PIL',
        # v1.5.0 — API backends + realtime
        'httpx',
        'httpx._transports.default',
        'websocket',
        'websocket._abnf',
        'soundfile',
        'src.transcriber_api',
        'src.realtime_manager',
        'src.realtime_overlay',
        'src.settings_window',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
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
    # icns gerado pelo workflow a partir do PNG
    icon=os.path.join(BASE, 'assets', 'scribe4me.icns'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Scribe4me',
)

# Bundle .app
app = BUNDLE(
    coll,
    name='Scribe4me.app',
    icon=os.path.join(BASE, 'assets', 'scribe4me.icns'),
    bundle_identifier='com.felipecarzo.scribe4me',
    info_plist={
        'CFBundleShortVersionString': '1.5.0',
        'CFBundleVersion': '1.5.0',
        'NSMicrophoneUsageDescription': 'Scribe4me precisa do microfone para gravar e transcrever voz.',
        'NSAppleEventsUsageDescription': 'Scribe4me usa AppleEvents para exibir dialogos de erro.',
        'LSUIElement': True,  # app de barra de status (sem icone no Dock)
        'NSHighResolutionCapable': True,
    },
)
