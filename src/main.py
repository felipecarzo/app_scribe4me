"""Orquestrador: hotkey -> grava -> transcreve -> cola."""

import logging
import os
import queue
import sys
import time
import threading
from pathlib import Path

import pyperclip
from pynput import keyboard as kb

from src.config import Config, APP_NAME
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.clipboard import OutputHandler
from src.gui import Scribe4meGUI, QueueLogHandler
from src.hardware import detect_hardware, recommend_model, WHISPER_MODELS
from src.profiles import list_profiles, get_profile_by_name, get_default_profile, Profile
from src.tray import TrayIcon, AppState
from src.voice_commands import VoiceCommandEngine

logger = logging.getLogger("scribe4me")


def _setup_logging(config: Config, log_queue: queue.Queue | None = None) -> Path:
    """Configura logging para arquivo, console (se disponivel) e GUI queue."""
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scribe4me.log"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler(sys.stdout))

    if log_queue is not None:
        queue_handler = QueueLogHandler(log_queue)
        queue_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S",
        ))
        handlers.append(queue_handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    return log_file


class Scribe4me:
    """Orquestra gravacao, transcricao e saida de texto."""

    def __init__(self, config: Config | None = None, log_queue: queue.Queue | None = None):
        self.config = config or Config()
        self.transcriber = Transcriber(self.config)
        self.recorder = Recorder(self.config)
        self.output = OutputHandler(self.config)
        self._voice_engine = VoiceCommandEngine()
        self._toggle_active = False
        self._quit_event = threading.Event()
        self._listener: kb.Listener | None = None
        self._ready_timer: threading.Timer | None = None
        self._log_file: Path | None = None

        # Carrega profile ativo
        self._active_profile = self._load_initial_profile()
        self.transcriber.set_prompt(self._active_profile.prompt)

        # Detecta hardware e recomenda modelo
        self._hw = detect_hardware()
        self._recommended_model = recommend_model(self._hw)

        # Lista profiles
        self._profiles = list_profiles()
        profile_names = [p.name for p in self._profiles]
        model_names = list(WHISPER_MODELS.keys())

        # GUI (janela tkinter — opcional, inicia escondida)
        self._log_queue = log_queue
        self._gui: Scribe4meGUI | None = None
        if log_queue is not None:
            self._gui = Scribe4meGUI(
                log_queue=log_queue,
                on_record_toggle=self._on_gui_record_toggle,
                on_profile_change=self._change_profile,
                on_model_change=self._change_model,
                profile_names=profile_names,
                model_names=model_names,
                current_profile=self._active_profile.name,
                current_model=self.config.model,
            )

        self._tray = TrayIcon(
            on_quit=self._request_quit,
            on_copy_last=self._copy_last_text,
            on_open_log=self._open_log,
            on_model_change=self._change_model,
            on_profile_change=self._change_profile,
            on_activate=self._toggle_gui,
            current_model=self.config.model,
            recommended_model=self._recommended_model,
            current_profile_name=self._active_profile.name,
            profile_names=profile_names,
            code_mode=self._active_profile.code_mode,
        )

        self._pressed_keys: set = set()

    # --- State management ---

    def _set_state(self, state: AppState) -> None:
        """Atualiza estado no tray e no GUI."""
        self._tray.set_state(state)
        if self._gui:
            labels = {
                AppState.LOADING: "Carregando...",
                AppState.IDLE: "Idle",
                AppState.RECORDING: "Gravando",
                AppState.TRANSCRIBING: "Transcrevendo...",
                AppState.READY_TO_COPY: "Texto pronto",
            }
            self._gui.update_state(labels.get(state, state.value))

    # --- Callbacks ---

    def _request_quit(self) -> None:
        logger.info("Quit solicitado.")
        self._quit_event.set()
        if self._listener:
            self._listener.stop()

    def _copy_last_text(self) -> None:
        text = self.output.last_text
        if text:
            pyperclip.copy(text)
            self._tray.notify(APP_NAME, f"Texto copiado ({len(text)} chars)")
            logger.info("Ultimo texto copiado via menu.")
        else:
            self._tray.notify(APP_NAME, "Nenhum texto disponivel.")

    def _open_log(self) -> None:
        if self._log_file and self._log_file.exists():
            os.startfile(str(self._log_file))

    def _toggle_gui(self) -> None:
        if self._gui:
            self._gui.toggle()

    def _on_gui_record_toggle(self) -> None:
        self._on_toggle()

    def _load_initial_profile(self) -> Profile:
        profile = get_profile_by_name(self.config.active_profile_name)
        if profile:
            logger.info("Profile carregado: '%s' (code_mode=%s)", profile.name, profile.code_mode)
            return profile
        default = get_default_profile()
        logger.info("Profile '%s' nao encontrado, usando default: '%s'",
                     self.config.active_profile_name, default.name)
        return default

    def _change_profile(self, profile_name: str) -> None:
        profile = get_profile_by_name(profile_name)
        if not profile:
            logger.warning("Profile '%s' nao encontrado.", profile_name)
            return
        self._active_profile = profile
        self.config.active_profile_name = profile_name
        self.transcriber.set_prompt(profile.prompt)
        self._tray.set_profile(profile.name, profile.code_mode)
        if self._gui:
            self._gui.update_profile(profile.name)
        code_suffix = " [Code]" if profile.code_mode else ""
        logger.info("Profile trocado para '%s'%s", profile.name, code_suffix)
        self._tray.notify(APP_NAME, f"Profile: {profile.name}{code_suffix}")

    def _change_model(self, model_name: str) -> None:
        def _reload():
            self._set_state(AppState.LOADING)
            self._tray.notify(APP_NAME, f"Baixando/carregando modelo '{model_name}'...")
            try:
                self.transcriber.reload_model(model_name)
                self._set_state(AppState.IDLE)
                self._tray.notify(APP_NAME, f"Modelo '{model_name}' pronto!")
                if self._gui:
                    self._gui.update_model(model_name)
                logger.info("Modelo trocado para '%s'.", model_name)
            except Exception as e:
                logger.error("Erro ao trocar modelo: %s", e)
                self._set_state(AppState.IDLE)
                self._tray.notify(APP_NAME, f"Erro ao carregar modelo: {e}")

        threading.Thread(target=_reload, daemon=True).start()

    # --- Hotkey handlers ---

    def _on_push_to_talk_press(self) -> None:
        if not self.recorder.is_recording:
            logger.info("Gravando (push-to-talk)...")
            self._cancel_ready_timer()
            self._set_state(AppState.RECORDING)
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        if self.recorder.is_recording and not self._toggle_active:
            self._process_recording()

    def _on_toggle(self) -> None:
        if not self._toggle_active:
            self._toggle_active = True
            self._cancel_ready_timer()
            self._set_state(AppState.RECORDING)
            logger.info("Gravando (toggle ON)...")
            self.recorder.start()
        else:
            self._toggle_active = False
            self._process_recording()

    def _process_recording(self) -> None:
        t0 = time.perf_counter()
        self._set_state(AppState.TRANSCRIBING)
        logger.info("Processando...")

        audio = self.recorder.stop()
        text = self._pipeline_scribe(audio)

        if text:
            self.output.send(text)
            elapsed = time.perf_counter() - t0
            logger.info(">>> %s (%.1fs)", text, elapsed)
            self._set_state(AppState.READY_TO_COPY)
            self._start_ready_timer()
        else:
            logger.info("Nenhum texto detectado.")
            self._set_state(AppState.IDLE)

    def _pipeline_scribe(self, audio) -> str:
        """Fala -> texto. Se code_mode, processa comandos de voz."""
        text = self.transcriber.transcribe(audio)
        if not text:
            return ""
        if self._active_profile.code_mode:
            results = self._voice_engine.process(text)
            self.output.send_command_results(results)
            logger.info("[code_mode] %s -> %d comando(s)", text, len(results))
            return ""
        return text

    # --- Ready-to-copy timer ---

    def _start_ready_timer(self) -> None:
        self._cancel_ready_timer()
        self._ready_timer = threading.Timer(
            self.config.ready_to_copy_timeout,
            self._ready_timeout,
        )
        self._ready_timer.daemon = True
        self._ready_timer.start()

    def _ready_timeout(self) -> None:
        if self._tray._state == AppState.READY_TO_COPY:
            self._set_state(AppState.IDLE)

    def _cancel_ready_timer(self) -> None:
        if self._ready_timer is not None:
            self._ready_timer.cancel()
            self._ready_timer = None

    # --- pynput Listener ---

    _VK_H = 72
    _VK_T = 84
    _VK_Q = 81

    @staticmethod
    def _get_vk(key) -> int | None:
        if hasattr(key, "vk") and key.vk is not None:
            return key.vk
        if hasattr(key, "value") and hasattr(key.value, "vk"):
            return key.value.vk
        if hasattr(key, "char") and key.char is not None:
            return ord(key.char.upper())
        return None

    def _on_press(self, key) -> None:
        self._pressed_keys.add(key)
        vk = self._get_vk(key)

        if vk == self._VK_Q and self._mod_ctrl():
            self._request_quit()
            return

        if self._tray._state == AppState.LOADING:
            return

        if vk == self._VK_T and self._mod_ctrl() and self._mod_alt():
            self._on_toggle()
            return

        if vk == self._VK_H and self._mod_ctrl() and self._mod_alt():
            self._on_push_to_talk_press()
            return

    def _on_release(self, key) -> None:
        vk = self._get_vk(key)
        if vk == self._VK_H and self.recorder.is_recording and not self._toggle_active:
            self._on_push_to_talk_release()
        self._pressed_keys.discard(key)

    def _mod_ctrl(self) -> bool:
        return any(
            k in self._pressed_keys
            for k in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r)
        )

    def _mod_alt(self) -> bool:
        return any(
            k in self._pressed_keys
            for k in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r)
        )

    # --- Run ---

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        if self._gui:
            self._gui.start()

        self._tray.start()
        self._set_state(AppState.LOADING)

        self._listener = kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        logger.info("Carregando modelo Whisper...")
        try:
            self.transcriber.load_model()
            self.transcriber.warm_up()
        except Exception as e:
            logger.error("Falha ao carregar modelo: %s", e, exc_info=True)
            self._set_state(AppState.IDLE)
            self._tray.notify(APP_NAME, f"Erro ao carregar modelo: {e}")
            self._quit_event.wait()
            self._tray.stop()
            return

        logger.info("Pronto!")
        logger.info("  Profile:      %s (code_mode=%s)", self._active_profile.name, self._active_profile.code_mode)
        logger.info("  Push-to-talk: Ctrl+Alt+H (segura e fala)")
        logger.info("  Toggle:       Ctrl+Alt+T (aperta pra iniciar/parar)")
        logger.info("  Saida:        %s", self.config.output_mode)
        logger.info("  Sair:         Ctrl+Q")

        self._set_state(AppState.IDLE)
        self._tray.notify(APP_NAME, "Pronto! Ctrl+Alt+H para gravar.")

        self._quit_event.wait()
        logger.info("Encerrando.")

        self._cancel_ready_timer()
        if self._listener.is_alive():
            self._listener.stop()
        self._tray.stop()
        if self._gui:
            self._gui.stop()

        if self.recorder.is_recording:
            self.recorder.stop()


def _acquire_single_instance():
    """Garante que apenas uma instancia rode por vez (Windows mutex)."""
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, f"{APP_NAME}_SingleInstance")
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:
        logger.error("%s ja esta rodando. Encerrando.", APP_NAME)
        sys.exit(1)
    return mutex


def _show_error_dialog(title: str, message: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        pass


def main():
    config = Config()

    if "--clipboard" in sys.argv:
        config.output_mode = "clipboard"
    elif "--cursor" in sys.argv:
        config.output_mode = "cursor"

    # Detecta hardware e ajusta device/modelo
    hw = detect_hardware()
    if not hw.cuda_available:
        config.device = "cpu"
    recommended = recommend_model(hw)
    if "--model" not in " ".join(sys.argv):
        config.model = recommended

    for i, arg in enumerate(sys.argv):
        if arg == "--model" and i + 1 < len(sys.argv):
            config.model = sys.argv[i + 1]

    log_queue = None if "--no-gui" in sys.argv else queue.Queue(maxsize=1000)

    log_file = _setup_logging(config, log_queue=log_queue)
    _mutex = _acquire_single_instance()

    logger.info("Hardware: GPU=%s (%d MB), RAM=%d MB", hw.gpu_name or "nenhuma", hw.gpu_vram_mb, hw.ram_mb)
    logger.info("Modelo recomendado: %s / Modelo selecionado: %s", recommended, config.model)

    try:
        app = Scribe4me(config, log_queue=log_queue)
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
