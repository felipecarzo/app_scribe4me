"""Configuracoes do app_speedosper."""

from dataclasses import dataclass, field


@dataclass
class Config:
    # Whisper
    model: str = "large"
    language: str = "pt"
    device: str = "cuda"

    # Hotkey (teclas internas — AHK traduz Win+H -> F20, Win+Shift+H -> F21)
    hotkey_push_to_talk: str = "f20"
    hotkey_toggle: str = "f21"

    # Saida
    # "cursor" = cola direto no cursor ativo (simula digitacao)
    # "clipboard" = copia pro clipboard
    output_mode: str = "cursor"

    # Audio
    sample_rate: int = 16000
    channels: int = 1
