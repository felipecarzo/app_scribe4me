"""Overlay flutuante premium para exibir transcrição em tempo real."""

import logging
import queue
import sys
import threading
import tkinter as tk

logger = logging.getLogger("scribe4me")

_PILL_COLOR = "#0F172A"      # Slate 900 (Dark Mode Premium)
_TEXT_COLOR = "#F8FAFC"      # Slate 50
_FONT = ("Segoe UI", 13, "bold")
_MAX_WIDTH_PX = 700
_PADDING_X = 24
_PADDING_Y = 16
_ALPHA = 0.90
_CORNER_RADIUS = 20

def _create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Cria um retângulo arredondado no canvas usando um polígono."""
    points = [
        x1+radius, y1,   x1+radius, y1,   x2-radius, y1,   x2-radius, y1,
        x2, y1,          x2, y1+radius,   x2, y1+radius,   x2, y2-radius,
        x2, y2-radius,   x2, y2,          x2-radius, y2,   x2-radius, y2,
        x1+radius, y2,   x1+radius, y2,   x1, y2,          x1, y2-radius,
        x1, y2-radius,   x1, y1+radius,   x1, y1+radius,   x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)


class RealtimeOverlay:
    """Janela flutuante topmost estilo 'Ilha Dinâmica' ou 'Pílula'."""

    def __init__(self):
        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._rect_id: int | None = None
        self._text_id: int | None = None
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False

    def show(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, text: str) -> None:
        self._queue.put(("update", text))

    def hide(self) -> None:
        self._queue.put(("hide", None))

    def _run(self) -> None:
        try:
            self._root = tk.Tk()
            self._root.withdraw()
            self._setup_window()
            self._root.after(50, self._process_queue)
            self._root.mainloop()
        except Exception as e:
            logger.warning("RealtimeOverlay erro: %s", e)
        finally:
            self._running = False
            self._root = None
            self._canvas = None
            self._rect_id = None
            self._text_id = None

    def _setup_window(self) -> None:
        root = self._root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", _ALPHA)

        # Transparência real no Windows
        if sys.platform == "win32":
            bg_key = "#FF00FF"
            root.configure(bg=bg_key)
            root.attributes("-transparentcolor", bg_key)
        else:
            bg_key = _PILL_COLOR
            root.configure(bg=bg_key)

        self._canvas = tk.Canvas(
            root, bg=bg_key, highlightthickness=0, bd=0,
            width=_MAX_WIDTH_PX, height=100
        )
        self._canvas.pack(fill="both", expand=True)

        self._rect_id = _create_rounded_rect(
            self._canvas, 0, 0, _MAX_WIDTH_PX, 100, 
            radius=_CORNER_RADIUS, fill=_PILL_COLOR
        )

        self._text_id = self._canvas.create_text(
            _PADDING_X, _PADDING_Y,
            anchor="nw",
            text="...",
            fill=_TEXT_COLOR,
            font=_FONT,
            width=_MAX_WIDTH_PX - 2 * _PADDING_X,
            justify="center"
        )
        
        self._reposition("...")
        root.deiconify()

    def _process_queue(self) -> None:
        try:
            while True:
                cmd, payload = self._queue.get_nowait()
                if cmd == "update" and self._canvas is not None and self._text_id is not None:
                    txt = payload or "..."
                    self._canvas.itemconfig(self._text_id, text=txt)
                    self._reposition(txt)
                elif cmd == "hide":
                    if self._root:
                        self._root.destroy()
                    return
        except queue.Empty:
            pass

        if self._root:
            self._root.after(50, self._process_queue)

    def _reposition(self, current_text: str) -> None:
        if self._root is None or self._canvas is None or self._text_id is None:
            return

        # Calcular bbox real do texto
        bbox = self._canvas.bbox(self._text_id)
        if not bbox:
            return
            
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Evita encolher mais do que um tamanho mínimo pra não ficar muito tremido
        win_w = min(_MAX_WIDTH_PX, text_w + 2 * _PADDING_X)
        if win_w < 200:
            win_w = 200
            
        win_h = text_h + 2 * _PADDING_Y
        
        # Centraliza o texto no canvas redesenhado
        text_x = (win_w - text_w) / 2
        
        # Atualiza retângulo de fundo
        self._canvas.config(width=win_w, height=win_h)
        self._canvas.delete(self._rect_id)
        self._rect_id = _create_rounded_rect(
            self._canvas, 0, 0, win_w, win_h, 
            radius=_CORNER_RADIUS, fill=_PILL_COLOR, width=2, outline="#334155" # leve borda
        )
        
        # Move o texto pra ficar centralizado e desenha-o acima do background
        self._canvas.coords(self._text_id, text_x, _PADDING_Y)
        self._canvas.tag_raise(self._text_id)

        # Atualiza Posição na Tela na parte inferior
        self._root.update_idletasks()
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        
        x = int((screen_w - win_w) / 2)
        y = int(screen_h - win_h - 120)  # subiu mais um pouco (120px da taskbar)
        
        self._root.geometry(f"{win_w}x{win_h}+{x}+{y}")
