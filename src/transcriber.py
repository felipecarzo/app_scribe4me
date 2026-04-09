"""Interface com Whisper para transcricao (via faster-whisper / CTranslate2)."""

import time
import logging

import numpy as np
from faster_whisper import WhisperModel

from src.config import Config, load_custom_prompt
from src.postprocess import postprocess

logger = logging.getLogger("scribe4me")

# Prompt padrao que induz pontuacao natural no Whisper
_DEFAULT_PROMPT = (
    "Olá, tudo bem? Sim, estou trabalhando no projeto. "
    "Vamos resolver isso agora, ok? Preciso que você faça o seguinte: "
    "primeiro, abra o arquivo; depois, edite a configuração."
)


def _compute_type(device: str) -> str:
    """Retorna o compute_type ideal para o dispositivo."""
    if device == "cuda":
        return "float16"
    return "int8"


class Transcriber:
    """Transcreve audio usando faster-whisper (CTranslate2)."""

    def __init__(self, config: Config):
        self.config = config
        self._model: WhisperModel | None = None
        self._custom_prompt: str = load_custom_prompt()

    @property
    def prompt(self) -> str:
        """Retorna o prompt ativo (customizado ou padrao)."""
        return self._custom_prompt or _DEFAULT_PROMPT

    def set_custom_prompt(self, prompt: str) -> None:
        """Atualiza o prompt customizado em runtime."""
        self._custom_prompt = prompt
        logger.info("Prompt atualizado (%d chars).", len(prompt))

    def load_model(self) -> None:
        """Carrega o modelo Whisper (chamado uma vez no startup)."""
        if self._model is not None:
            return
        device = self.config.device
        compute = _compute_type(device)
        logger.info(
            "Carregando modelo Whisper '%s' em '%s' (compute_type=%s)...",
            self.config.model, device, compute,
        )
        try:
            self._model = WhisperModel(
                self.config.model,
                device=device,
                compute_type=compute,
                cpu_threads=4,
            )
        except Exception as e:
            if device == "cuda":
                logger.warning(
                    "CUDA indisponivel (%s), usando CPU como fallback.", e,
                )
                self.config.device = "cpu"
                self._model = WhisperModel(
                    self.config.model,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
            else:
                raise
        logger.info("Modelo carregado em '%s'.", self.config.device)

    def reload_model(self, model_name: str) -> None:
        """Troca o modelo Whisper (download automatico se necessario)."""
        logger.info("Trocando modelo para '%s'...", model_name)
        self.config.model = model_name
        self._model = None
        self.load_model()
        self.warm_up()
        logger.info("Modelo '%s' pronto.", model_name)

    def warm_up(self) -> None:
        """Faz uma transcricao dummy para aquecer o modelo."""
        if self._model is None:
            self.load_model()
        logger.info("Aquecendo modelo (warm-up)...")
        t0 = time.perf_counter()
        dummy = np.zeros(self.config.sample_rate, dtype=np.float32)
        segments, _ = self._model.transcribe(dummy, language=self.config.language)
        for _ in segments:
            pass
        elapsed = time.perf_counter() - t0
        logger.info("Warm-up concluido (%.1fs).", elapsed)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcreve audio (float32, mono, 16kHz) para texto.

        Retorna string vazia se audio for muito curto.
        """
        if self._model is None:
            self.load_model()

        if len(audio) < self.config.sample_rate * 0.3:
            return ""

        t0 = time.perf_counter()
        segments, _info = self._model.transcribe(
            audio,
            language=self.config.language,
            initial_prompt=self.prompt,
            condition_on_previous_text=False,
            beam_size=1,
            no_speech_threshold=0.6,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments)
        elapsed = time.perf_counter() - t0

        text = postprocess(text.strip())

        if text:
            duration = len(audio) / self.config.sample_rate
            logger.info(
                "%.1fs de audio -> %.1fs de processamento (ratio %.2fx)",
                duration, elapsed, elapsed / duration,
            )

        return text
