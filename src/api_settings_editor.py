"""Janela de configuracao dos backends de transcricao via API."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from src.config import (
    SUPPORTED_API_BACKENDS,
    load_api_keys,
    load_api_config,
    save_api_keys,
    save_api_config,
)

_BACKEND_LABELS = {
    "local":    "Local (Whisper — sem API)",
    "openai":   "OpenAI (whisper-1)",
    "groq":     "Groq (whisper-large-v3 — gratis)",
    "gemini":   "Gemini Flash (Google)",
    "deepgram": "Deepgram Nova-2 (realtime disponivel)",
}

_KEY_PLACEHOLDERS = {
    "openai":   "sk-...",
    "groq":     "gsk_...",
    "gemini":   "AIza...",
    "deepgram": "Token ...",
}


def open_api_settings_editor(
    on_save: Callable[[str, bool], None] | None = None,
) -> None:
    """Abre a janela de configuracao de API em thread separada."""
    import threading
    threading.Thread(target=lambda: _show_editor(on_save), daemon=True).start()


def _show_editor(
    on_save: Callable[[str, bool], None] | None = None,
) -> None:
    api_keys = load_api_keys()
    api_cfg = load_api_config()

    root = tk.Tk()
    root.title("Scribe4me — Configurar API de Transcricao")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    # ---------------------------------------------------------------
    # Backend selector
    # ---------------------------------------------------------------
    frame_top = tk.Frame(root, padx=16, pady=12)
    frame_top.pack(fill="x")

    tk.Label(frame_top, text="Backend:", font=("Segoe UI", 10, "bold")).grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )

    backend_var = tk.StringVar(value=api_cfg["backend"])
    backend_combo = ttk.Combobox(
        frame_top,
        textvariable=backend_var,
        values=SUPPORTED_API_BACKENDS,
        state="readonly",
        width=14,
    )
    backend_combo.grid(row=0, column=1, sticky="w")

    backend_label = tk.Label(
        frame_top,
        text=_BACKEND_LABELS.get(api_cfg["backend"], ""),
        fg="#555",
        font=("Segoe UI", 9),
    )
    backend_label.grid(row=0, column=2, sticky="w", padx=(10, 0))

    # ---------------------------------------------------------------
    # API keys — uma por provider (exceto local)
    # ---------------------------------------------------------------
    frame_keys = tk.LabelFrame(root, text="API Keys", padx=12, pady=8)
    frame_keys.pack(fill="x", padx=16, pady=(0, 8))

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
        entry = tk.Entry(
            frame_keys,
            textvariable=var,
            width=44,
            show="*",
            font=("Consolas", 9),
        )
        entry.grid(row=i, column=1, sticky="ew", padx=(6, 0))

        # Botao para mostrar/ocultar key
        show_var = tk.BooleanVar(value=False)

        def _toggle_show(e=entry, v=show_var):
            e.config(show="" if not v.get() else "*")
            v.set(not v.get())

        tk.Button(
            frame_keys, text="👁", command=_toggle_show, width=3, relief="flat"
        ).grid(row=i, column=2, padx=(4, 0))

    frame_keys.columnconfigure(1, weight=1)

    # ---------------------------------------------------------------
    # Realtime toggle (so Deepgram) — frame sempre no layout, checkbox
    # aparece/desaparece dentro dele para nao quebrar a ordem do pack
    # ---------------------------------------------------------------
    realtime_var = tk.BooleanVar(value=api_cfg["realtime"])
    frame_realtime = tk.Frame(root, padx=16)
    frame_realtime.pack(fill="x")  # sempre no layout (vazio nao ocupa espaco visual)

    realtime_check = tk.Checkbutton(
        frame_realtime,
        text="Ativar transcricao em tempo real (Deepgram — exibe texto parcial enquanto fala)",
        variable=realtime_var,
        font=("Segoe UI", 9),
    )

    if api_cfg["backend"] == "deepgram":
        realtime_check.pack(anchor="w", pady=(0, 4))

    def _on_backend_change(*_):
        b = backend_var.get()
        backend_label.config(text=_BACKEND_LABELS.get(b, ""))
        if b == "deepgram":
            realtime_check.pack(anchor="w", pady=(0, 4))
        else:
            realtime_check.pack_forget()

    backend_var.trace_add("write", _on_backend_change)

    # ---------------------------------------------------------------
    # Info sobre gratuidade
    # ---------------------------------------------------------------
    info_text = (
        "Groq: 7.200s/dia gratis  |  OpenAI: $0.006/min  "
        "|  Gemini: free tier  |  Deepgram: 200h/mes gratis"
    )
    tk.Label(
        root, text=info_text, fg="#777", font=("Segoe UI", 8), wraplength=480
    ).pack(padx=16, pady=(0, 6))

    # ---------------------------------------------------------------
    # Botoes
    # ---------------------------------------------------------------
    frame_btn = tk.Frame(root, padx=16, pady=10)
    frame_btn.pack(fill="x")

    def _save():
        new_backend = backend_var.get()
        new_keys = {b: v.get().strip() for b, v in key_vars.items()}
        new_realtime = realtime_var.get() and new_backend == "deepgram"

        # Valida: se backend != local, key nao pode estar vazia
        if new_backend != "local" and not new_keys.get(new_backend, ""):
            messagebox.showwarning(
                "API Key obrigatoria",
                f"Informe a API key para o backend '{new_backend}'.",
                parent=root,
            )
            return

        save_api_keys(new_keys)
        save_api_config({"backend": new_backend, "realtime": new_realtime})

        if on_save:
            on_save(new_backend, new_realtime)

        root.destroy()

    tk.Button(frame_btn, text="Salvar", command=_save, width=12).pack(side="right")
    tk.Button(frame_btn, text="Cancelar", command=root.destroy, width=10).pack(
        side="right", padx=(0, 8)
    )

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = root.winfo_width()
    h = root.winfo_height()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.mainloop()
