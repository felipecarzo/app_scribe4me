"""Configuracoes do app_speedosper."""

from dataclasses import dataclass, field


@dataclass
class Config:
    # Whisper
    model: str = "large"
    language: str = "pt"
    device: str = "cuda"

    # Hotkey
    hotkey_push_to_talk: str = "windows+h"
    hotkey_toggle: str = "windows+shift+h"

    # Saida
    # "cursor" = cola direto no cursor ativo (simula digitacao)
    # "clipboard" = copia pro clipboard
    output_mode: str = "cursor"

    # Audio
    sample_rate: int = 16000
    channels: int = 1
