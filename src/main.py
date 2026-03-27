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

from src.config import Config, APP_NAME, AppMode
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.clipboard import OutputHandler
from src.gui import SpeedOsperGUI, QueueLogHandler
from src.hardware import detect_hardware, recommend_model
from src.model_prefetch import prefetch_models_async
from src.player import AudioPlayer
from src.profiles import list_profiles, get_profile_by_name, get_default_profile, Profile
from src.tray import TrayIcon, AppState
from src.voice_commands import VoiceCommandEngine

logger = logging.getLogger("speedosper")


def _setup_logging(config: Config, log_queue: queue.Queue | None = None) -> Path:
    """Configura logging para arquivo, console (se disponivel) e GUI queue."""
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "speedosper.log"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    # Adiciona console handler apenas se nao estiver em modo frozen (PyInstaller --windowed)
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler(sys.stdout))

    # Handler para GUI (queue-based)
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


class SpeedOsper:
    """Orquestra gravacao, transcricao e saida de texto."""

    def __init__(self, config: Config | None = None, log_queue: queue.Queue | None = None):
        self.config = config or Config()
        self.transcriber = Transcriber(self.config)
        self.recorder = Recorder(self.config)
        self.output = OutputHandler(self.config)
        self.player = AudioPlayer()
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

        # Lista nomes de profiles para o tray e GUI
        self._profiles = list_profiles()
        profile_names = [p.name for p in self._profiles]

        from src.hardware import WHISPER_MODELS
        model_names = list(WHISPER_MODELS.keys())

        # GUI (janela tkinter — opcional, inicia escondida)
        self._log_queue = log_queue
        self._gui: SpeedOsperGUI | None = None
        if log_queue is not None:
            self._gui = SpeedOsperGUI(
                log_queue=log_queue,
                on_record_toggle=self._on_gui_record_toggle,
                on_profile_change=self._change_profile,
                on_mode_change=self._gui_change_mode,
                on_model_change=self._change_model,
                profile_names=profile_names,
                mode_names=[m.value for m in AppMode],
                model_names=model_names,
                current_profile=self._active_profile.name,
                current_mode=self.config.mode.value,
                current_model=self.config.model,
            )

        self._tray = TrayIcon(
            on_quit=self._request_quit,
            on_copy_last=self._copy_last_text,
            on_open_log=self._open_log,
            on_model_change=self._change_model,
            on_mode_change=self._change_mode,
            on_target_lang_change=self._change_target_lang,
            on_profile_change=self._change_profile,
            on_activate=self._toggle_gui,
            current_model=self.config.model,
            recommended_model=self._recommended_model,
            current_mode=self.config.mode,
            current_target_lang=self.config.target_language,
            current_profile_name=self._active_profile.name,
            profile_names=profile_names,
            code_mode=self._active_profile.code_mode,
        )

        # Tracking de teclas modificadoras para detectar combinacoes
        self._pressed_keys: set = set()

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
        """Abre o arquivo de log no editor padrao."""
        if self._log_file and self._log_file.exists():
            os.startfile(str(self._log_file))

    def _prefetch_models(self) -> None:
        """Baixa modelos de traducao/TTS em background."""
        bridge = self.transcriber._bridge
        if bridge is None:
            return

        def _on_progress(step_name, current, total):
            self._tray.notify(APP_NAME, f"Baixando {step_name} ({current}/{total})...")

        def _on_complete(success):
            if success:
                logger.info("Prefetch de modelos concluido.")
            else:
                logger.warning("Prefetch de modelos incompleto — alguns modelos podem falhar.")

        prefetch_models_async(
            bridge,
            language=self.config.language,
            target_language=self.config.target_language,
            on_progress=_on_progress,
            on_complete=_on_complete,
        )

    def _change_mode(self, mode: AppMode) -> None:
        """Troca o modo de operacao."""
        self.config.mode = mode
        logger.info("Modo alterado para: %s", mode.value)
        self._tray.notify(APP_NAME, f"Modo: {mode.value.capitalize()}")
        if self._gui:
            self._gui.update_mode(mode.value)

    def _change_target_lang(self, lang_code: str) -> None:
        """Troca o idioma alvo para traducao."""
        self.config.target_language = lang_code
        from src.config import SUPPORTED_LANGUAGES
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, lang_code)
        logger.info("Idioma alvo alterado para: %s (%s)", lang_name, lang_code)
        self._tray.notify(APP_NAME, f"Idioma alvo: {lang_name}")

    def _load_initial_profile(self) -> Profile:
        """Carrega profile configurado ou default."""
        profile = get_profile_by_name(self.config.active_profile_name)
        if profile:
            logger.info("Profile carregado: '%s' (code_mode=%s)", profile.name, profile.code_mode)
            return profile
        default = get_default_profile()
        logger.info("Profile '%s' nao encontrado, usando default: '%s'",
                     self.config.active_profile_name, default.name)
        return default

    def _change_profile(self, profile_name: str) -> None:
        """Troca o profile ativo."""
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

    def _set_state(self, state: AppState) -> None:
        """Atualiza estado no tray e no GUI."""
        self._tray.set_state(state)
        if self._gui:
            # Mapeia AppState para label legivel
            labels = {
                AppState.LOADING: "Carregando...",
                AppState.IDLE: "Idle",
                AppState.RECORDING: "Gravando",
                AppState.TRANSCRIBING: "Transcrevendo...",
                AppState.READY_TO_COPY: "Texto pronto",
                AppState.PLAYING: "Reproduzindo",
            }
            self._gui.update_state(labels.get(state, state.value))

    def _toggle_gui(self) -> None:
        """Alterna visibilidade da janela GUI (double-click no tray)."""
        if self._gui:
            self._gui.toggle()

    def _on_gui_record_toggle(self) -> None:
        """Callback do botao gravar no GUI."""
        self._on_toggle()

    def _gui_change_mode(self, mode_str: str) -> None:
        """Callback do dropdown de modo no GUI (recebe string)."""
        try:
            mode = AppMode(mode_str)
            self._change_mode(mode)
        except ValueError:
            logger.warning("Modo invalido do GUI: %s", mode_str)

    def _change_model(self, model_name: str) -> None:
        """Troca o modelo Whisper em background."""
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
        """Ctrl+Alt+H press — inicia gravacao."""
        if not self.recorder.is_recording:
            logger.info("Gravando (push-to-talk)...")
            self._cancel_ready_timer()
            self._set_state(AppState.RECORDING)
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        """Win+H release — para e transcreve."""
        if self.recorder.is_recording and not self._toggle_active:
            self._process_recording()

    def _on_toggle(self) -> None:
        """Win+Shift+H — alterna gravacao on/off."""
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
        """Para gravacao e despacha para o pipeline do modo ativo."""
        t0 = time.perf_counter()
        self._set_state(AppState.TRANSCRIBING)
        logger.info("Processando (modo=%s)...", self.config.mode.value)

        audio = self.recorder.stop()
        mode = self.config.mode

        if mode == AppMode.SCRIBE:
            text = self._pipeline_scribe(audio)
        elif mode == AppMode.TRANSLATE:
            text = self._pipeline_translate(audio)
        elif mode == AppMode.VOICE:
            text = self._pipeline_voice(audio)
        else:
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
        """Modo scribe: fala -> texto. Se code_mode, processa comandos."""
        text = self.transcriber.transcribe(audio)
        if not text:
            return ""
        if self._active_profile.code_mode:
            results = self._voice_engine.process(text)
            self.output.send_command_results(results)
            logger.info("[code_mode] %s -> %d comando(s)", text, len(results))
            return ""  # ja enviou via command_results
        return text

    def _pipeline_translate(self, audio) -> str:
        """Modo translate: fala -> texto -> traducao."""
        text = self.transcriber.transcribe(audio)
        if not text:
            return ""
        try:
            bridge = self.transcriber._bridge
            if bridge is None:
                logger.error("Motor bridge nao inicializado.")
                return text
            result = bridge.translate(text, self.config.language, self.config.target_language)
            logger.info("Traducao: '%s' -> '%s' (cache=%s, quality=%.2f)",
                        text, result.translation, result.cache_hit, result.quality_score)
            return result.translation
        except Exception as e:
            logger.error("Falha na traducao: %s — retornando texto original.", e)
            return text

    def _pipeline_voice(self, audio) -> str:
        """Modo voice: fala -> texto -> traducao -> TTS -> playback."""
        try:
            bridge = self.transcriber._bridge
            if bridge is None:
                logger.error("Motor bridge nao inicializado.")
                return ""
            result = bridge.voice_translate(
                audio, self.config.target_language, src_lang=self.config.language,
            )
            logger.info(
                "Voice: '%s' -> '%s' (cache=%s, quality=%.2f)",
                result.source_text, result.translated_text,
                result.cache_hit, result.quality_score,
            )
            # Reproduz audio traduzido
            if len(result.samples) > 0:
                self._set_state(AppState.PLAYING)
                self.player.play(result.samples, result.sample_rate)
            return result.translated_text
        except Exception as e:
            logger.error("Falha no voice translate: %s", e)
            return ""

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
        if self._tray._state == AppState.READY_TO_COPY:
            self._set_state(AppState.IDLE)

    def _cancel_ready_timer(self) -> None:
        if self._ready_timer is not None:
            self._ready_timer.cancel()
            self._ready_timer = None

    # --- pynput Listener ---

    # Virtual key codes (Windows)
    _VK_H = 72
    _VK_T = 84
    _VK_Q = 81

    @staticmethod
    def _get_vk(key) -> int | None:
        """Extrai o virtual key code de uma tecla."""
        if hasattr(key, "vk") and key.vk is not None:
            return key.vk
        if hasattr(key, "value") and hasattr(key.value, "vk"):
            return key.value.vk
        # KeyCode.from_char
        if hasattr(key, "char") and key.char is not None:
            return ord(key.char.upper())
        return None

    def _on_press(self, key) -> None:
        """Callback de tecla pressionada."""
        self._pressed_keys.add(key)
        vk = self._get_vk(key)

        # Ctrl+Q -> quit (funciona mesmo durante loading)
        if vk == self._VK_Q and self._mod_ctrl():
            self._request_quit()
            return

        # Bloqueia hotkeys durante loading
        if self._tray._state == AppState.LOADING:
            return

        # Ctrl+Alt+T -> toggle
        if vk == self._VK_T and self._mod_ctrl() and self._mod_alt():
            self._on_toggle()
            return

        # Ctrl+Alt+H -> push-to-talk start
        if vk == self._VK_H and self._mod_ctrl() and self._mod_alt():
            self._on_push_to_talk_press()
            return

    def _on_release(self, key) -> None:
        """Callback de tecla solta."""
        vk = self._get_vk(key)

        # H release -> push-to-talk stop
        if vk == self._VK_H and self.recorder.is_recording and not self._toggle_active:
            self._on_push_to_talk_release()

        self._pressed_keys.discard(key)

    def _mod_ctrl(self) -> bool:
        """Verifica se Ctrl esta pressionado."""
        return any(
            k in self._pressed_keys
            for k in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r)
        )

    def _mod_alt(self) -> bool:
        """Verifica se Alt esta pressionado."""
        return any(
            k in self._pressed_keys
            for k in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r)
        )

    # --- Run ---

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        # Inicia GUI (escondida — abre com double-click no tray)
        if self._gui:
            self._gui.start()

        self._tray.start()
        self._set_state(AppState.LOADING)

        # Inicia listener antes do warm-up (Ctrl+Q ja funciona)
        self._listener = kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        # Carrega modelo (bolinha amarela piscando)
        logger.info("Carregando modelo Whisper...")
        try:
            self.transcriber.load_model()
            self.transcriber.warm_up()
        except Exception as e:
            logger.error("Falha ao carregar modelo: %s", e, exc_info=True)
            self._set_state(AppState.IDLE)
            self._tray.notify(APP_NAME, f"Erro ao carregar modelo: {e}")
            # Permite trocar modelo pelo menu mesmo com erro
            self._quit_event.wait()
            self._tray.stop()
            return

        logger.info("Pronto!")
        logger.info("  Modo:         %s", self.config.mode.value)
        logger.info("  Profile:      %s (code_mode=%s)", self._active_profile.name, self._active_profile.code_mode)
        logger.info("  Idioma alvo:  %s", self.config.target_language)
        logger.info("  Push-to-talk: Ctrl+Alt+H (segura e fala)")
        logger.info("  Toggle:       Ctrl+Alt+T (aperta pra iniciar/parar)")
        logger.info("  Saida:        %s", self.config.output_mode)
        logger.info("  Sair:         Ctrl+Q")

        self._set_state(AppState.IDLE)
        self._tray.notify(APP_NAME, "Pronto! Ctrl+Alt+H para gravar.")

        # Prefetch de modelos em background (traducao, TTS)
        if self.config.mode != AppMode.SCRIBE:
            self._prefetch_models()

        # Aguarda quit
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
    """Garante que apenas uma instancia do SpeedOsper rode por vez (Windows mutex)."""
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, f"{APP_NAME}_SingleInstance")
    last_error = ctypes.windll.kernel32.GetLastError()
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        logger.error("%s ja esta rodando. Encerrando.", APP_NAME)
        sys.exit(1)
    return mutex  # manter referencia para nao ser garbage collected


def _show_error_dialog(title: str, message: str) -> None:
    """Mostra erro via MessageBox do Windows (funciona sem console)."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, message, title, 0x10  # MB_ICONERROR
        )
    except Exception:
        pass


def main():
    config = Config()

    # Permitir trocar modo de saida via argumento
    if "--clipboard" in sys.argv:
        config.output_mode = "clipboard"
    elif "--cursor" in sys.argv:
        config.output_mode = "cursor"

    # Modo de operacao
    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            try:
                config.mode = AppMode(sys.argv[i + 1])
            except ValueError:
                pass
        if arg == "--target-lang" and i + 1 < len(sys.argv):
            config.target_language = sys.argv[i + 1]

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

    # Queue para log real-time no GUI (--no-gui desabilita)
    log_queue = None if "--no-gui" in sys.argv else queue.Queue(maxsize=1000)

    log_file = _setup_logging(config, log_queue=log_queue)
    _mutex = _acquire_single_instance()

    logger.info("Hardware: GPU=%s (%d MB), RAM=%d MB", hw.gpu_name or "nenhuma", hw.gpu_vram_mb, hw.ram_mb)
    logger.info("Modelo recomendado: %s / Modelo selecionado: %s", recommended, config.model)

    try:
        app = SpeedOsper(config, log_queue=log_queue)
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
