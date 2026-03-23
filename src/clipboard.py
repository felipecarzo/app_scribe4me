"""Envio do texto transcrito para clipboard ou cursor ativo."""

import time

import pyperclip
from pynput.keyboard import Controller, Key

from src.config import Config


class OutputHandler:
    """Envia texto transcrito para o destino configurado."""

    def __init__(self, config: Config):
        self.config = config
        self._keyboard = Controller()

    def send(self, text: str) -> None:
        """Envia texto usando o modo configurado (cursor ou clipboard)."""
        if not text:
            return

        if self.config.output_mode == "cursor":
            self._paste_at_cursor(text)
        else:
            self._copy_to_clipboard(text)

    def _copy_to_clipboard(self, text: str) -> None:
        """Copia texto para o clipboard."""
        pyperclip.copy(text)
        print(f"[output] Copiado para clipboard ({len(text)} chars)")

    def _paste_at_cursor(self, text: str) -> None:
        """Copia para clipboard e cola na posicao do cursor com Ctrl+V."""
        pyperclip.copy(text)
        time.sleep(0.05)
        self._keyboard.press(Key.ctrl)
        self._keyboard.press("v")
        self._keyboard.release("v")
        self._keyboard.release(Key.ctrl)
        print(f"[output] Colado no cursor ({len(text)} chars)")
