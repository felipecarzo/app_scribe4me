"""Prefetch de modelos ONNX do Motor Ayvu no primeiro uso.

Na primeira execucao, os modelos sao baixados do HuggingFace:
- Whisper-base (~200 MB) — STT
- M2M-100 (~1.2 GB) — traducao
- MMS-TTS (~50 MB por idioma) — sintese de voz
- paraphrase-MiniLM (~465 MB) — embeddings

Downloads subsequentes usam cache local (~/.cache/huggingface/hub/).
"""

import logging
import threading
from typing import Callable

import numpy as np

from src.motor_bridge import MotorBridge

logger = logging.getLogger("speedosper.prefetch")

# Modelos e sua ordem de download
_STEPS = [
    ("STT (Whisper)", "stt"),
    ("Traducao (M2M-100)", "translate"),
    ("TTS (MMS-TTS)", "tts"),
]


def prefetch_models(
    bridge: MotorBridge,
    language: str = "pt",
    target_language: str = "en",
    on_progress: Callable[[str, int, int], None] | None = None,
) -> bool:
    """Aciona download de todos os modelos necessarios.

    Args:
        bridge: MotorBridge ja inicializado.
        language: Idioma de origem (para STT e TTS).
        target_language: Idioma alvo (para traducao e TTS).
        on_progress: Callback (step_name, current, total) para feedback.

    Returns:
        True se todos os modelos foram carregados com sucesso.
    """
    total = len(_STEPS)
    success = True

    for i, (name, step_type) in enumerate(_STEPS):
        if on_progress:
            on_progress(name, i + 1, total)
        logger.info("Prefetch [%d/%d]: %s...", i + 1, total, name)

        try:
            if step_type == "stt":
                # Transcricao dummy aciona download do Whisper
                dummy = np.zeros(16000, dtype=np.float32)
                bridge.transcribe(dummy, lang=language)

            elif step_type == "translate":
                # Traducao dummy aciona download do M2M-100
                bridge.translate("teste", language, target_language)

            elif step_type == "tts":
                # Sintese dummy aciona download do MMS-TTS
                bridge.synthesize("teste", target_language)

            logger.info("Prefetch [%d/%d]: %s OK", i + 1, total, name)

        except Exception as e:
            logger.warning("Prefetch [%d/%d]: %s falhou: %s", i + 1, total, name, e)
            success = False

    return success


def prefetch_models_async(
    bridge: MotorBridge,
    language: str = "pt",
    target_language: str = "en",
    on_progress: Callable[[str, int, int], None] | None = None,
    on_complete: Callable[[bool], None] | None = None,
) -> threading.Thread:
    """Versao async do prefetch — roda em thread separada."""
    def _run():
        ok = prefetch_models(bridge, language, target_language, on_progress)
        if on_complete:
            on_complete(ok)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
