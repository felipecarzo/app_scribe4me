"""Janela para edicao do prompt personalizado do Whisper."""

import sys
import threading
import tkinter as tk
from tkinter import scrolledtext

_FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "sans-serif"

from src.config import APP_NAME, load_custom_prompt, save_custom_prompt

_DEFAULT_HINT = (
    "Cole aqui um texto de exemplo no estilo que voce quer que a transcricao siga.\n"
    "O Whisper usa esse prompt como referencia para pontuacao e formatacao.\n\n"
    "Deixe vazio para usar o prompt padrao do Scribe4me."
)


def open_prompt_editor(on_save=None):
    """Abre a janela de edicao do prompt em thread separada."""
    threading.Thread(target=lambda: _show_editor(on_save), daemon=True).start()


def _show_editor(on_save=None):
    """Cria e exibe a janela tkinter."""
    root = tk.Tk()
    root.title(f"{APP_NAME} — Prompt personalizado")
    root.geometry("560x380")
    root.resizable(True, True)

    # Tenta trazer a janela pro frente
    root.attributes("-topmost", True)
    root.after(100, lambda: root.attributes("-topmost", False))

    label = tk.Label(
        root,
        text="Prompt personalizado (texto de referencia para o Whisper):",
        anchor="w",
        padx=8,
        pady=4,
    )
    label.pack(fill="x")

    text_area = scrolledtext.ScrolledText(root, wrap="word", font=(_FONT_FAMILY, 10))
    text_area.pack(fill="both", expand=True, padx=8, pady=(0, 4))

    current = load_custom_prompt()
    if current:
        text_area.insert("1.0", current)
    else:
        text_area.insert("1.0", _DEFAULT_HINT)
        text_area.config(fg="gray")

        def _on_focus(event):
            if text_area.get("1.0", "end-1c") == _DEFAULT_HINT:
                text_area.delete("1.0", "end")
                text_area.config(fg="black")

        text_area.bind("<FocusIn>", _on_focus)

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", padx=8, pady=8)

    def _save():
        content = text_area.get("1.0", "end-1c").strip()
        if content == _DEFAULT_HINT:
            content = ""
        save_custom_prompt(content)
        if on_save:
            on_save(content)
        root.destroy()

    def _clear():
        text_area.delete("1.0", "end")
        text_area.config(fg="black")

    tk.Button(btn_frame, text="Limpar", command=_clear, width=10).pack(side="left")
    tk.Button(btn_frame, text="Salvar", command=_save, width=10).pack(side="right")

    root.mainloop()
