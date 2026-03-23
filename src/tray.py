"""System tray icon com indicador de estado."""

import threading
from enum import Enum

from PIL import Image, ImageDraw
import pystray


class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


# Cores por estado
_COLORS = {
    AppState.IDLE: "#4CAF50",         # verde — pronto
    AppState.RECORDING: "#F44336",     # vermelho — gravando
    AppState.TRANSCRIBING: "#FF9800",  # laranja — processando
}

_TOOLTIPS = {
    AppState.IDLE: "SpeedOsper — Pronto (Win+H)",
    AppState.RECORDING: "SpeedOsper — Gravando...",
    AppState.TRANSCRIBING: "SpeedOsper — Transcrevendo...",
}


def _create_icon_image(color: str, size: int = 64) -> Image.Image:
    """Cria icone circular com a cor do estado."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    return img


class TrayIcon:
    """Gerencia o system tray icon do SpeedOsper."""

    def __init__(self, on_quit=None):
        self._state = AppState.IDLE
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Inicia o tray icon em thread separada."""
        menu = pystray.Menu(
            pystray.MenuItem("SpeedOsper", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair (Ctrl+Q)", self._quit_clicked),
        )
        self._icon = pystray.Icon(
            name="speedosper",
            icon=_create_icon_image(_COLORS[AppState.IDLE]),
            title=_TOOLTIPS[AppState.IDLE],
            menu=menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_state(self, state: AppState) -> None:
        """Atualiza cor e tooltip do icone."""
        self._state = state
        if self._icon is not None:
            self._icon.icon = _create_icon_image(_COLORS[state])
            self._icon.title = _TOOLTIPS[state]

    def stop(self) -> None:
        """Remove o tray icon."""
        if self._icon is not None:
            self._icon.stop()

    def _quit_clicked(self, icon, item):
        if self._on_quit:
            self._on_quit()
