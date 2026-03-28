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

# Hotkeys padrao
DEFAULT_HOTKEYS = {
    "push_to_talk": "<ctrl>+<alt>+h",
    "toggle": "<ctrl>+<alt>+t",
    "quit": "<ctrl>+q",
}


def _load_config_data() -> dict:
    """Carrega o config.json inteiro como dict."""
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_config_data(data: dict) -> None:
    """Salva o dict inteiro no config.json."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_custom_prompt() -> str:
    """Carrega o prompt personalizado salvo, ou retorna string vazia."""
    return _load_config_data().get("custom_prompt", "")


def save_custom_prompt(prompt: str) -> None:
    """Salva o prompt personalizado no config.json."""
    data = _load_config_data()
    data["custom_prompt"] = prompt
    _save_config_data(data)


def load_hotkeys() -> dict[str, str]:
    """Carrega hotkeys do config.json, preenchendo com defaults."""
    saved = _load_config_data().get("hotkeys", {})
    result = dict(DEFAULT_HOTKEYS)
    for key in DEFAULT_HOTKEYS:
        if key in saved and saved[key]:
            result[key] = saved[key]
    return result


def save_hotkeys(hotkeys: dict[str, str]) -> None:
    """Salva hotkeys no config.json."""
    data = _load_config_data()
    data["hotkeys"] = hotkeys
    _save_config_data(data)


def parse_hotkey(hotkey_str: str) -> tuple[set[str], int | None]:
    """Converte string como '<ctrl>+<alt>+h' em (modifiers, vk_code).

    Retorna:
        (set de modificadores {'ctrl','alt','shift'}, vk_code da tecla principal)
    """
    parts = hotkey_str.lower().split("+")
    modifiers = set()
    vk = None
    for part in parts:
        part = part.strip()
        if part in ("<ctrl>", "ctrl"):
            modifiers.add("ctrl")
        elif part in ("<alt>", "alt"):
            modifiers.add("alt")
        elif part in ("<shift>", "shift"):
            modifiers.add("shift")
        elif part.startswith("<") and part.endswith(">"):
            # Tecla especial — ignora modificadores ja tratados
            pass
        else:
            # Letra ou tecla final
            if len(part) == 1:
                vk = ord(part.upper())
    return modifiers, vk


def hotkey_display(hotkey_str: str) -> str:
    """Converte '<ctrl>+<alt>+h' em 'Ctrl+Alt+H' para exibicao."""
    parts = hotkey_str.lower().split("+")
    display = []
    for part in parts:
        part = part.strip()
        if part in ("<ctrl>", "ctrl"):
            display.append("Ctrl")
        elif part in ("<alt>", "alt"):
            display.append("Alt")
        elif part in ("<shift>", "shift"):
            display.append("Shift")
        elif len(part) == 1:
            display.append(part.upper())
        else:
            display.append(part.strip("<>").capitalize())
    return "+".join(display)


@dataclass
class Config:
    # Whisper
    model: str = "large"
    language: str = "pt"
    device: str = "cuda"

    # Hotkeys (carregados do config.json ou defaults)
    hotkey_push_to_talk: str = field(default_factory=lambda: load_hotkeys()["push_to_talk"])
    hotkey_toggle: str = field(default_factory=lambda: load_hotkeys()["toggle"])
    hotkey_quit: str = field(default_factory=lambda: load_hotkeys()["quit"])

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
