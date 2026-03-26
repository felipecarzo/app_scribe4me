"""Envio do texto transcrito para clipboard ou cursor ativo."""

from __future__ import annotations

import logging
import time

import pyperclip
from pynput.keyboard import Controller, Key

from src.config import Config

logger = logging.getLogger("speedosper")

# Mapa de nomes de tecla (string) para objetos Key do pynput
_KEY_MAP = {
    "backspace": Key.backspace,
    "enter": Key.enter,
    "tab": Key.tab,
    "delete": Key.delete,
    "escape": Key.esc,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "home": Key.home,
    "end": Key.end,
}

_MOD_MAP = {
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "shift": Key.shift,
}


def _parse_keypress(keypress: str) -> tuple[Key | str, list[Key]]:
    """Converte string tipo 'ctrl+z' em (key, [modifiers])."""
    parts = keypress.lower().split("+")
    modifiers = []
    for part in parts[:-1]:
        mod = _MOD_MAP.get(part)
        if mod:
            modifiers.append(mod)
    key_str = parts[-1]
    key = _KEY_MAP.get(key_str, key_str)
    return key, modifiers


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

    def send_keypress(self, key: Key | str, modifiers: list[Key] | None = None) -> None:
        """Simula pressionamento de tecla (para comandos de navegacao)."""
        if modifiers:
            for mod in modifiers:
                self._keyboard.press(mod)
        self._keyboard.press(key)
        self._keyboard.release(key)
        if modifiers:
            for mod in reversed(modifiers):
                self._keyboard.release(mod)

    def send_command_results(self, results: list) -> None:
        """Processa lista de CommandResult — texto e/ou keypresses.

        Args:
            results: lista de CommandResult do voice_commands engine.
        """
        for result in results:
            if result.keypress:
                key, modifiers = _parse_keypress(result.keypress)
                self.send_keypress(key, modifiers)
                logger.info("Keypress: %s", result.keypress)
            elif result.text:
                self._keyboard.type(result.text)
                logger.info("Code output: %r", result.text)

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
