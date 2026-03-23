"""Interface com Whisper para transcricao."""

import time

import numpy as np
import whisper

from src.config import Config
from src.postprocess import postprocess

# Prompt que induz pontuacao natural no Whisper
_PUNCTUATION_PROMPT = (
    "Olá, tudo bem? Sim, estou trabalhando no projeto. "
    "Vamos resolver isso agora, ok? Preciso que você faça o seguinte: "
    "primeiro, abra o arquivo; depois, edite a configuração."
)


class Transcriber:
    """Transcreve audio usando Whisper."""

    def __init__(self, config: Config):
        self.config = config
        self._model: whisper.Whisper | None = None

    def load_model(self) -> None:
        """Carrega o modelo Whisper (chamado uma vez no startup)."""
        if self._model is not None:
            return
        print(f"[transcriber] Carregando modelo Whisper '{self.config.model}' em '{self.config.device}'...")
        self._model = whisper.load_model(self.config.model, device=self.config.device)
        print("[transcriber] Modelo carregado.")

    def warm_up(self) -> None:
        """Faz uma transcricao dummy para aquecer CUDA JIT e kernels."""
        if self._model is None:
            self.load_model()
        print("[transcriber] Aquecendo modelo (warm-up)...")
        t0 = time.perf_counter()
        dummy = np.zeros(self.config.sample_rate, dtype=np.float32)
        self._model.transcribe(
            dummy,
            language=self.config.language,
            fp16=(self.config.device == "cuda"),
        )
        elapsed = time.perf_counter() - t0
        print(f"[transcriber] Warm-up concluido ({elapsed:.1f}s). Proximas transcricoes serao mais rapidas.")

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
        result = self._model.transcribe(
            audio,
            language=self.config.language,
            fp16=(self.config.device == "cuda"),
            initial_prompt=_PUNCTUATION_PROMPT,
            condition_on_previous_text=False,
            beam_size=1,
            no_speech_threshold=0.6,
        )
        elapsed = time.perf_counter() - t0
        text = postprocess(result["text"].strip())

        if text:
            duration = len(audio) / self.config.sample_rate
            print(f"[transcriber] {duration:.1f}s de audio -> {elapsed:.1f}s de processamento (ratio {elapsed/duration:.2f}x)")

        return text
