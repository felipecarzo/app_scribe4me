"""Configuracoes do app_speedosper."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Nome do app (usado em menus, notificacoes, mutex, logs)
APP_NAME = os.environ.get("APP_BRAND", "SpeedOsper")


@dataclass
class Config:
    # Motor Ayvu (Rust ONNX backend)
    model: str = "large"  # mantido para compatibilidade (motor usa modelo fixo)
    language: str = "pt"
    device: str = "cuda"  # mantido para compatibilidade
    motor_dll_path: str = ""  # vazio = usa MOTOR_AYVU_DLL ou path padrao

    # Hotkeys (pynput — Ctrl+Alt+H push-to-talk, Ctrl+Alt+T toggle, Ctrl+Q sair)
    hotkey_push_to_talk: str = "<ctrl>+<alt>+h"
    hotkey_toggle: str = "<ctrl>+<alt>+t"
    hotkey_quit: str = "<ctrl>+q"

    # Saida
    # "cursor" = cola direto no cursor ativo (simula digitacao)
    # "clipboard" = copia pro clipboard
    output_mode: str = "cursor"

    # Audio
    sample_rate: int = 16000
    channels: int = 1

    # Tray / UI
    ready_to_copy_timeout: float = 10.0  # segundos no estado azul antes de voltar ao idle

    # Logging
    log_dir: str = field(default_factory=lambda: str(
        Path(os.environ.get("LOCALAPPDATA", ".")) / APP_NAME / "logs"
    ))
