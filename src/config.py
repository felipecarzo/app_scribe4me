"""Configuracoes do app_speedosper."""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Nome do app (usado em menus, notificacoes, mutex, logs)
APP_NAME = os.environ.get("APP_BRAND", "SpeedOsper")


class AppMode(Enum):
    SCRIBE = "scribe"        # STT apenas — fala -> texto
    TRANSLATE = "translate"  # STT + traducao — fala -> texto traduzido
    VOICE = "voice"          # STT + traducao + TTS — fala -> voz traduzida


# Idiomas suportados pelo motor (NLLB-200 codes)
SUPPORTED_LANGUAGES = {
    "pt": "Portugues",
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "de": "Deutsch",
    "it": "Italiano",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ru": "Russian",
}


@dataclass
class Config:
    # Motor Ayvu (Rust ONNX backend)
    model: str = "large-v3"  # faster-whisper STT (large-v3 = melhor qualidade pt-BR)
    language: str = "pt"
    device: str = "cuda"  # mantido para compatibilidade
    motor_dll_path: str = ""  # vazio = usa MOTOR_AYVU_DLL ou path padrao

    # Modo de operacao
    mode: AppMode = AppMode.SCRIBE
    target_language: str = "en"  # idioma alvo para traducao (modo translate/voice)

    # Qualidade da transcricao
    beam_size: int = 1       # 1=rapido/greedy, 5=qualidade padrao, 8-10=maximo
    best_of: int = 3         # N candidatos (so atua com beam_size=1; com beam>1 e ignorado)

    # Profile ativo (nome do profile em %LOCALAPPDATA%/SpeedOsper/profiles/)
    active_profile_name: str = "Tech-Dev"

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
