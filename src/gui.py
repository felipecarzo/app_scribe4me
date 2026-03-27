"""Janela GUI opcional do SpeedOsper (tkinter, thread separada).

A janela e complementar ao tray — o app funciona sem ela.
Double-click no tray abre/fecha a janela.
Fechar a janela apenas esconde (minimiza pro tray).
"""

import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable

from src.config import APP_NAME

logger = logging.getLogger("speedosper.gui")

# --- Dark Theme Colors (VS Code style) ---

DARK_BG = "#1e1e1e"
DARK_SURFACE = "#252526"
DARK_BORDER = "#3c3c3c"
DARK_INPUT = "#2d2d2d"
TEXT_PRIMARY = "#cccccc"
TEXT_SECONDARY = "#808080"
TEXT_LOG = "#d4d4d4"
ACCENT = "#007acc"
RECORD_IDLE = "#4CAF50"
RECORD_ACTIVE = "#f44336"
STATUS_BG = "#007acc"
STATUS_TEXT = "#ffffff"


# --- QueueLogHandler ---

class QueueLogHandler(logging.Handler):
    """Handler que envia log records formatados para uma queue."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self._queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self._queue.put_nowait(msg)
        except queue.Full:
            pass


# --- GUI ---

class SpeedOsperGUI:
    """Janela principal do SpeedOsper (opcional — app funciona sem ela)."""

    def __init__(
        self,
        log_queue: queue.Queue,
        on_record_toggle: Callable | None = None,
        on_profile_change: Callable[[str], None] | None = None,
        on_mode_change: Callable[[str], None] | None = None,
        on_model_change: Callable[[str], None] | None = None,
        profile_names: list[str] | None = None,
        mode_names: list[str] | None = None,
        model_names: list[str] | None = None,
        current_profile: str = "Tech-Dev",
        current_mode: str = "scribe",
        current_model: str = "large-v3",
    ):
        self._log_queue = log_queue
        self._on_record_toggle = on_record_toggle
        self._on_profile_change = on_profile_change
        self._on_mode_change = on_mode_change
        self._on_model_change = on_model_change
        self._profile_names = profile_names or ["Tech-Dev"]
        self._mode_names = mode_names or ["scribe", "translate", "voice"]
        self._model_names = model_names or ["large-v3"]
        self._current_profile = current_profile
        self._current_mode = current_mode
        self._current_model = current_model
        self._current_state = "Idle"

        self._root: tk.Tk | None = None
        self._thread: threading.Thread | None = None
        self._visible = False
        self._ready = threading.Event()

        # Widgets (preenchidos no _build_ui)
        self._log_text: scrolledtext.ScrolledText | None = None
        self._btn_record: tk.Button | None = None
        self._var_profile: tk.StringVar | None = None
        self._var_mode: tk.StringVar | None = None
        self._var_model: tk.StringVar | None = None
        self._lbl_state: tk.Label | None = None
        self._lbl_model: tk.Label | None = None
        self._lbl_profile: tk.Label | None = None
        self._combo_profile: ttk.Combobox | None = None
        self._combo_mode: ttk.Combobox | None = None
        self._combo_model: ttk.Combobox | None = None
        self._is_recording = False
        self._stopped = False

    def start(self) -> None:
        """Inicia a janela em thread separada (inicia escondida)."""
        self._thread = threading.Thread(target=self._run, daemon=True, name="gui-thread")
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self) -> None:
        """Loop principal do tkinter."""
        self._root = tk.Tk()
        self._root.title(APP_NAME)
        self._root.geometry("700x450")
        self._root.minsize(500, 300)
        self._root.configure(bg=DARK_BG)
        self._root.protocol("WM_DELETE_WINDOW", self.hide)
        # Inicia escondida
        self._root.withdraw()

        self._setup_dark_theme()
        self._build_ui()
        self._poll_log_queue()
        self._ready.set()
        self._root.mainloop()

    def _setup_dark_theme(self) -> None:
        """Configura ttk style dark."""
        style = ttk.Style(self._root)
        style.theme_use("clam")

        style.configure(".", background=DARK_BG, foreground=TEXT_PRIMARY,
                         fieldbackground=DARK_INPUT, borderwidth=0)
        style.configure("TFrame", background=DARK_BG)
        style.configure("TLabel", background=DARK_BG, foreground=TEXT_PRIMARY)
        style.configure("TCombobox", fieldbackground=DARK_INPUT, background=DARK_SURFACE,
                         foreground=TEXT_PRIMARY, arrowcolor=TEXT_PRIMARY)
        style.map("TCombobox",
                   fieldbackground=[("readonly", DARK_INPUT)],
                   selectbackground=[("readonly", DARK_INPUT)],
                   selectforeground=[("readonly", TEXT_PRIMARY)])
        style.configure("Status.TLabel", background=STATUS_BG, foreground=STATUS_TEXT,
                         padding=(8, 4))
        style.configure("StatusBar.TFrame", background=STATUS_BG)
        style.configure("Controls.TFrame", background=DARK_SURFACE)
        style.configure("Controls.TLabel", background=DARK_SURFACE, foreground=TEXT_SECONDARY,
                         font=("Segoe UI", 9))

    def _build_ui(self) -> None:
        """Constroi a interface."""
        root = self._root

        # --- Control bar (top) ---
        ctrl_frame = ttk.Frame(root, style="Controls.TFrame", padding=8)
        ctrl_frame.pack(fill=tk.X, side=tk.TOP)

        # Botao gravar
        self._btn_record = tk.Button(
            ctrl_frame, text="GRAVAR", font=("Segoe UI", 11, "bold"),
            bg=RECORD_IDLE, fg="white", activebackground="#388E3C",
            relief=tk.FLAT, padx=16, pady=6, cursor="hand2",
            command=self._on_record_click,
        )
        self._btn_record.pack(side=tk.LEFT, padx=(0, 16))

        # Profile dropdown
        ttk.Label(ctrl_frame, text="Profile:", style="Controls.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self._var_profile = tk.StringVar(value=self._current_profile)
        self._combo_profile = ttk.Combobox(
            ctrl_frame, textvariable=self._var_profile,
            values=self._profile_names, state="readonly", width=14,
        )
        self._combo_profile.pack(side=tk.LEFT, padx=(0, 12))
        self._combo_profile.bind("<<ComboboxSelected>>", self._on_profile_select)

        # Mode dropdown
        ttk.Label(ctrl_frame, text="Modo:", style="Controls.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self._var_mode = tk.StringVar(value=self._current_mode)
        self._combo_mode = ttk.Combobox(
            ctrl_frame, textvariable=self._var_mode,
            values=self._mode_names, state="readonly", width=10,
        )
        self._combo_mode.pack(side=tk.LEFT, padx=(0, 12))
        self._combo_mode.bind("<<ComboboxSelected>>", self._on_mode_select)

        # Model dropdown
        ttk.Label(ctrl_frame, text="Modelo:", style="Controls.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self._var_model = tk.StringVar(value=self._current_model)
        self._combo_model = ttk.Combobox(
            ctrl_frame, textvariable=self._var_model,
            values=self._model_names, state="readonly", width=12,
        )
        self._combo_model.pack(side=tk.LEFT, padx=(0, 0))
        self._combo_model.bind("<<ComboboxSelected>>", self._on_model_select)

        # --- Log panel (center) ---
        log_frame = ttk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 0))

        self._log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=DARK_BG, fg=TEXT_LOG, insertbackground=TEXT_PRIMARY,
            font=("Cascadia Code", 9), relief=tk.FLAT,
            selectbackground=ACCENT, selectforeground="white",
            borderwidth=0, highlightthickness=0,
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # --- Status bar (bottom) ---
        status_frame = ttk.Frame(root, style="StatusBar.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._lbl_state = ttk.Label(status_frame, text=f"Estado: {self._current_state}",
                                     style="Status.TLabel", width=20, anchor=tk.W)
        self._lbl_state.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._lbl_model = ttk.Label(status_frame, text=f"Modelo: {self._current_model}",
                                     style="Status.TLabel", width=20, anchor=tk.CENTER)
        self._lbl_model.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._lbl_profile = ttk.Label(status_frame, text=f"Profile: {self._current_profile}",
                                       style="Status.TLabel", width=20, anchor=tk.E)
        self._lbl_profile.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # --- Log queue polling ---

    def _poll_log_queue(self) -> None:
        """Le mensagens da queue e insere no log panel."""
        if self._stopped:
            return
        batch = []
        try:
            while len(batch) < 50:
                msg = self._log_queue.get_nowait()
                batch.append(msg)
        except queue.Empty:
            pass

        if batch and self._log_text is not None:
            self._log_text.configure(state=tk.NORMAL)
            for msg in batch:
                self._log_text.insert(tk.END, msg + "\n")
            # Limita a 2000 linhas
            line_count = int(self._log_text.index("end-1c").split(".")[0])
            if line_count > 2000:
                self._log_text.delete("1.0", f"{line_count - 2000}.0")
            self._log_text.see(tk.END)
            self._log_text.configure(state=tk.DISABLED)

        if self._root is not None:
            self._root.after(100, self._poll_log_queue)

    # --- Control callbacks ---

    def _on_record_click(self) -> None:
        if self._on_record_toggle:
            self._on_record_toggle()

    def _on_profile_select(self, event) -> None:
        name = self._var_profile.get()
        if name and self._on_profile_change:
            self._on_profile_change(name)

    def _on_mode_select(self, event) -> None:
        mode = self._var_mode.get()
        if mode and self._on_mode_change:
            self._on_mode_change(mode)

    def _on_model_select(self, event) -> None:
        model = self._var_model.get()
        if model and self._on_model_change:
            self._on_model_change(model)

    # --- External state updates (chamados pelo main via root.after) ---

    def update_state(self, state: str) -> None:
        """Atualiza o estado exibido (chamado pelo SpeedOsper)."""
        self._current_state = state
        if self._root is None:
            return
        self._root.after(0, self._do_update_state, state)

    def _do_update_state(self, state: str) -> None:
        if self._lbl_state:
            self._lbl_state.configure(text=f"Estado: {state}")
        # Atualiza botao gravar
        is_rec = state in ("Gravando", "Recording")
        self._is_recording = is_rec
        if self._btn_record:
            if is_rec:
                self._btn_record.configure(text="PARAR", bg=RECORD_ACTIVE,
                                            activebackground="#D32F2F")
            else:
                self._btn_record.configure(text="GRAVAR", bg=RECORD_IDLE,
                                            activebackground="#388E3C")

    def update_profile(self, name: str) -> None:
        """Atualiza profile exibido."""
        self._current_profile = name
        if self._root is None:
            return
        self._root.after(0, self._do_update_profile, name)

    def _do_update_profile(self, name: str) -> None:
        if self._var_profile:
            self._var_profile.set(name)
        if self._lbl_profile:
            self._lbl_profile.configure(text=f"Profile: {name}")

    def update_mode(self, mode: str) -> None:
        """Atualiza modo exibido."""
        self._current_mode = mode
        if self._root is None:
            return
        self._root.after(0, self._do_update_mode, mode)

    def _do_update_mode(self, mode: str) -> None:
        if self._var_mode:
            self._var_mode.set(mode)

    def update_model(self, model: str) -> None:
        """Atualiza modelo exibido."""
        self._current_model = model
        if self._root is None:
            return
        self._root.after(0, self._do_update_model, model)

    def _do_update_model(self, model: str) -> None:
        if self._var_model:
            self._var_model.set(model)
        if self._lbl_model:
            self._lbl_model.configure(text=f"Modelo: {model}")

    def update_profile_list(self, names: list[str]) -> None:
        """Atualiza lista de profiles nos dropdowns."""
        self._profile_names = names
        if self._root is None:
            return
        self._root.after(0, self._do_update_profile_list, names)

    def _do_update_profile_list(self, names: list[str]) -> None:
        if self._combo_profile:
            self._combo_profile["values"] = names

    # --- Show / Hide / Toggle ---

    def show(self) -> None:
        """Mostra a janela."""
        if self._root is None:
            return
        self._visible = True
        self._root.after(0, self._do_show)

    def _do_show(self) -> None:
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()

    def hide(self) -> None:
        """Esconde a janela (minimiza pro tray)."""
        if self._root is None:
            return
        self._visible = False
        self._root.after(0, self._do_hide)

    def _do_hide(self) -> None:
        self._root.withdraw()

    def toggle(self) -> None:
        """Alterna visibilidade."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def is_visible(self) -> bool:
        return self._visible

    def stop(self) -> None:
        """Encerra a janela."""
        self._stopped = True
        if self._root is not None:
            self._root.after(0, self._root.destroy)
