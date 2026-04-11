"""System tray icon com indicador de estado e notificacoes."""

import logging
import sys
import threading
from enum import Enum
from typing import Callable

from PIL import Image, ImageDraw
import pystray

from src.config import APP_NAME, hotkey_display, load_hotkeys

logger = logging.getLogger("scribe4me.tray")


class AppState(Enum):
    LOADING = "loading"              # amarelo piscando — aquecendo modelo
    IDLE = "idle"                    # verde — pronto
    RECORDING = "recording"          # vermelho — gravando
    TRANSCRIBING = "transcribing"    # vermelho piscando — processando
    READY_TO_COPY = "ready_to_copy"  # azul — texto disponivel


# Cores por estado
_COLORS = {
    AppState.LOADING: (255, 193, 7),        # amarelo
    AppState.IDLE: (76, 175, 80),           # verde
    AppState.RECORDING: (244, 67, 54),      # vermelho
    AppState.TRANSCRIBING: (244, 67, 54),   # vermelho (pisca)
    AppState.READY_TO_COPY: (33, 150, 243), # azul
}

def _build_tooltips(hotkeys: dict[str, str] | None = None) -> dict[AppState, str]:
    """Constroi tooltips com os atalhos atuais."""
    if hotkeys is None:
        hotkeys = load_hotkeys()
    ptt = hotkey_display(hotkeys["push_to_talk"])
    return {
        AppState.LOADING: f"{APP_NAME} — Carregando modelo...",
        AppState.IDLE: f"{APP_NAME} — Pronto ({ptt})",
        AppState.RECORDING: f"{APP_NAME} — Gravando...",
        AppState.TRANSCRIBING: f"{APP_NAME} — Transcrevendo...",
        AppState.READY_TO_COPY: f"{APP_NAME} — Texto pronto (Ctrl+V)",
    }


def _draw_mic_silhouette(draw: ImageDraw.Draw, cx: int, cy: int, s: float, color="white"):
    """Desenha silhueta de microfone simples e solida, legivel em 16x16."""
    w = max(1, int(2 * s))

    # Capsula (oval preenchida)
    cap_w = int(8 * s)
    cap_h = int(14 * s)
    cap_top = cy - int(10 * s)
    draw.rounded_rectangle(
        [cx - cap_w, cap_top, cx + cap_w, cap_top + cap_h],
        radius=cap_w,
        fill=color,
    )

    # Arco U (suporte)
    arc_w = int(11 * s)
    arc_top = cap_top + cap_h - int(5 * s)
    arc_h = int(10 * s)
    draw.arc(
        [cx - arc_w, arc_top, cx + arc_w, arc_top + arc_h * 2],
        start=0, end=180,
        fill=color,
        width=w,
    )

    # Haste vertical
    haste_top = arc_top + arc_h
    haste_bot = haste_top + int(5 * s)
    draw.line([cx, haste_top, cx, haste_bot], fill=color, width=w)

    # Base horizontal
    base_hw = int(6 * s)
    draw.line([cx - base_hw, haste_bot, cx + base_hw, haste_bot], fill=color, width=w)


def _create_state_icon(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    """Cria icone colorido com silhueta de microfone branca."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 2
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)

    s = size / 64
    cx, cy = size // 2, size // 2
    _draw_mic_silhouette(draw, cx, cy, s, color="white")
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
        on_open_log_dir: Callable | None = None,
        on_open_settings: Callable | None = None,
        on_help: Callable | None = None,
        hotkeys: dict[str, str] | None = None,
    ):
        self._state = AppState.IDLE
        self._on_quit = on_quit
        self._on_copy_last = on_copy_last
        self._on_open_log = on_open_log
        self._on_open_log_dir = on_open_log_dir
        self._on_open_settings = on_open_settings
        self._on_help = on_help
        self._hotkeys = hotkeys or load_hotkeys()
        self._tooltips = _build_tooltips(self._hotkeys)
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._blink_timer: threading.Timer | None = None
        self._blink_visible = True

    def _state_icon(self, state: AppState, size: int = 64) -> Image.Image:
        """Retorna o icone do tray para o estado dado."""
        return _create_state_icon(_COLORS[state], size)

    def _build_menu(self) -> pystray.Menu:
        """Constroi o menu de contexto."""
        ptt = hotkey_display(self._hotkeys["push_to_talk"])
        tog = hotkey_display(self._hotkeys["toggle"])
        cnc = hotkey_display(self._hotkeys["cancel"])
        qt = hotkey_display(self._hotkeys["quit"])

        return pystray.Menu(
            pystray.MenuItem(APP_NAME, self._help_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"{ptt}  —  Gravar (segura e fala)", None, enabled=False),
            pystray.MenuItem(f"{tog}  —  Toggle (iniciar/parar)", None, enabled=False),
            pystray.MenuItem(f"{cnc}  —  Cancelar gravacao", None, enabled=False),
            pystray.MenuItem(f"{qt}  —  Sair", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Configuracoes...", self._settings_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Copiar ultimo texto", self._copy_last_clicked),
            pystray.MenuItem("Log de hoje", self._open_log_clicked),
            pystray.MenuItem("Pasta de logs", self._open_log_dir_clicked),
            pystray.MenuItem("Ajuda", self._help_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._quit_clicked),
        )

    @property
    def state(self) -> AppState:
        return self._state

    def _update_menu(self) -> None:
        """Atualiza o menu apos troca de modelo."""
        if self._icon is not None:
            self._icon.menu = self._build_menu()

    def start(self) -> None:
        """Cria o tray icon.

        No Windows/Linux inicia em thread separada.
        No macOS o pystray exige a main thread — chame run_blocking() apos start().
        """
        self._icon = pystray.Icon(
            name="scribe4me",
            icon=self._state_icon(AppState.IDLE),
            title=self._tooltips[AppState.IDLE],
            menu=self._build_menu(),
        )
        if sys.platform != "darwin":
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()

    def run_blocking(self) -> None:
        """Roda o tray no thread atual (bloqueia ate icon.stop() ser chamado).

        Deve ser chamado a partir da main thread no macOS.
        No-op se o icon ainda nao foi criado.
        """
        if self._icon is not None:
            self._icon.run()

    def set_state(self, state: AppState) -> None:
        """Atualiza cor, tooltip e notificacao do icone."""
        old_state = self._state
        self._state = state

        # Para o piscar se estava piscando
        self._stop_blink()

        if self._icon is None:
            return

        self._icon.icon = self._state_icon(state)
        self._icon.title = self._tooltips[state]

        # Inicia piscar se carregando ou transcrevendo
        if state in (AppState.LOADING, AppState.TRANSCRIBING):
            self._start_blink()

        # Notificacoes
        if state != old_state:
            self._notify_state(state)

    def notify(self, title: str, message: str) -> None:
        """Envia notificacao via tray icon."""
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.debug("Falha ao enviar notificacao", exc_info=True)

    def stop(self) -> None:
        """Remove o tray icon."""
        self._stop_blink()
        if self._icon is not None:
            self._icon.stop()

    # --- Blink ---

    def _start_blink(self) -> None:
        """Inicia o piscar do icone (500ms)."""
        self._blink_visible = True
        self._blink_tick()

    def _blink_tick(self) -> None:
        """Alterna entre visivel e transparente."""
        if self._state not in (AppState.LOADING, AppState.TRANSCRIBING) or self._icon is None:
            return
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self._icon.icon = self._state_icon(self._state)
        else:
            self._icon.icon = _create_blank_image()
        self._blink_timer = threading.Timer(0.5, self._blink_tick)
        self._blink_timer.daemon = True
        self._blink_timer.start()

    def _stop_blink(self) -> None:
        """Para o timer de piscar."""
        if self._blink_timer is not None:
            self._blink_timer.cancel()
            self._blink_timer = None

    # --- Notificacoes ---

    def _notify_state(self, state: AppState) -> None:
        """Envia notificacao nativa de acordo com o estado."""
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

    def update_hotkeys(self, hotkeys: dict[str, str]) -> None:
        """Atualiza hotkeys, tooltips e menu apos edicao."""
        self._hotkeys = hotkeys
        self._tooltips = _build_tooltips(hotkeys)
        if self._icon is not None:
            self._icon.title = self._tooltips[self._state]
        self._update_menu()

    def _quit_clicked(self, icon, item) -> None:
        if self._on_quit:
            self._on_quit()

    def _copy_last_clicked(self, icon, item) -> None:
        if self._on_copy_last:
            self._on_copy_last()

    def _open_log_clicked(self, icon, item) -> None:
        if self._on_open_log:
            self._on_open_log()

    def _open_log_dir_clicked(self, icon, item) -> None:
        if self._on_open_log_dir:
            self._on_open_log_dir()

    def _settings_clicked(self, icon, item) -> None:
        if self._on_open_settings:
            self._on_open_settings()

    def _help_clicked(self, icon, item) -> None:
        if self._on_help:
            self._on_help()
