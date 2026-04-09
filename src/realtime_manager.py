"""Transcricao em tempo real via Deepgram WebSocket."""

import json
import logging
import threading
import time
from typing import Callable

import numpy as np
import websocket

logger = logging.getLogger("scribe4me")

# Deepgram WebSocket endpoint
_WS_BASE = "wss://api.deepgram.com/v1/listen"


class DeepgramRealtimeManager:
    """Conecta ao Deepgram via WebSocket e transcreve audio em tempo real.

    Uso:
        manager = DeepgramRealtimeManager(api_key, on_partial=..., on_final=...)
        manager.start()
        # durante gravacao:
        manager.send_chunk(audio_chunk_float32)
        # ao terminar:
        final_text = manager.stop()
    """

    def __init__(
        self,
        api_key: str,
        language: str = "pt-BR",
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[str], None] | None = None,
        on_fragment: Callable[[str], None] | None = None,
    ):
        self._api_key = api_key
        self._language = language
        self.on_partial = on_partial
        self.on_final = on_final
        # on_fragment(sentence) — chamado com a frase nova confirmada (nao acumulada)
        # util para injetar texto no cursor em tempo real
        self.on_fragment = on_fragment

        self._ws: websocket.WebSocketApp | None = None
        self._thread: threading.Thread | None = None
        self._connected = threading.Event()
        self._closed = threading.Event()
        self._accumulated: list[str] = []  # frases finais confirmadas
        self._error: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Abre a conexao WebSocket com o Deepgram.

        Retorna True se conectado com sucesso dentro de 3s.
        """
        params = (
            f"model=nova-2"
            f"&language={self._language}"
            f"&punctuate=true"
            f"&interim_results=true"
            f"&smart_format=true"
            f"&encoding=linear16"
            f"&sample_rate=16000"
            f"&channels=1"
        )
        url = f"{_WS_BASE}?{params}"

        self._connected.clear()
        self._closed.clear()
        self._accumulated = []
        self._error = None

        self._ws = websocket.WebSocketApp(
            url,
            header={"Authorization": f"Token {self._api_key}"},
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._thread = threading.Thread(
            target=self._ws.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        )
        self._thread.start()

        connected = self._connected.wait(timeout=3.0)
        if not connected:
            logger.error("Deepgram realtime: timeout ao conectar.")
            return False
        logger.info("Deepgram realtime: conectado.")
        return True

    def send_chunk(self, audio_chunk: np.ndarray) -> None:
        """Envia chunk de audio (float32, mono) para o Deepgram.

        Converte para LINEAR16 (int16) antes de enviar.
        """
        if self._ws is None or not self._connected.is_set():
            return
        try:
            pcm = np.clip(audio_chunk, -1.0, 1.0)
            pcm_int16 = (pcm * 32767).astype(np.int16)
            self._ws.send(pcm_int16.tobytes(), websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.warning("Deepgram send_chunk error: %s", e)

    def stop(self) -> str:
        """Fecha o stream e retorna o texto final acumulado."""
        if self._ws is not None and self._connected.is_set():
            try:
                self._ws.send(json.dumps({"type": "CloseStream"}))
            except Exception:
                pass
            # Aguarda fechamento gracioso (max 3s)
            self._closed.wait(timeout=3.0)

        text = " ".join(self._accumulated).strip()
        logger.info("Deepgram realtime finalizado: %d chars.", len(text))
        return text

    # ------------------------------------------------------------------
    # WebSocket callbacks (thread do websocket)
    # ------------------------------------------------------------------

    def _on_open(self, ws) -> None:
        self._connected.set()

    def _on_message(self, ws, message: str) -> None:
        try:
            data = json.loads(message)
        except Exception:
            return

        msg_type = data.get("type")

        if msg_type == "Results":
            channel = data.get("channel", {})
            alts = channel.get("alternatives", [])
            if not alts:
                return
            transcript = alts[0].get("transcript", "").strip()
            is_final = data.get("is_final", False)
            speech_final = data.get("speech_final", False)

            if not transcript:
                return

            if is_final or speech_final:
                # Frase confirmada — adiciona ao acumulado
                self._accumulated.append(transcript)
                full = " ".join(self._accumulated)
                if self.on_fragment:
                    self.on_fragment(transcript)   # apenas a frase nova
                if self.on_final:
                    self.on_final(full)            # acumulado total (overlay)
                logger.debug("Deepgram final: %s", transcript)
            else:
                # Resultado parcial — mostra acumulado + parcial atual
                confirmed = " ".join(self._accumulated)
                partial = (confirmed + " " + transcript).strip() if confirmed else transcript
                if self.on_partial:
                    self.on_partial(partial)

        elif msg_type == "Metadata":
            logger.debug("Deepgram metadata: %s", data)

        elif msg_type == "Error":
            self._error = data.get("message", "unknown error")
            logger.error("Deepgram error: %s", self._error)

    def _on_error(self, ws, error) -> None:
        self._error = str(error)
        logger.error("Deepgram WS error: %s", error)
        self._connected.set()  # desbloqueia start() em caso de erro

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        logger.debug("Deepgram WS closed: %s %s", close_status_code, close_msg)
        self._closed.set()
