"""Configuracoes do Scribe4me."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

# Nome do app (usado em menus, notificacoes, mutex, logs)
APP_NAME = "Scribe4me"

# URL do repositorio (usado no Help)
GITHUB_URL = "https://github.com/felipecarzo/app_scribe4me"

# Diretorio de dados do app (%LOCALAPPDATA%/Scribe4me/)
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / APP_NAME

# Arquivo de configuracao persistente
_CONFIG_FILE = APP_DATA_DIR / "config.json"


def load_custom_prompt() -> str:
    """Carrega o prompt personalizado salvo, ou retorna string vazia."""
    try:
        if _CONFIG_FILE.exists():
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            return data.get("custom_prompt", "")
    except Exception:
        pass
    return ""


def save_custom_prompt(prompt: str) -> None:
    """Salva o prompt personalizado no config.json."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        if _CONFIG_FILE.exists():
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    data["custom_prompt"] = prompt
    _CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
