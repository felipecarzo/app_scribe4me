"""Overlay flutuante para exibir transcricao em tempo real."""

import logging
import queue
import threading
import tkinter as tk

logger = logging.getLogger("scribe4me")

# Configuracoes visuais do overlay
_BG_COLOR = "#1e1e1e"
_TEXT_COLOR = "#ffffff"
_FONT = ("Segoe UI", 12)
_MAX_WIDTH_PX = 700
_PADDING = 12
_ALPHA = 0.88  # transparencia (0.0 = invisivel, 1.0 = solido)


class RealtimeOverlay:
    """Janela flutuante topmost que exibe texto parcial durante gravacao realtime.

    - Aparece centralizada na parte inferior da tela ao chamar show()
    - Atualiza o texto com update(text)
    - Some ao chamar hide()
    """

    def __init__(self):
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False

    def show(self) -> None:
        """Exibe o overlay. Seguro para chamar de qualquer thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, text: str) -> None:
        """Atualiza o texto exibido. Seguro para chamar de qualquer thread."""
        self._queue.put(("update", text))

    def hide(self) -> None:
        """Fecha o overlay. Seguro para chamar de qualquer thread."""
        self._queue.put(("hide", None))

    # ------------------------------------------------------------------
    # Loop interno (roda na thread propria do overlay)
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            self._root = tk.Tk()
            self._root.withdraw()  # esconde enquanto configura
            self._setup_window()
            self._root.after(50, self._process_queue)
            self._root.mainloop()
        except Exception as e:
            logger.warning("RealtimeOverlay erro: %s", e)
        finally:
            self._running = False
            self._root = None
            self._label = None

    def _setup_window(self) -> None:
        root = self._root
        root.overrideredirect(True)  # sem borda/titlebar
        root.attributes("-topmost", True)
        root.attributes("-alpha", _ALPHA)
        root.configure(bg=_BG_COLOR)

        # Label com texto — wraplength para nao ultrapassar largura maxima
        self._label = tk.Label(
            root,
            text="...",
            font=_FONT,
            fg=_TEXT_COLOR,
            bg=_BG_COLOR,
            wraplength=_MAX_WIDTH_PX - 2 * _PADDING,
            justify="left",
            padx=_PADDING,
            pady=_PADDING,
        )
        self._label.pack()

        # Posiciona na parte inferior central da tela
        root.update_idletasks()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        win_w = min(_MAX_WIDTH_PX, screen_w - 40)
        win_h = self._label.winfo_reqheight() + 2 * _PADDING
        x = (screen_w - win_w) // 2
        y = screen_h - win_h - 80  # 80px acima da barra de tarefas
        root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        root.deiconify()

    def _process_queue(self) -> None:
        """Drena a fila de comandos e reagenda."""
        try:
            while True:
                cmd, payload = self._queue.get_nowait()
                if cmd == "update" and self._label is not None:
                    self._label.config(text=payload or "...")
                    # Reajusta posicao se o texto cresceu
                    self._reposition()
                elif cmd == "hide":
                    if self._root:
                        self._root.destroy()
                    return
        except queue.Empty:
            pass

        if self._root:
            self._root.after(50, self._process_queue)

    def _reposition(self) -> None:
        """Recalcula posicao vertical apos mudanca de tamanho do texto."""
        if self._root is None or self._label is None:
            return
        self._root.update_idletasks()
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        win_w = min(_MAX_WIDTH_PX, screen_w - 40)
        win_h = self._label.winfo_reqheight() + 2 * _PADDING
        x = (screen_w - win_w) // 2
        y = screen_h - win_h - 80
        self._root.geometry(f"{win_w}x{win_h}+{x}+{y}")
