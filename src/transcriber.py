"""Interface com Whisper para transcricao (via Motor Ayvu — Rust ONNX backend)."""

import time
import logging

import numpy as np

from src.config import Config
from src.motor_bridge import MotorBridge
from src.postprocess import postprocess

logger = logging.getLogger("speedosper")


class Transcriber:
    """Transcreve audio usando Motor Ayvu (Whisper via ONNX Runtime)."""

    def __init__(self, config: Config):
        self.config = config
        self._bridge: MotorBridge | None = None

    def load_model(self) -> None:
        """Carrega o Motor Ayvu (chamado uma vez no startup)."""
        if self._bridge is not None:
            return
        logger.info("Carregando Motor Ayvu (model=%s, lang=%s)...",
                     self.config.model, self.config.language)
        try:
            dll_path = self.config.motor_dll_path or None
            self._bridge = MotorBridge(dll_path=dll_path)
            # Configura modelo Whisper antes da primeira transcricao
            model = self.config.model
            if model in ("tiny", "base", "small", "medium", "large"):
                ok = self._bridge.set_stt_model(model)
                if ok:
                    logger.info("Modelo STT configurado: %s", model)
                else:
                    logger.warning("Modelo STT ja inicializado — nao foi possivel trocar para '%s'.", model)
        except Exception as e:
            logger.error("Falha ao carregar Motor Ayvu: %s", e)
            raise
        logger.info("Motor Ayvu carregado — versao %s.", self._bridge.version())

    def reload_model(self, model_name: str) -> None:
        """Recarrega o motor com novo modelo Whisper.

        NOTA: OnceLock no Rust impede troca apos primeira transcricao.
        Reinicia o bridge para forcar nova inicializacao com modelo diferente.
        """
        logger.info("Reload solicitado (model=%s) — reiniciando bridge...", model_name)
        self.config.model = model_name
        self._bridge = None
        self.load_model()
        self.warm_up()
        logger.info("Motor Ayvu recarregado com modelo '%s'.", model_name)

    def warm_up(self) -> None:
        """Faz uma transcricao dummy para aquecer o motor."""
        if self._bridge is None:
            self.load_model()
        logger.info("Aquecendo Motor Ayvu (warm-up)...")
        t0 = time.perf_counter()
        dummy = np.zeros(self.config.sample_rate, dtype=np.float32)
        self._bridge.transcribe(dummy, lang=self.config.language)
        elapsed = time.perf_counter() - t0
        logger.info("Warm-up concluido (%.1fs).", elapsed)

    @property
    def is_loaded(self) -> bool:
        return self._bridge is not None

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcreve audio (float32, mono, 16kHz) para texto.

        Retorna string vazia se audio for muito curto.
        """
        if self._bridge is None:
            self.load_model()

        if len(audio) < self.config.sample_rate * 0.3:
            return ""

        t0 = time.perf_counter()
        text = self._bridge.transcribe(audio, lang=self.config.language)
        elapsed = time.perf_counter() - t0

        text = postprocess(text.strip())

        if text:
            duration = len(audio) / self.config.sample_rate
            logger.info(
                "%.1fs de audio -> %.1fs de processamento (ratio %.2fx)",
                duration, elapsed, elapsed / duration,
            )

        return text
