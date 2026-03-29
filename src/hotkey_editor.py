"""Janela para configuracao de atalhos do Scribe4me."""

import threading
import tkinter as tk
from pynput import keyboard as kb

from src.config import (
    APP_NAME,
    load_hotkeys,
    save_hotkeys,
    hotkey_display,
)

# Labels amigaveis para cada acao
_ACTION_LABELS = {
    "push_to_talk": "Gravar (segura e fala)",
    "toggle": "Toggle (iniciar/parar)",
    "cancel": "Cancelar gravacao",
    "quit": "Sair",
}

# Ordem de exibicao
_ACTION_ORDER = ["push_to_talk", "toggle", "cancel", "quit"]


class _HotkeyCaptureButton(tk.Button):
    """Botao que, ao ser clicado, captura a proxima combinacao de teclas."""

    def __init__(self, master, hotkey_str: str, **kwargs):
        self._hotkey_str = hotkey_str
        super().__init__(
            master,
            text=hotkey_display(hotkey_str),
            width=22,
            font=("Segoe UI", 10, "bold"),
            **kwargs,
        )
        self._listener: kb.Listener | None = None
        self._pressed_mods: set[str] = set()
        self._capturing = False
        self.config(command=self._start_capture)

    @property
    def hotkey_str(self) -> str:
        return self._hotkey_str

    def _start_capture(self) -> None:
        """Inicia captura de teclas."""
        if self._capturing:
            return
        self._capturing = True
        self._pressed_mods = set()
        self.config(text="Pressione o atalho...", relief="sunken")

        self._listener = kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def _on_press(self, key) -> None:
        """Acumula modificadores; quando uma tecla final chega, registra."""
        if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
            self._pressed_mods.add("ctrl")
        elif key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
            self._pressed_mods.add("alt")
        elif key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
            self._pressed_mods.add("shift")
        else:
            # Tecla final — monta a combo
            char = None
            if hasattr(key, "char") and key.char is not None:
                char = key.char.lower()
            elif hasattr(key, "vk") and key.vk is not None:
                vk = key.vk
                if 65 <= vk <= 90:  # A-Z
                    char = chr(vk).lower()
                elif 48 <= vk <= 57:  # 0-9
                    char = chr(vk)

            if char and self._pressed_mods:
                parts = []
                for mod in ("ctrl", "alt", "shift"):
                    if mod in self._pressed_mods:
                        parts.append(f"<{mod}>")
                parts.append(char)
                self._hotkey_str = "+".join(parts)
                self._finish_capture()

    def _on_release(self, key) -> None:
        """Remove modificadores ao soltar."""
        if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
            self._pressed_mods.discard("ctrl")
        elif key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
            self._pressed_mods.discard("alt")
        elif key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
            self._pressed_mods.discard("shift")

        # Se soltou tudo sem tecla final, cancela
        if not self._pressed_mods and self._capturing:
            self._cancel_capture()

    def _finish_capture(self) -> None:
        """Finaliza captura com sucesso."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._capturing = False
        self.after(0, lambda: self.config(
            text=hotkey_display(self._hotkey_str),
            relief="raised",
        ))

    def _cancel_capture(self) -> None:
        """Cancela captura sem alterar o atalho."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._capturing = False
        self.after(0, lambda: self.config(
            text=hotkey_display(self._hotkey_str),
            relief="raised",
        ))

    def destroy(self) -> None:
        if self._listener:
            self._listener.stop()
        super().destroy()


def open_hotkey_editor(on_save=None):
    """Abre a janela de configuracao de atalhos em thread separada."""
    threading.Thread(target=lambda: _show_editor(on_save), daemon=True).start()


def _show_editor(on_save=None):
    """Cria e exibe a janela tkinter de edicao de atalhos."""
    root = tk.Tk()
    root.title(f"{APP_NAME} — Configurar atalhos")
    root.geometry("420x300")
    root.resizable(False, False)

    root.attributes("-topmost", True)
    root.after(100, lambda: root.attributes("-topmost", False))

    label = tk.Label(
        root,
        text="Clique no botao e pressione a nova combinacao de teclas:",
        anchor="w",
        padx=12,
        pady=8,
        font=("Segoe UI", 10),
    )
    label.pack(fill="x")

    hotkeys = load_hotkeys()
    buttons: dict[str, _HotkeyCaptureButton] = {}

    for action in _ACTION_ORDER:
        frame = tk.Frame(root)
        frame.pack(fill="x", padx=12, pady=4)

        tk.Label(
            frame,
            text=_ACTION_LABELS[action],
            width=22,
            anchor="w",
            font=("Segoe UI", 10),
        ).pack(side="left")

        btn = _HotkeyCaptureButton(frame, hotkeys[action])
        btn.pack(side="right")
        buttons[action] = btn

    hint = tk.Label(
        root,
        text="Use pelo menos 1 modificador (Ctrl, Alt, Shift) + 1 tecla.",
        fg="gray",
        font=("Segoe UI", 8),
        padx=12,
    )
    hint.pack(fill="x", pady=(8, 0))

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", padx=12, pady=12)

    def _save():
        new_hotkeys = {action: buttons[action].hotkey_str for action in _ACTION_ORDER}
        save_hotkeys(new_hotkeys)
        if on_save:
            on_save(new_hotkeys)
        root.destroy()

    def _reset():
        from src.config import DEFAULT_HOTKEYS
        for action in _ACTION_ORDER:
            buttons[action]._hotkey_str = DEFAULT_HOTKEYS[action]
            buttons[action].config(text=hotkey_display(DEFAULT_HOTKEYS[action]))

    tk.Button(btn_frame, text="Restaurar padrao", command=_reset, width=16).pack(side="left")
    tk.Button(btn_frame, text="Salvar", command=_save, width=10).pack(side="right")

    root.mainloop()
