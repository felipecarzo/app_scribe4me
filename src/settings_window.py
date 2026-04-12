"""Janela de configuracoes unificada do Scribe4me.

Abas: Geral (modelo + modo de saida), Atalhos, Prompt, API.
Usando CustomTkinter para uma UI Premium Dark Mode.
"""

import sys
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk
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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

_FONT = "Segoe UI" if sys.platform == "win32" else "Roboto"

_BACKEND_LABELS = {
    "local":    "Local (Whisper — sem API)",
    "openai":   "OpenAI (whisper-1)",
    "groq":     "Groq (whisper-large-v3)",
    "gemini":   "Gemini Flash (Google)",
    "deepgram": "Deepgram Nova-2",
}

_ACTION_LABELS = {
    "push_to_talk": "Gravar (segura e fala)",
    "toggle":       "Toggle (iniciar/parar)",
    "cancel":       "Cancelar gravacao",
    "quit":         "Sair",
}
_ACTION_ORDER = ["push_to_talk", "toggle", "cancel", "quit"]

_DEFAULT_PROMPT_HINT = (
    "Cole aqui um texto de exemplo no estilo que você quer que a transcrição siga.\n"
    "O Whisper usa esse prompt como referência para pontuação e formatação.\n\n"
    "Deixe vazio para usar o prompt padrão do Scribe4me."
)


# ---------------------------------------------------------------------------
# HotkeyCaptureButton
# ---------------------------------------------------------------------------

class _HotkeyCaptureButton(ctk.CTkButton):
    """Botão que, ao ser clicado, captura a proxima combinação de teclas."""

    def __init__(self, master, hotkey_str: str, **kwargs):
        self._hotkey_str = hotkey_str
        super().__init__(
            master,
            text=hotkey_display(hotkey_str),
            width=200,
            font=(_FONT, 12, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            **kwargs,
        )
        self._listener: kb.Listener | None = None
        self._pressed_mods: set[str] = set()
        self._capturing = False
        self.configure(command=self._start_capture)

    @property
    def hotkey_str(self) -> str:
        return self._hotkey_str

    def _start_capture(self) -> None:
        if self._capturing:
            return
        self._capturing = True
        self._pressed_mods = set()
        self.configure(text="Pressione o atalho...", fg_color="#F59E0B", hover_color="#D97706")
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
            self._finish_capture()  # ou cancel, apenas finaliza se não apertar modificador válido

    def _finish_capture(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._capturing = False
        def _reset_btn():
            self.configure(text=hotkey_display(self._hotkey_str), fg_color="#3B82F6", hover_color="#2563EB")
        self.after(0, _reset_btn)

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
    root = ctk.CTk()
    root.title(APP_NAME)
    root.minsize(580, 520)
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))

    label_title = ctk.CTkLabel(root, text="Configurações", font=(_FONT, 20, "bold"), text_color="#E2E8F0")
    label_title.pack(pady=(16, 4))

    notebook = ctk.CTkTabview(root, width=540, height=380, fg_color="#1E293B", segmented_button_selected_color="#3B82F6")
    notebook.pack(fill="both", expand=True, padx=16, pady=(8, 16))

    tab_geral = notebook.add("Geral")
    tab_atalhos = notebook.add("Atalhos")
    tab_prompt = notebook.add("Prompt")
    tab_api = notebook.add("API")

    # ------------------------------------------------------------------
    # Aba: Geral
    # ------------------------------------------------------------------
    ctk.CTkLabel(tab_geral, text="Modo de saída:", font=(_FONT, 14, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=16, pady=(16, 8))
    
    output_var = ctk.StringVar(value=load_output_mode())
    ctk.CTkRadioButton(
        tab_geral, text="Colar no cursor (simula digitação)", 
        variable=output_var, value="cursor", font=(_FONT, 13)
    ).pack(anchor="w", padx=32, pady=4)
    ctk.CTkRadioButton(
        tab_geral, text="Só clipboard (Ctrl+V manual)", 
        variable=output_var, value="clipboard", font=(_FONT, 13)
    ).pack(anchor="w", padx=32, pady=4)

    # divisor
    ctk.CTkFrame(tab_geral, height=2, fg_color="#334155").pack(fill="x", padx=16, pady=20)

    ctk.CTkLabel(tab_geral, text="Modelo Whisper (backend local):", font=(_FONT, 14, "bold"), text_color="#F8FAFC").pack(anchor="w", padx=16, pady=(0, 8))

    model_var = ctk.StringVar(value=current_model)
    model_frame = ctk.CTkFrame(tab_geral, fg_color="transparent")
    model_frame.pack(fill="x", padx=32)
    
    # Organize in rows (2 columns max)
    row_frames = []
    for i in range(0, len(WHISPER_MODELS), 2):
        row = ctk.CTkFrame(model_frame, fg_color="transparent")
        row.pack(fill="x", pady=4)
        row_frames.append(row)

    for idx, name in enumerate(WHISPER_MODELS):
        lbl = model_label(name, recommended_model)
        r_frame = row_frames[idx // 2]
        rb = ctk.CTkRadioButton(r_frame, text=lbl, variable=model_var, value=name, font=(_FONT, 12))
        rb.pack(side="left", padx=(0, 16), fill="x", expand=True)

    # ------------------------------------------------------------------
    # Aba: Atalhos
    # ------------------------------------------------------------------
    ctk.CTkLabel(
        tab_atalhos,
        text="Clique no botão e pressione a nova combinação de teclas:",
        font=(_FONT, 13), text_color="#CBD5E1"
    ).pack(anchor="w", padx=16, pady=(16, 12))

    hotkeys = load_hotkeys()
    hk_buttons: dict[str, _HotkeyCaptureButton] = {}
    for action in _ACTION_ORDER:
        row = ctk.CTkFrame(tab_atalhos, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=_ACTION_LABELS[action], width=180, anchor="w", font=(_FONT, 13, "bold"), text_color="#F8FAFC").pack(side="left")
        btn = _HotkeyCaptureButton(row, hotkeys[action])
        btn.pack(side="right")
        hk_buttons[action] = btn

    ctk.CTkLabel(
        tab_atalhos,
        text="Use pelo menos 1 modificador (Ctrl, Alt, Shift) + 1 tecla.",
        text_color="#94A3B8", font=(_FONT, 11)
    ).pack(anchor="w", padx=16, pady=(12, 0))

    def _reset_hotkeys():
        for action in _ACTION_ORDER:
            hk_buttons[action]._hotkey_str = DEFAULT_HOTKEYS[action]
            hk_buttons[action].configure(text=hotkey_display(DEFAULT_HOTKEYS[action]))

    ctk.CTkButton(tab_atalhos, text="Restaurar padrão", command=_reset_hotkeys, width=140, fg_color="#475569", hover_color="#334155").pack(
        anchor="w", padx=16, pady=(16, 0)
    )

    # ------------------------------------------------------------------
    # Aba: Prompt
    # ------------------------------------------------------------------
    ctk.CTkLabel(
        tab_prompt,
        text="Prompt personalizado (referência para o Whisper):",
        anchor="w", font=(_FONT, 13, "bold"), text_color="#F8FAFC"
    ).pack(fill="x", padx=16, pady=(16, 8))

    text_area = ctk.CTkTextbox(tab_prompt, font=(_FONT, 13), height=180, fg_color="#0F172A", border_color="#334155", border_width=1)
    text_area.pack(fill="both", expand=True, padx=16)

    current_prompt = load_custom_prompt()
    if current_prompt:
        text_area.insert("0.0", current_prompt)
    else:
        text_area.insert("0.0", _DEFAULT_PROMPT_HINT)
        text_area.configure(text_color="#64748B")

    def _on_focus(_event):
        content = text_area.get("0.0", "end").strip()
        if content == _DEFAULT_PROMPT_HINT.strip():
            text_area.delete("0.0", "end")
            text_area.configure(text_color="#F8FAFC")

    text_area.bind("<FocusIn>", _on_focus)

    def _clear_prompt():
        text_area.delete("0.0", "end")
        text_area.configure(text_color="#F8FAFC")

    ctk.CTkButton(tab_prompt, text="Limpar prompt", command=_clear_prompt, width=140, fg_color="#475569", hover_color="#334155").pack(
        anchor="w", padx=16, pady=(12, 16)
    )

    # ------------------------------------------------------------------
    # Aba: API
    # ------------------------------------------------------------------
    api_cfg = load_api_config()
    api_keys = load_api_keys()

    top_api_row = ctk.CTkFrame(tab_api, fg_color="transparent")
    top_api_row.pack(fill="x", padx=16, pady=(16, 12))

    ctk.CTkLabel(top_api_row, text="Backend:", font=(_FONT, 14, "bold"), text_color="#F8FAFC").pack(side="left")
    
    backend_var = ctk.StringVar(value=api_cfg["backend"])
    backend_desc_var = ctk.StringVar(value=_BACKEND_LABELS.get(api_cfg["backend"], ""))
    
    backend_combo = ctk.CTkComboBox(
        top_api_row, variable=backend_var,
        values=SUPPORTED_API_BACKENDS, width=140, state="readonly"
    )
    backend_combo.pack(side="left", padx=16)
    
    ctk.CTkLabel(top_api_row, textvariable=backend_desc_var, text_color="#94A3B8", font=(_FONT, 12)).pack(side="left")

    frame_keys = ctk.CTkFrame(tab_api, fg_color="#0F172A", border_width=1, border_color="#334155")
    frame_keys.pack(fill="x", padx=16, pady=8)
    
    ctk.CTkLabel(frame_keys, text="API Keys (Chaves de Acesso)", font=(_FONT, 13, "bold")).pack(anchor="w", padx=12, pady=(8, 0))

    key_vars: dict[str, ctk.StringVar] = {}
    for backend in SUPPORTED_API_BACKENDS:
        if backend == "local":
            continue
            
        row_k = ctk.CTkFrame(frame_keys, fg_color="transparent")
        row_k.pack(fill="x", padx=12, pady=4)
        
        label_text = _BACKEND_LABELS[backend].split("(")[0].strip()
        ctk.CTkLabel(row_k, text=f"{label_text}:", width=100, anchor="w", font=(_FONT, 12)).pack(side="left")
        
        var = ctk.StringVar(value=api_keys.get(backend, ""))
        key_vars[backend] = var
        entry = ctk.CTkEntry(row_k, textvariable=var, show="*", font=("Consolas", 12), height=28)
        entry.pack(side="left", fill="x", expand=True, padx=8)

        show_var = tk.BooleanVar(value=False)
        def _make_toggle(e=entry, v=show_var):
            def _toggle():
                e.configure(show="" if not v.get() else "*")
                v.set(not v.get())
            return _toggle

        ctk.CTkButton(row_k, text="Ocultar/Exibir", command=_make_toggle(), width=100, height=28, fg_color="#475569", hover_color="#334155", font=(_FONT, 11)).pack(side="right")

    frame_rt_container = ctk.CTkFrame(tab_api, fg_color="transparent")
    frame_rt_container.pack(fill="x", padx=16, pady=8)

    realtime_var = ctk.BooleanVar(value=api_cfg["realtime"])
    realtime_check = ctk.CTkCheckBox(
        frame_rt_container,
        text="Tempo real (Deepgram — texto parcial ao falar)",
        variable=realtime_var, font=(_FONT, 12), onvalue=True, offvalue=False
    )
    if api_cfg["backend"] == "deepgram":
        realtime_check.pack(anchor="w")

    def _on_backend_change(*_):
        b = backend_var.get()
        backend_desc_var.set(_BACKEND_LABELS.get(b, ""))
        if b == "deepgram":
            realtime_check.pack(anchor="w")
        else:
            realtime_check.pack_forget()

    backend_var.trace_add("write", _on_backend_change)

    ctk.CTkLabel(
        tab_api,
        text=(
            "Custos aprox: Groq (Gratis) | OpenAI ($0.006/min) | Gemini (Free Tier) | Deepgram (200h/mês grátis)"
        ),
        text_color="#64748B", font=(_FONT, 11)
    ).pack(anchor="w", padx=16, pady=(4, 8))

    # ------------------------------------------------------------------
    # Botoes globais
    # ------------------------------------------------------------------
    frame_btn = ctk.CTkFrame(root, fg_color="transparent")
    frame_btn.pack(fill="x", padx=16, pady=8)

    def _save_all():
        new_backend = backend_var.get()
        new_keys = {b: v.get().strip() for b, v in key_vars.items()}
        if new_backend != "local" and not new_keys.get(new_backend, ""):
            messagebox.showwarning(
                "API Key obrigatoria",
                f"Informe a API key para o backend '{new_backend}'.",
                parent=root,
            )
            notebook.set("API")
            return

        new_hotkeys = {action: hk_buttons[action].hotkey_str for action in _ACTION_ORDER}
        save_hotkeys(new_hotkeys)
        if on_save_hotkeys:
            on_save_hotkeys(new_hotkeys)

        content = text_area.get("0.0", "end").strip()
        if content == _DEFAULT_PROMPT_HINT.strip():
            content = ""
        save_custom_prompt(content)
        if on_save_prompt:
            on_save_prompt(content)

        new_output = output_var.get()
        save_output_mode(new_output)
        if on_change_output_mode:
            on_change_output_mode(new_output)

        new_model = model_var.get()
        if new_model != current_model and on_change_model:
            on_change_model(new_model)

        new_realtime = realtime_var.get() and new_backend == "deepgram"
        save_api_keys(new_keys)
        save_api_config({"backend": new_backend, "realtime": new_realtime})
        if on_save_api:
            on_save_api(new_backend, new_realtime)

        root.destroy()

    ctk.CTkButton(frame_btn, text="Salvar", command=_save_all, width=120, fg_color="#10B981", hover_color="#059669", font=(_FONT, 13, "bold")).pack(side="right")
    ctk.CTkButton(frame_btn, text="Cancelar", command=root.destroy, width=120, fg_color="#64748B", hover_color="#475569", font=(_FONT, 13)).pack(side="right", padx=(0, 16))

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = root.winfo_width()
    h = root.winfo_height()
    root.geometry(f"+{int((sw - w) / 2)}+{int((sh - h) / 2)}")

    root.mainloop()
