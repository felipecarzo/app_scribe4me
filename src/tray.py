"""System tray icon com indicador de estado e notificacoes."""

import logging
import threading
from enum import Enum
from typing import Callable

from PIL import Image, ImageDraw
import pystray

from src.config import APP_NAME
from src.hardware import WHISPER_MODELS, model_label

logger = logging.getLogger("scribe4me.tray")


class AppState(Enum):
    LOADING = "loading"              # amarelo piscando — aquecendo modelo
    IDLE = "idle"                    # verde — pronto
    RECORDING = "recording"          # vermelho — gravando
    TRANSCRIBING = "transcribing"    # vermelho piscando — processando
    READY_TO_COPY = "ready_to_copy"  # azul — texto disponivel


# Cores por estado
_COLORS = {
    AppState.LOADING: "#FFC107",        # amarelo
    AppState.IDLE: "#4CAF50",           # verde
    AppState.RECORDING: "#F44336",      # vermelho
    AppState.TRANSCRIBING: "#F44336",   # vermelho (pisca)
    AppState.READY_TO_COPY: "#2196F3",  # azul
}

_TOOLTIPS = {
    AppState.LOADING: f"{APP_NAME} — Carregando modelo...",
    AppState.IDLE: f"{APP_NAME} — Pronto (Ctrl+Alt+H)",
    AppState.RECORDING: f"{APP_NAME} — Gravando...",
    AppState.TRANSCRIBING: f"{APP_NAME} — Transcrevendo...",
    AppState.READY_TO_COPY: f"{APP_NAME} — Texto pronto (Ctrl+V)",
}


def _create_icon_image(color: str, size: int = 64) -> Image.Image:
    """Cria icone com silhueta de microfone sobre circulo colorido."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 2

    draw.ellipse([m, m, size - m, size - m], fill=color)

    s = size
    white = "#FFFFFF"

    bw = s * 0.22
    bh = s * 0.32
    cx = s / 2
    top = s * 0.18
    draw.rounded_rectangle(
        [cx - bw / 2, top, cx + bw / 2, top + bh],
        radius=bw / 2, fill=white,
    )

    arc_w = s * 0.34
    arc_top = top + bh * 0.3
    arc_bot = top + bh + s * 0.10
    lw = max(2, int(s * 0.05))
    draw.arc(
        [cx - arc_w / 2, arc_top, cx + arc_w / 2, arc_bot],
        start=0, end=180, fill=white, width=lw,
    )

    haste_top = arc_bot - lw / 2
    haste_bot = haste_top + s * 0.10
    draw.line([cx, haste_top, cx, haste_bot], fill=white, width=lw)

    base_w = s * 0.18
    draw.line(
        [cx - base_w / 2, haste_bot, cx + base_w / 2, haste_bot],
        fill=white, width=lw,
    )

    return img


def _create_blank_image(size: int = 64) -> Image.Image:
    """Cria icone transparente (usado no piscar)."""
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


class TrayIcon:
    """Gerencia o system tray icon do Scribe4me."""

    def __init__(
        self,
        on_quit: Callable | None = None,
        on_copy_last: Callable | None = None,
        on_open_log: Callable | None = None,
        on_model_change: Callable[[str], None] | None = None,
        on_profile_change: Callable[[str], None] | None = None,
        on_activate: Callable | None = None,
        current_model: str = "large-v3",
        recommended_model: str = "large-v3",
        current_profile_name: str = "Tech-Dev",
        profile_names: list[str] | None = None,
        code_mode: bool = False,
    ):
        self._state = AppState.IDLE
        self._on_quit = on_quit
        self._on_copy_last = on_copy_last
        self._on_open_log = on_open_log
        self._on_model_change = on_model_change
        self._on_profile_change = on_profile_change
        self._on_activate = on_activate
        self._current_model = current_model
        self._recommended_model = recommended_model
        self._current_profile_name = current_profile_name
        self._profile_names = profile_names or ["Tech-Dev"]
        self._code_mode = code_mode
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._blink_timer: threading.Timer | None = None
        self._blink_visible = True

    def _build_menu(self) -> pystray.Menu:
        """Constroi o menu de contexto."""
        model_items = []
        for name in WHISPER_MODELS:
            label = model_label(name, self._recommended_model)
            model_items.append(
                pystray.MenuItem(
                    label,
                    self._make_model_callback(name),
                    checked=lambda item, n=name: n == self._current_model,
                    radio=True,
                )
            )

        profile_items = []
        for pname in self._profile_names:
            profile_items.append(
                pystray.MenuItem(
                    pname,
                    self._make_profile_callback(pname),
                    checked=lambda item, n=pname: n == self._current_profile_name,
                    radio=True,
                )
            )

        code_suffix = " [Code]" if self._code_mode else ""

        return pystray.Menu(
            pystray.MenuItem(APP_NAME, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ctrl+Alt+H  —  Gravar (segura e fala)", None, enabled=False),
            pystray.MenuItem("Ctrl+Alt+T  —  Toggle (iniciar/parar)", None, enabled=False),
            pystray.MenuItem("Ctrl+Q            —  Sair", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"Profile: {self._current_profile_name}{code_suffix}",
                pystray.Menu(*profile_items),
            ),
            pystray.MenuItem(
                f"Modelo: {self._current_model.capitalize()}",
                pystray.Menu(*model_items),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Abrir janela", self._activate_clicked),
            pystray.MenuItem("Copiar ultimo texto", self._copy_last_clicked),
            pystray.MenuItem("Abrir log", self._open_log_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._quit_clicked),
        )

    def _make_profile_callback(self, profile_name: str):
        def callback(icon, item):
            if profile_name != self._current_profile_name:
                self._current_profile_name = profile_name
                self._update_menu()
                if self._on_profile_change:
                    self._on_profile_change(profile_name)
        return callback

    def _make_model_callback(self, model_name: str):
        def callback(icon, item):
            if model_name != self._current_model:
                self._current_model = model_name
                self._update_menu()
                if self._on_model_change:
                    self._on_model_change(model_name)
        return callback

    def _update_menu(self) -> None:
        if self._icon is not None:
            self._icon.menu = self._build_menu()

    def start(self) -> None:
        """Inicia o tray icon em thread separada."""
        self._icon = pystray.Icon(
            name="scribe4me",
            icon=_create_icon_image(_COLORS[AppState.IDLE]),
            title=_TOOLTIPS[AppState.IDLE],
            menu=self._build_menu(),
        )
        if self._on_activate:
            self._icon.on_activate = self._on_activate
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_state(self, state: AppState) -> None:
        """Atualiza cor, tooltip e notificacao do icone."""
        old_state = self._state
        self._state = state
        self._stop_blink()

        if self._icon is None:
            return

        if state == AppState.IDLE and self._code_mode:
            self._icon.icon = _create_icon_image("#00BCD4")
            self._icon.title = _TOOLTIPS[state] + " [Code]"
        else:
            self._icon.icon = _create_icon_image(_COLORS[state])
            self._icon.title = _TOOLTIPS[state]

        if state in (AppState.LOADING, AppState.TRANSCRIBING):
            self._start_blink()

        if state != old_state:
            self._notify_state(state)

    def notify(self, title: str, message: str) -> None:
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.debug("Falha ao enviar notificacao", exc_info=True)

    def stop(self) -> None:
        self._stop_blink()
        if self._icon is not None:
            self._icon.stop()

    # --- Blink ---

    def _start_blink(self) -> None:
        self._blink_visible = True
        self._blink_tick()

    def _blink_tick(self) -> None:
        if self._state not in (AppState.LOADING, AppState.TRANSCRIBING) or self._icon is None:
            return
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self._icon.icon = _create_icon_image(_COLORS[self._state])
        else:
            self._icon.icon = _create_blank_image()
        self._blink_timer = threading.Timer(0.5, self._blink_tick)
        self._blink_timer.daemon = True
        self._blink_timer.start()

    def _stop_blink(self) -> None:
        if self._blink_timer is not None:
            self._blink_timer.cancel()
            self._blink_timer = None

    # --- Notificacoes ---

    def _notify_state(self, state: AppState) -> None:
        messages = {
            AppState.LOADING: (APP_NAME, "Carregando modelo Whisper... aguarde."),
            AppState.RECORDING: (APP_NAME, "Gravando..."),
            AppState.TRANSCRIBING: (APP_NAME, "Processando transcricao..."),
            AppState.READY_TO_COPY: (APP_NAME, "Texto pronto! Ctrl+V para colar."),
        }
        if state in messages:
            title, msg = messages[state]
            self.notify(title, msg)

    # --- Menu callbacks ---

    def _quit_clicked(self, icon, item) -> None:
        if self._on_quit:
            self._on_quit()

    def _copy_last_clicked(self, icon, item) -> None:
        if self._on_copy_last:
            self._on_copy_last()

    def _open_log_clicked(self, icon, item) -> None:
        if self._on_open_log:
            self._on_open_log()

    def _activate_clicked(self, icon, item) -> None:
        if self._on_activate:
            self._on_activate()

    def set_profile(self, profile_name: str, code_mode: bool) -> None:
        """Atualiza profile ativo no tray."""
        self._current_profile_name = profile_name
        self._code_mode = code_mode
        self._update_menu()
        if self._state == AppState.IDLE and self._icon is not None:
            color = "#00BCD4" if code_mode else _COLORS[AppState.IDLE]
            self._icon.icon = _create_icon_image(color)
            suffix = " [Code]" if code_mode else ""
            self._icon.title = _TOOLTIPS[AppState.IDLE] + suffix
