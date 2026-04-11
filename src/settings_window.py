"""Janela de configuracoes unificada do Scribe4me.

Abas: Geral (modelo + modo de saida), Atalhos, Prompt, API.
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable

from pynput import keyboard as kb

from src.config import (
    APP_NAME,
    DEFAULT_HOTKEYS,
    SUPPORTED_API_BACKENDS,
    hotkey_display,
    load_api_config,
    load_api_keys,
    load_custom_prompt,
    load_hotkeys,
    load_output_mode,
    save_api_config,
    save_api_keys,
    save_custom_prompt,
    save_hotkeys,
    save_output_mode,
)
from src.hardware import WHISPER_MODELS, model_label

_FONT = "Segoe UI" if sys.platform == "win32" else "sans-serif"

_BACKEND_LABELS = {
    "local":    "Local (Whisper — sem API)",
    "openai":   "OpenAI (whisper-1)",
    "groq":     "Groq (whisper-large-v3 — gratis)",
    "gemini":   "Gemini Flash (Google)",
    "deepgram": "Deepgram Nova-2 (realtime disponivel)",
}

_ACTION_LABELS = {
    "push_to_talk": "Gravar (segura e fala)",
    "toggle":       "Toggle (iniciar/parar)",
    "cancel":       "Cancelar gravacao",
    "quit":         "Sair",
}
_ACTION_ORDER = ["push_to_talk", "toggle", "cancel", "quit"]

_DEFAULT_PROMPT_HINT = (
    "Cole aqui um texto de exemplo no estilo que voce quer que a transcricao siga.\n"
    "O Whisper usa esse prompt como referencia para pontuacao e formatacao.\n\n"
    "Deixe vazio para usar o prompt padrao do Scribe4me."
)


# ---------------------------------------------------------------------------
# HotkeyCaptureButton — botao que captura combinacao de teclas via pynput
# ---------------------------------------------------------------------------

class _HotkeyCaptureButton(tk.Button):
    """Botao que, ao ser clicado, captura a proxima combinacao de teclas."""

    def __init__(self, master, hotkey_str: str, **kwargs):
        self._hotkey_str = hotkey_str
        super().__init__(
            master,
            text=hotkey_display(hotkey_str),
            width=22,
            font=(_FONT, 10, "bold"),
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
        if self._capturing:
            return
        self._capturing = True
        self._pressed_mods = set()
        self.config(text="Pressione o atalho...", relief="sunken")
        self._listener = kb.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def _on_press(self, key) -> None:
        if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
            self._pressed_mods.add("ctrl")
        elif key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
            self._pressed_mods.add("alt")
        elif key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
            self._pressed_mods.add("shift")
        else:
            char = None
            if hasattr(key, "char") and key.char is not None:
                char = key.char.lower()
            elif hasattr(key, "vk") and key.vk is not None:
                vk = key.vk
                if 65 <= vk <= 90:
                    char = chr(vk).lower()
                elif 48 <= vk <= 57:
                    char = chr(vk)
            if char and self._pressed_mods:
                parts = [f"<{m}>" for m in ("ctrl", "alt", "shift") if m in self._pressed_mods]
                parts.append(char)
                self._hotkey_str = "+".join(parts)
                self._finish_capture()

    def _on_release(self, key) -> None:
        if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
            self._pressed_mods.discard("ctrl")
        elif key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
            self._pressed_mods.discard("alt")
        elif key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
            self._pressed_mods.discard("shift")
        if not self._pressed_mods and self._capturing:
            self._cancel_capture()

    def _finish_capture(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._capturing = False
        self.after(0, lambda: self.config(text=hotkey_display(self._hotkey_str), relief="raised"))

    _cancel_capture = _finish_capture

    def destroy(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener.join(timeout=1)
        super().destroy()


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def open_settings_window(
    on_save_hotkeys: Callable[[dict[str, str]], None] | None = None,
    on_save_prompt: Callable[[str], None] | None = None,
    on_save_api: Callable[[str, bool], None] | None = None,
    on_change_model: Callable[[str], None] | None = None,
    on_change_output_mode: Callable[[str], None] | None = None,
    current_model: str = "large",
    recommended_model: str = "large",
) -> None:
    """Abre a janela de configuracoes em thread separada."""
    threading.Thread(
        target=lambda: _show_settings(
            on_save_hotkeys, on_save_prompt, on_save_api,
            on_change_model, on_change_output_mode,
            current_model, recommended_model,
        ),
        daemon=True,
    ).start()


# ---------------------------------------------------------------------------
# Implementacao interna
# ---------------------------------------------------------------------------

def _show_settings(
    on_save_hotkeys, on_save_prompt, on_save_api,
    on_change_model, on_change_output_mode,
    current_model, recommended_model,
) -> None:
    root = tk.Tk()
    root.title(f"{APP_NAME} — Configuracoes")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=(8, 0))

    # ------------------------------------------------------------------
    # Aba: Geral
    # ------------------------------------------------------------------
    tab_geral = ttk.Frame(notebook, padding=14)
    notebook.add(tab_geral, text="  Geral  ")

    # Output mode
    tk.Label(tab_geral, text="Modo de saida:", font=(_FONT, 10, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )
    output_var = tk.StringVar(value=load_output_mode())
    tk.Radiobutton(
        tab_geral, text="Colar no cursor (simula digitacao)",
        variable=output_var, value="cursor", font=(_FONT, 10),
    ).grid(row=1, column=0, sticky="w", padx=(16, 0))
    tk.Radiobutton(
        tab_geral, text="So clipboard (Ctrl+V manual)",
        variable=output_var, value="clipboard", font=(_FONT, 10),
    ).grid(row=2, column=0, sticky="w", padx=(16, 0))

    ttk.Separator(tab_geral, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=12)

    tk.Label(tab_geral, text="Modelo Whisper (backend local):", font=(_FONT, 10, "bold")).grid(
        row=4, column=0, sticky="w", pady=(0, 4)
    )

    model_var = tk.StringVar(value=current_model)
    model_frame = tk.Frame(tab_geral)
    model_frame.grid(row=5, column=0, sticky="w")
    for name in WHISPER_MODELS:
        lbl = model_label(name, recommended_model)
        tk.Radiobutton(
            model_frame, text=lbl, variable=model_var, value=name, font=(_FONT, 9),
        ).pack(anchor="w", padx=(16, 0))

    # ------------------------------------------------------------------
    # Aba: Atalhos
    # ------------------------------------------------------------------
    tab_atalhos = ttk.Frame(notebook, padding=14)
    notebook.add(tab_atalhos, text="  Atalhos  ")

    tk.Label(
        tab_atalhos,
        text="Clique no botao e pressione a nova combinacao de teclas:",
        font=(_FONT, 10),
    ).pack(anchor="w", pady=(0, 8))

    hotkeys = load_hotkeys()
    hk_buttons: dict[str, _HotkeyCaptureButton] = {}
    for action in _ACTION_ORDER:
        row = tk.Frame(tab_atalhos)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=_ACTION_LABELS[action], width=24, anchor="w", font=(_FONT, 10)).pack(side="left")
        btn = _HotkeyCaptureButton(row, hotkeys[action])
        btn.pack(side="right")
        hk_buttons[action] = btn

    tk.Label(
        tab_atalhos,
        text="Use pelo menos 1 modificador (Ctrl, Alt, Shift) + 1 tecla.",
        fg="gray", font=(_FONT, 8),
    ).pack(anchor="w", pady=(8, 0))

    def _reset_hotkeys():
        for action in _ACTION_ORDER:
            hk_buttons[action]._hotkey_str = DEFAULT_HOTKEYS[action]
            hk_buttons[action].config(text=hotkey_display(DEFAULT_HOTKEYS[action]))

    tk.Button(tab_atalhos, text="Restaurar padrao", command=_reset_hotkeys, width=16).pack(
        anchor="w", pady=(8, 0)
    )

    # ------------------------------------------------------------------
    # Aba: Prompt
    # ------------------------------------------------------------------
    tab_prompt = ttk.Frame(notebook, padding=14)
    notebook.add(tab_prompt, text="  Prompt  ")

    tk.Label(
        tab_prompt,
        text="Prompt personalizado (texto de referencia para o Whisper):",
        anchor="w", font=(_FONT, 10),
    ).pack(fill="x", pady=(0, 4))

    text_area = scrolledtext.ScrolledText(tab_prompt, wrap="word", font=(_FONT, 10), height=10, width=56)
    text_area.pack(fill="both", expand=True)

    current_prompt = load_custom_prompt()
    if current_prompt:
        text_area.insert("1.0", current_prompt)
    else:
        text_area.insert("1.0", _DEFAULT_PROMPT_HINT)
        text_area.config(fg="gray")

        def _on_focus(_event):
            if text_area.get("1.0", "end-1c") == _DEFAULT_PROMPT_HINT:
                text_area.delete("1.0", "end")
                text_area.config(fg="black")

        text_area.bind("<FocusIn>", _on_focus)

    def _clear_prompt():
        text_area.delete("1.0", "end")
        text_area.config(fg="black")

    tk.Button(tab_prompt, text="Limpar prompt", command=_clear_prompt, width=14).pack(
        anchor="w", pady=(6, 0)
    )

    # ------------------------------------------------------------------
    # Aba: API
    # ------------------------------------------------------------------
    tab_api = ttk.Frame(notebook, padding=14)
    notebook.add(tab_api, text="  API  ")

    api_cfg = load_api_config()
    api_keys = load_api_keys()

    tk.Label(tab_api, text="Backend:", font=(_FONT, 10, "bold")).grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )
    backend_var = tk.StringVar(value=api_cfg["backend"])
    backend_combo = ttk.Combobox(
        tab_api, textvariable=backend_var,
        values=SUPPORTED_API_BACKENDS, state="readonly", width=14,
    )
    backend_combo.grid(row=0, column=1, sticky="w")
    backend_desc = tk.Label(
        tab_api, text=_BACKEND_LABELS.get(api_cfg["backend"], ""),
        fg="#555", font=(_FONT, 9),
    )
    backend_desc.grid(row=0, column=2, sticky="w", padx=(10, 0))

    frame_keys = tk.LabelFrame(tab_api, text="API Keys", padx=12, pady=8)
    frame_keys.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    key_vars: dict[str, tk.StringVar] = {}
    for i, backend in enumerate(SUPPORTED_API_BACKENDS):
        if backend == "local":
            continue
        label_text = _BACKEND_LABELS[backend].split("(")[0].strip()
        tk.Label(frame_keys, text=f"{label_text}:", width=22, anchor="w").grid(
            row=i, column=0, sticky="w"
        )
        var = tk.StringVar(value=api_keys.get(backend, ""))
        key_vars[backend] = var
        entry = tk.Entry(frame_keys, textvariable=var, width=36, show="*", font=("Consolas", 9))
        entry.grid(row=i, column=1, sticky="ew", padx=(6, 0))
        show_var = tk.BooleanVar(value=False)

        def _make_toggle(e=entry, v=show_var):
            def _toggle():
                e.config(show="" if not v.get() else "*")
                v.set(not v.get())
            return _toggle

        tk.Button(frame_keys, text="👁", command=_make_toggle(), width=3, relief="flat").grid(
            row=i, column=2, padx=(4, 0)
        )
    frame_keys.columnconfigure(1, weight=1)

    realtime_var = tk.BooleanVar(value=api_cfg["realtime"])
    frame_rt = tk.Frame(tab_api)
    frame_rt.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
    realtime_check = tk.Checkbutton(
        frame_rt,
        text="Ativar transcricao em tempo real (Deepgram — exibe texto parcial enquanto fala)",
        variable=realtime_var, font=(_FONT, 9),
    )
    if api_cfg["backend"] == "deepgram":
        realtime_check.pack(anchor="w")

    def _on_backend_change(*_):
        b = backend_var.get()
        backend_desc.config(text=_BACKEND_LABELS.get(b, ""))
        if b == "deepgram":
            realtime_check.pack(anchor="w")
        else:
            realtime_check.pack_forget()

    backend_var.trace_add("write", _on_backend_change)

    tk.Label(
        tab_api,
        text=(
            "Groq: 7.200s/dia gratis  |  OpenAI: $0.006/min  "
            "|  Gemini: free tier  |  Deepgram: 200h/mes gratis"
        ),
        fg="#777", font=(_FONT, 8), wraplength=430,
    ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

    # ------------------------------------------------------------------
    # Botoes globais
    # ------------------------------------------------------------------
    frame_btn = tk.Frame(root, padx=8, pady=8)
    frame_btn.pack(fill="x")

    def _save_all():
        # Validacao API antes de qualquer save
        new_backend = backend_var.get()
        new_keys = {b: v.get().strip() for b, v in key_vars.items()}
        if new_backend != "local" and not new_keys.get(new_backend, ""):
            messagebox.showwarning(
                "API Key obrigatoria",
                f"Informe a API key para o backend '{new_backend}'.",
                parent=root,
            )
            notebook.select(tab_api)
            return

        # Atalhos
        new_hotkeys = {action: hk_buttons[action].hotkey_str for action in _ACTION_ORDER}
        save_hotkeys(new_hotkeys)
        if on_save_hotkeys:
            on_save_hotkeys(new_hotkeys)

        # Prompt
        content = text_area.get("1.0", "end-1c").strip()
        if content == _DEFAULT_PROMPT_HINT:
            content = ""
        save_custom_prompt(content)
        if on_save_prompt:
            on_save_prompt(content)

        # Modo de saida
        new_output = output_var.get()
        save_output_mode(new_output)
        if on_change_output_mode:
            on_change_output_mode(new_output)

        # Modelo (so dispara callback se mudou)
        new_model = model_var.get()
        if new_model != current_model and on_change_model:
            on_change_model(new_model)

        # API
        new_realtime = realtime_var.get() and new_backend == "deepgram"
        save_api_keys(new_keys)
        save_api_config({"backend": new_backend, "realtime": new_realtime})
        if on_save_api:
            on_save_api(new_backend, new_realtime)

        root.destroy()

    tk.Button(frame_btn, text="Salvar", command=_save_all, width=12).pack(side="right")
    tk.Button(frame_btn, text="Cancelar", command=root.destroy, width=10).pack(
        side="right", padx=(0, 8)
    )

    # Centraliza na tela
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = root.winfo_width()
    h = root.winfo_height()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.mainloop()
