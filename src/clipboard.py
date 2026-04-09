"""Envio do texto transcrito para clipboard ou cursor ativo."""

import logging
import time

import pyperclip
from pynput.keyboard import Controller, Key

from src.config import Config

logger = logging.getLogger("scribe4me")


class OutputHandler:
    """Envia texto transcrito para o destino configurado."""

    def __init__(self, config: Config):
        self.config = config
        self._keyboard = Controller()
        self._last_text: str = ""

    @property
    def last_text(self) -> str:
        """Retorna o ultimo texto enviado."""
        return self._last_text

    def send(self, text: str) -> None:
        """Envia texto usando o modo configurado (cursor ou clipboard)."""
        if not text:
            return
        self._last_text = text

        if self.config.output_mode == "cursor":
            self._paste_at_cursor(text)
        else:
            self._copy_to_clipboard(text)

    def _copy_to_clipboard(self, text: str) -> None:
        """Copia texto para o clipboard."""
        pyperclip.copy(text)
        logger.info("Copiado para clipboard (%d chars)", len(text))

    def _paste_at_cursor(self, text: str) -> None:
        """Copia para clipboard e cola na posicao do cursor com Ctrl+V."""
        pyperclip.copy(text)
        time.sleep(0.05)
        self._keyboard.press(Key.ctrl)
        self._keyboard.press("v")
        self._keyboard.release("v")
        self._keyboard.release(Key.ctrl)
        logger.info("Colado no cursor (%d chars)", len(text))
