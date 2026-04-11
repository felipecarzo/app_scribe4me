"""Orquestrador: hotkey -> grava -> transcreve -> cola."""

import logging
import sys
import time
import threading
import webbrowser
from pathlib import Path

from src.platform import platform

import pyperclip
from pynput import keyboard as kb

from src.config import (
    Config, APP_NAME, GITHUB_URL,
    load_hotkeys, load_api_keys, load_api_config,
    parse_hotkey, hotkey_display,
)
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.transcriber_api import create_api_transcriber
from src.realtime_manager import DeepgramRealtimeManager
from src.realtime_overlay import RealtimeOverlay
from src.clipboard import OutputHandler
from src.hardware import detect_hardware, recommend_model
from src.settings_window import open_settings_window
from src.tray import TrayIcon, AppState

logger = logging.getLogger("scribe4me")


def _setup_logging(config: Config) -> tuple[Path, Path]:
    """Configura logging para arquivo diario e (se console disponivel) stdout.

    Retorna (log_dir, log_file_do_dia).
    """
    from datetime import date

    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{date.today().isoformat()}.log"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    # Adiciona console handler apenas se nao estiver em modo frozen (PyInstaller --windowed)
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    return log_dir, log_file


class Scribe4me:
    """Orquestra gravacao, transcricao e saida de texto."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.transcriber = Transcriber(self.config)
        self.recorder = Recorder(self.config)
        self.output = OutputHandler(self.config)
        self._toggle_active = False
        self._quit_event = threading.Event()
        self._listener: kb.Listener | None = None
        self._ready_timer: threading.Timer | None = None
        self._log_file: Path | None = None
        self._log_dir: Path | None = None

        # Detecta hardware e recomenda modelo
        self._hw = detect_hardware()
        self._recommended_model = recommend_model(self._hw)

        # Hotkeys dinamicos — carrega do config
        self._hotkeys = load_hotkeys()
        self._parse_all_hotkeys()

        # API transcription
        self._api_cfg = load_api_config()
        self._api_keys = load_api_keys()
        self._api_transcriber = create_api_transcriber(
            self._api_cfg["backend"], self._api_keys, self.config.language
        )
        self._realtime_manager: DeepgramRealtimeManager | None = None
        self._overlay = RealtimeOverlay()

        self._tray = TrayIcon(
            on_quit=self._request_quit,
            on_copy_last=self._copy_last_text,
            on_open_log=self._open_log,
            on_open_log_dir=self._open_log_dir,
            on_open_settings=self._open_settings,
            on_help=self._open_help,
            hotkeys=self._hotkeys,
        )

        # Tracking de teclas modificadoras para detectar combinacoes
        self._pressed_keys: set = set()

    def _parse_all_hotkeys(self) -> None:
        """Faz parse dos hotkeys atuais em (modifiers, vk)."""
        self._hk_ptt_mods, self._hk_ptt_vk = parse_hotkey(self._hotkeys["push_to_talk"])
        self._hk_tog_mods, self._hk_tog_vk = parse_hotkey(self._hotkeys["toggle"])
        self._hk_cancel_mods, self._hk_cancel_vk = parse_hotkey(self._hotkeys["cancel"])
        self._hk_quit_mods, self._hk_quit_vk = parse_hotkey(self._hotkeys["quit"])

    # --- Callbacks do tray ---

    def _request_quit(self) -> None:
        """Callback do tray icon para encerrar."""
        logger.info("Quit solicitado.")
        self._quit_event.set()
        if self._listener:
            self._listener.stop()

    def _copy_last_text(self) -> None:
        """Copia o ultimo texto transcrito para o clipboard."""
        text = self.output.last_text
        if text:
            pyperclip.copy(text)
            self._tray.notify(APP_NAME, f"Texto copiado ({len(text)} chars)")
            logger.info("Ultimo texto copiado via menu.")
        else:
            self._tray.notify(APP_NAME, "Nenhum texto disponivel.")

    def _open_log(self) -> None:
        """Abre o log do dia no editor padrao."""
        if self._log_file and self._log_file.exists():
            platform.open_path(self._log_file)

    def _open_log_dir(self) -> None:
        """Abre a pasta de logs no gerenciador de arquivos."""
        if self._log_dir and self._log_dir.exists():
            platform.open_path(self._log_dir)

    def _open_settings(self) -> None:
        """Abre a janela de configuracoes unificada."""
        def _on_hotkeys(new_hotkeys: dict[str, str]):
            self._hotkeys = new_hotkeys
            self._parse_all_hotkeys()
            self._tray.update_hotkeys(new_hotkeys)
            self._tray.notify(APP_NAME, "Atalhos atualizados!")
            logger.info("Hotkeys atualizados: %s", new_hotkeys)

        def _on_prompt(content: str):
            self.transcriber.set_custom_prompt(content)
            label = "personalizado" if content else "padrao"
            self._tray.notify(APP_NAME, f"Prompt {label} salvo.")
            logger.info("Prompt atualizado (%s).", label)

        def _on_api(backend: str, realtime: bool):
            self._api_cfg = {"backend": backend, "realtime": realtime}
            self._api_keys = load_api_keys()
            self.config.api_backend = backend
            self.config.api_realtime = realtime
            self._api_transcriber = create_api_transcriber(
                backend, self._api_keys, self.config.language
            )
            mode = "realtime" if realtime else "batch"
            label = backend if backend != "local" else "local (Whisper)"
            self._tray.notify(APP_NAME, f"Backend: {label} ({mode})")
            logger.info("API backend: '%s' (realtime=%s).", backend, realtime)

        def _on_output_mode(mode: str):
            self.config.output_mode = mode
            label = "Colar no cursor" if mode == "cursor" else "So clipboard (Ctrl+V)"
            self._tray.notify(APP_NAME, f"Modo: {label}")
            logger.info("Modo de saida: %s", mode)

        open_settings_window(
            on_save_hotkeys=_on_hotkeys,
            on_save_prompt=_on_prompt,
            on_save_api=_on_api,
            on_change_model=self._change_model,
            on_change_output_mode=_on_output_mode,
            current_model=self.config.model,
            recommended_model=self._recommended_model,
        )

    def _open_help(self) -> None:
        """Abre a pagina do projeto no GitHub."""
        webbrowser.open(GITHUB_URL)
        logger.info("Ajuda aberta no navegador.")

    def _change_model(self, model_name: str) -> None:
        """Troca o modelo Whisper em background."""
        def _reload():
            self._tray.set_state(AppState.LOADING)
            self._tray.notify(APP_NAME, f"Baixando/carregando modelo '{model_name}'...")
            try:
                self.transcriber.reload_model(model_name)
                self.config.model = model_name
                self._tray.set_state(AppState.IDLE)
                self._tray.notify(APP_NAME, f"Modelo '{model_name}' pronto!")
                logger.info("Modelo trocado para '%s'.", model_name)
            except Exception as e:
                logger.error("Erro ao trocar modelo: %s", e)
                self._tray.set_state(AppState.IDLE)
                self._tray.notify(APP_NAME, f"Erro ao carregar modelo: {e}")

        threading.Thread(target=_reload, daemon=True).start()

    # --- Hotkey handlers ---

    def _is_realtime_mode(self) -> bool:
        """Retorna True se realtime esta ativo e configurado."""
        return (
            self.config.api_backend == "deepgram"
            and self.config.api_realtime
            and bool(self._api_keys.get("deepgram", "").strip())
        )

    def _start_realtime(self) -> None:
        """Inicia o manager de realtime e o overlay."""
        api_key = self._api_keys.get("deepgram", "").strip()
        lang = "pt-BR" if self.config.language.startswith("pt") else self.config.language

        self._realtime_manager = DeepgramRealtimeManager(
            api_key=api_key,
            language=lang,
            on_partial=self._on_realtime_partial,
            on_final=self._on_realtime_final,
            on_fragment=self._on_realtime_fragment,
        )
        ok = self._realtime_manager.start()
        if ok:
            self.recorder.chunk_callback = self._realtime_manager.send_chunk
            self._overlay.show()
        else:
            self._tray.notify(APP_NAME, "Erro ao conectar Deepgram realtime. Usando batch.")
            self._realtime_manager = None
            self.recorder.chunk_callback = None

    def _stop_realtime(self) -> str:
        """Para o manager de realtime e o overlay. Retorna texto final."""
        self.recorder.chunk_callback = None
        text = ""
        if self._realtime_manager is not None:
            text = self._realtime_manager.stop()
            self._realtime_manager = None
        self._overlay.hide()
        return text

    def _on_realtime_partial(self, text: str) -> None:
        """Callback — texto parcial chegando do Deepgram (acumulado)."""
        self._overlay.update(text)

    def _on_realtime_final(self, text: str) -> None:
        """Callback — acumulado total atualizado (para o overlay)."""
        self._overlay.update(text)

    def _on_realtime_fragment(self, sentence: str) -> None:
        """Callback — nova frase confirmada pelo Deepgram.

        No modo cursor: injeta imediatamente no cursor ativo (sem esperar o fim).
        No modo clipboard: nao faz nada aqui — o texto e colado todo no final.
        """
        if self.config.output_mode == "cursor" and sentence:
            # Adiciona espaco antes da frase se nao for o inicio da gravacao
            text_to_inject = sentence + " "
            self.output.send(text_to_inject)
            logger.info("Realtime injetado no cursor: %s", sentence)

    def _on_push_to_talk_press(self) -> None:
        """Ctrl+Alt+H press — inicia gravacao."""
        if not self.recorder.is_recording:
            logger.info("Gravando (push-to-talk)...")
            self._cancel_ready_timer()
            self._tray.set_state(AppState.RECORDING)
            if self._is_realtime_mode():
                self._start_realtime()
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        """Win+H release — para e transcreve."""
        if self.recorder.is_recording and not self._toggle_active:
            self._process_recording()

    def _on_toggle(self) -> None:
        """Toggle — alterna gravacao on/off."""
        if not self._toggle_active:
            self._toggle_active = True
            self._cancel_ready_timer()
            self._tray.set_state(AppState.RECORDING)
            logger.info("Gravando (toggle ON)...")
            if self._is_realtime_mode():
                self._start_realtime()
            self.recorder.start()
        else:
            self._toggle_active = False
            self._process_recording()

    def _on_cancel(self) -> None:
        """Cancela a gravacao em andamento sem processar."""
        if self.recorder.is_recording:
            self._toggle_active = False
            if self._realtime_manager is not None:
                self._stop_realtime()
            self.recorder.stop()  # descarta o audio
            self._tray.set_state(AppState.IDLE)
            self._tray.notify(APP_NAME, "Gravacao cancelada.")
            logger.info("Gravacao cancelada pelo usuario.")

    def _process_recording(self) -> None:
        """Para gravacao, transcreve (local, API batch ou realtime) e envia texto."""
        t0 = time.perf_counter()
        self._tray.set_state(AppState.TRANSCRIBING)
        logger.info("Processando...")

        if self._is_realtime_mode() and self._realtime_manager is not None:
            audio = self.recorder.stop()
            text = self._stop_realtime()
            if not text:
                # Fallback para batch se realtime nao retornou nada
                text = self.transcriber.transcribe(audio)
            elif self.config.output_mode == "cursor":
                # Modo cursor: texto ja foi injetado fragmento a fragmento.
                # Apenas registra o last_text para "Copiar ultimo texto" funcionar.
                self.output._last_text = text.rstrip()
                # Pula o send() — vai direto para o estado READY_TO_COPY
                if text:
                    elapsed = time.perf_counter() - t0
                    logger.info(">>> [realtime cursor] %s (%.1fs)", text, elapsed)
                    self._tray.set_state(AppState.READY_TO_COPY)
                    self._start_ready_timer()
                else:
                    self._tray.set_state(AppState.IDLE)
                return
        elif self._api_transcriber is not None:
            # API batch
            audio = self.recorder.stop()
            try:
                text = self._api_transcriber.transcribe(audio, self.config.sample_rate)
            except Exception as e:
                logger.error("Erro na API de transcricao (%s): %s", self.config.api_backend, e)
                self._tray.notify(APP_NAME, f"Erro API {self.config.api_backend}: {e}")
                text = self.transcriber.transcribe(audio)  # fallback local
        else:
            # Local Whisper
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)

        if text:
            self.output.send(text)
            elapsed = time.perf_counter() - t0
            logger.info(">>> %s (%.1fs)", text, elapsed)
            self._tray.set_state(AppState.READY_TO_COPY)
            self._start_ready_timer()
        else:
            logger.info("Nenhum texto detectado.")
            self._tray.set_state(AppState.IDLE)

    # --- Ready-to-copy timer ---

    def _start_ready_timer(self) -> None:
        """Volta pro idle apos timeout."""
        self._cancel_ready_timer()
        self._ready_timer = threading.Timer(
            self.config.ready_to_copy_timeout,
            self._ready_timeout,
        )
        self._ready_timer.daemon = True
        self._ready_timer.start()

    def _ready_timeout(self) -> None:
        """Timeout do estado azul — volta ao idle."""
        if self._tray.state == AppState.READY_TO_COPY:
            self._tray.set_state(AppState.IDLE)

    def _cancel_ready_timer(self) -> None:
        if self._ready_timer is not None:
            self._ready_timer.cancel()
            self._ready_timer = None

    # --- pynput Listener ---

    @staticmethod
    def _get_vk(key) -> int | None:
        """Extrai o virtual key code de uma tecla."""
        if hasattr(key, "vk") and key.vk is not None:
            return key.vk
        if hasattr(key, "value") and hasattr(key.value, "vk"):
            return key.value.vk
        if hasattr(key, "char") and key.char is not None:
            return ord(key.char.upper())
        return None

    def _active_mods(self) -> set[str]:
        """Retorna set dos modificadores atualmente pressionados."""
        mods = set()
        if any(k in self._pressed_keys for k in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r)):
            mods.add("ctrl")
        if any(k in self._pressed_keys for k in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r)):
            mods.add("alt")
        if any(k in self._pressed_keys for k in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r)):
            mods.add("shift")
        return mods

    def _match_hotkey(self, vk: int | None, required_mods: set[str], required_vk: int | None) -> bool:
        """Verifica se a tecla e modificadores batem com um hotkey configurado."""
        if vk is None or required_vk is None:
            return False
        return vk == required_vk and required_mods <= self._active_mods()

    def _on_press(self, key) -> None:
        """Callback de tecla pressionada."""
        self._pressed_keys.add(key)
        vk = self._get_vk(key)

        # Quit — funciona mesmo durante loading
        if self._match_hotkey(vk, self._hk_quit_mods, self._hk_quit_vk):
            self._request_quit()
            return

        # Bloqueia hotkeys durante loading
        if self._tray.state == AppState.LOADING:
            return

        # Cancel — cancela gravacao em andamento
        if self._match_hotkey(vk, self._hk_cancel_mods, self._hk_cancel_vk):
            self._on_cancel()
            return

        # Toggle
        if self._match_hotkey(vk, self._hk_tog_mods, self._hk_tog_vk):
            self._on_toggle()
            return

        # Push-to-talk start
        if self._match_hotkey(vk, self._hk_ptt_mods, self._hk_ptt_vk):
            self._on_push_to_talk_press()
            return

    def _on_release(self, key) -> None:
        """Callback de tecla solta."""
        vk = self._get_vk(key)

        # Push-to-talk stop — verifica se a tecla solta e a do PTT
        if vk == self._hk_ptt_vk and self.recorder.is_recording and not self._toggle_active:
            self._on_push_to_talk_release()

        self._pressed_keys.discard(key)

    # --- Run ---

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        self._tray.start()
        self._tray.set_state(AppState.LOADING)

        # Inicia listener antes do warm-up (Ctrl+Q ja funciona)
        self._listener = kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        # Carrega modelo local apenas se o backend for local
        # (evita espera de ~5s desnecessaria quando usando API)
        if self.config.api_backend == "local" or self._api_transcriber is None:
            logger.info("Carregando modelo Whisper...")
            try:
                self.transcriber.load_model()
                self.transcriber.warm_up()
            except Exception as e:
                logger.error("Falha ao carregar modelo: %s", e, exc_info=True)
                self._tray.set_state(AppState.IDLE)
                self._tray.notify(APP_NAME, f"Erro ao carregar modelo: {e}")
                # Permite trocar modelo pelo menu mesmo com erro
                self._quit_event.wait()
                self._tray.stop()
                return
        else:
            logger.info(
                "Modelo local ignorado no startup (backend: %s).", self.config.api_backend
            )

        logger.info("Pronto!")
        logger.info("  Push-to-talk: %s (segura e fala)", hotkey_display(self._hotkeys["push_to_talk"]))
        logger.info("  Toggle:       %s (aperta pra iniciar/parar)", hotkey_display(self._hotkeys["toggle"]))
        logger.info("  Cancelar:     %s (cancela gravacao)", hotkey_display(self._hotkeys["cancel"]))
        logger.info("  Saida:        %s", self.config.output_mode)
        logger.info("  Sair:         %s", hotkey_display(self._hotkeys["quit"]))

        self._tray.set_state(AppState.IDLE)
        self._tray.notify(APP_NAME, f"Pronto! {hotkey_display(self._hotkeys['push_to_talk'])} para gravar.")

        # Aguarda quit
        self._quit_event.wait()
        logger.info("Encerrando.")

        self._cancel_ready_timer()
        if self._listener.is_alive():
            self._listener.stop()
        self._tray.stop()

        if self.recorder.is_recording:
            self.recorder.stop()


def _acquire_single_instance():
    """Garante que apenas uma instancia do Scribe4me rode por vez (cross-platform)."""
    return platform.acquire_single_instance(APP_NAME)


def _show_error_dialog(title: str, message: str) -> None:
    """Mostra dialogo de erro nativo (cross-platform)."""
    platform.show_error_dialog(title, message)


def main():
    config = Config()

    # Permitir trocar modo de saida via argumento
    if "--clipboard" in sys.argv:
        config.output_mode = "clipboard"
    elif "--cursor" in sys.argv:
        config.output_mode = "cursor"

    # Detecta hardware e ajusta device/modelo automaticamente
    hw = detect_hardware()
    if not hw.cuda_available:
        config.device = "cpu"
    recommended = recommend_model(hw)
    if "--model" not in " ".join(sys.argv):
        config.model = recommended

    # Permite override via --model <nome>
    for i, arg in enumerate(sys.argv):
        if arg == "--model" and i + 1 < len(sys.argv):
            config.model = sys.argv[i + 1]

    log_dir, log_file = _setup_logging(config)
    _mutex = _acquire_single_instance()

    logger.info("Hardware: GPU=%s (%d MB), RAM=%d MB", hw.gpu_name or "nenhuma", hw.gpu_vram_mb, hw.ram_mb)
    logger.info("Modelo recomendado: %s / Modelo selecionado: %s", recommended, config.model)

    try:
        app = Scribe4me(config)
        app._log_dir = log_dir
        app._log_file = log_file
        app.run()
    except Exception as e:
        logger.critical("Erro fatal: %s", e, exc_info=True)
        _show_error_dialog(
            f"{APP_NAME} — Erro",
            f"Ocorreu um erro inesperado:\n\n{e}\n\nVeja o log em:\n{log_file}",
        )


if __name__ == "__main__":
    main()
