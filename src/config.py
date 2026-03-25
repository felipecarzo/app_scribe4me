"""Configuracoes do Scribe4me."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Nome do app (usado em menus, notificacoes, mutex, logs)
APP_NAME = "Scribe4me"


@dataclass
class Config:
    # Whisper
    model: str = "large"
    language: str = "pt"
    device: str = "cuda"

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
