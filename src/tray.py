"""System tray icon com indicador de estado e notificacoes."""

import logging
import threading
from enum import Enum
from typing import Callable

from PIL import Image, ImageDraw
import pystray

from src.config import APP_NAME, AppMode, SUPPORTED_LANGUAGES
from src.hardware import WHISPER_MODELS, model_label

logger = logging.getLogger("speedosper.tray")


class AppState(Enum):
    LOADING = "loading"              # amarelo piscando — aquecendo modelo
    IDLE = "idle"                    # verde — pronto
    RECORDING = "recording"          # vermelho — gravando
    TRANSCRIBING = "transcribing"    # vermelho piscando — processando
    READY_TO_COPY = "ready_to_copy"  # azul — texto disponivel
    PLAYING = "playing"              # roxo — reproduzindo audio traduzido


# Cores por estado
_COLORS = {
    AppState.LOADING: "#FFC107",        # amarelo
    AppState.IDLE: "#4CAF50",           # verde
    AppState.RECORDING: "#F44336",      # vermelho
    AppState.TRANSCRIBING: "#F44336",   # vermelho (pisca)
    AppState.READY_TO_COPY: "#2196F3",  # azul
    AppState.PLAYING: "#9C27B0",        # roxo
}

_TOOLTIPS = {
    AppState.LOADING: f"{APP_NAME} — Carregando modelo...",
    AppState.IDLE: f"{APP_NAME} — Pronto (Ctrl+Alt+H)",
    AppState.RECORDING: f"{APP_NAME} — Gravando...",
    AppState.TRANSCRIBING: f"{APP_NAME} — Transcrevendo...",
    AppState.READY_TO_COPY: f"{APP_NAME} — Texto pronto (Ctrl+V)",
    AppState.PLAYING: f"{APP_NAME} — Reproduzindo...",
}


def _create_icon_image(color: str, size: int = 64) -> Image.Image:
    """Cria icone circular com a cor do estado."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    return img


def _create_blank_image(size: int = 64) -> Image.Image:
    """Cria icone transparente (usado no piscar)."""
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


class TrayIcon:
    """Gerencia o system tray icon do SpeedOsper."""

    def __init__(
        self,
        on_quit: Callable | None = None,
        on_copy_last: Callable | None = None,
        on_open_log: Callable | None = None,
        on_model_change: Callable[[str], None] | None = None,
        on_mode_change: Callable[[AppMode], None] | None = None,
        on_target_lang_change: Callable[[str], None] | None = None,
        current_model: str = "large-v3",
        recommended_model: str = "large-v3",
        current_mode: AppMode = AppMode.SCRIBE,
        current_target_lang: str = "en",
    ):
        self._state = AppState.IDLE
        self._on_quit = on_quit
        self._on_copy_last = on_copy_last
        self._on_open_log = on_open_log
        self._on_model_change = on_model_change
        self._on_mode_change = on_mode_change
        self._on_target_lang_change = on_target_lang_change
        self._current_model = current_model
        self._recommended_model = recommended_model
        self._current_mode = current_mode
        self._current_target_lang = current_target_lang
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._blink_timer: threading.Timer | None = None
        self._blink_visible = True

    def _build_menu(self) -> pystray.Menu:
        """Constroi o menu de contexto."""
        # Submenu de modelos
        model_items = []
        for name in WHISPER_MODELS:
            label = model_label(name, self._recommended_model)
            # Checkmark no modelo atual
            checked = name == self._current_model
            model_items.append(
                pystray.MenuItem(
                    label,
                    self._make_model_callback(name),
                    checked=lambda item, n=name: n == self._current_model,
                    radio=True,
                )
            )

        # Submenu de modos
        mode_items = []
        mode_labels = {
            AppMode.SCRIBE: "Scribe (fala -> texto)",
            AppMode.TRANSLATE: "Translate (fala -> texto traduzido)",
            AppMode.VOICE: "Voice (fala -> voz traduzida)",
        }
        for mode in AppMode:
            mode_items.append(
                pystray.MenuItem(
                    mode_labels[mode],
                    self._make_mode_callback(mode),
                    checked=lambda item, m=mode: m == self._current_mode,
                    radio=True,
                )
            )

        # Submenu de idioma alvo
        lang_items = []
        for code, label in SUPPORTED_LANGUAGES.items():
            lang_items.append(
                pystray.MenuItem(
                    f"{label} ({code})",
                    self._make_lang_callback(code),
                    checked=lambda item, c=code: c == self._current_target_lang,
                    radio=True,
                )
            )

        return pystray.Menu(
            pystray.MenuItem(APP_NAME, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ctrl+Alt+H  —  Gravar (segura e fala)", None, enabled=False),
            pystray.MenuItem("Ctrl+Alt+T  —  Toggle (iniciar/parar)", None, enabled=False),
            pystray.MenuItem("Ctrl+Q            —  Sair", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"Modo: {self._current_mode.value.capitalize()}",
                pystray.Menu(*mode_items),
            ),
            pystray.MenuItem(
                f"Idioma alvo: {SUPPORTED_LANGUAGES.get(self._current_target_lang, self._current_target_lang)}",
                pystray.Menu(*lang_items),
            ),
            pystray.MenuItem(
                f"Modelo: {self._current_model.capitalize()}",
                pystray.Menu(*model_items),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Copiar ultimo texto", self._copy_last_clicked),
            pystray.MenuItem("Abrir log", self._open_log_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._quit_clicked),
        )

    def _make_mode_callback(self, mode: AppMode):
        """Cria callback para selecao de modo."""
        def callback(icon, item):
            if mode != self._current_mode:
                self._current_mode = mode
                self._update_menu()
                if self._on_mode_change:
                    self._on_mode_change(mode)
        return callback

    def _make_lang_callback(self, lang_code: str):
        """Cria callback para selecao de idioma alvo."""
        def callback(icon, item):
            if lang_code != self._current_target_lang:
                self._current_target_lang = lang_code
                self._update_menu()
                if self._on_target_lang_change:
                    self._on_target_lang_change(lang_code)
        return callback

    def _make_model_callback(self, model_name: str):
        """Cria callback para selecao de modelo."""
        def callback(icon, item):
            if model_name != self._current_model:
                self._current_model = model_name
                self._update_menu()
                if self._on_model_change:
                    self._on_model_change(model_name)
        return callback

    def _update_menu(self) -> None:
        """Atualiza o menu apos troca de modelo."""
        if self._icon is not None:
            self._icon.menu = self._build_menu()

    def start(self) -> None:
        """Inicia o tray icon em thread separada."""
        self._icon = pystray.Icon(
            name="speedosper",
            icon=_create_icon_image(_COLORS[AppState.IDLE]),
            title=_TOOLTIPS[AppState.IDLE],
            menu=self._build_menu(),
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_state(self, state: AppState) -> None:
        """Atualiza cor, tooltip e notificacao do icone."""
        old_state = self._state
        self._state = state

        # Para o piscar se estava piscando
        self._stop_blink()

        if self._icon is None:
            return

        self._icon.icon = _create_icon_image(_COLORS[state])
        self._icon.title = _TOOLTIPS[state]

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
            self._icon.icon = _create_icon_image(_COLORS[self._state])
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
            AppState.PLAYING: (APP_NAME, "Reproduzindo audio traduzido..."),
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
