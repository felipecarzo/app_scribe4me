"""Interface com Whisper para transcricao."""

import numpy as np
import whisper

from src.config import Config


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

        result = self._model.transcribe(
            audio,
            language=self.config.language,
            fp16=(self.config.device == "cuda"),
            initial_prompt="Olá, tudo bem? Sim, estou trabalhando no projeto. Vamos resolver isso agora, ok? Preciso que você faça o seguinte: primeiro, abra o arquivo; depois, edite a configuração.",
        )
        return result["text"].strip()
