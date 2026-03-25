"""Playback de audio PCM f32 via sounddevice."""

import logging
import threading

import numpy as np
import sounddevice as sd

logger = logging.getLogger("speedosper.player")


class AudioPlayer:
    """Reproduz audio PCM float32 mono."""

    def __init__(self):
        self._playing = False
        self._lock = threading.Lock()

    @property
    def is_playing(self) -> bool:
        return self._playing

    def play(self, samples: np.ndarray, sample_rate: int, blocking: bool = False) -> None:
        """Reproduz audio.

        Args:
            samples: Array float32 mono normalizado [-1.0, 1.0].
            sample_rate: Taxa de amostragem (ex: 22050).
            blocking: Se True, bloqueia ate terminar. Se False, reproduz em thread.
        """
        if len(samples) == 0:
            logger.warning("Audio vazio, nada para reproduzir.")
            return

        samples = np.ascontiguousarray(samples, dtype=np.float32)

        if blocking:
            self._play_sync(samples, sample_rate)
        else:
            thread = threading.Thread(
                target=self._play_sync, args=(samples, sample_rate), daemon=True
            )
            thread.start()

    def _play_sync(self, samples: np.ndarray, sample_rate: int) -> None:
        """Reproduz audio de forma sincrona."""
        with self._lock:
            self._playing = True
            try:
                logger.info(
                    "Reproduzindo: %.1fs de audio a %dHz",
                    len(samples) / sample_rate, sample_rate,
                )
                sd.play(samples, samplerate=sample_rate)
                sd.wait()
                logger.info("Playback concluido.")
            except Exception as e:
                logger.error("Erro no playback: %s", e)
            finally:
                self._playing = False

    def stop(self) -> None:
        """Para a reproducao em andamento."""
        sd.stop()
        self._playing = False
