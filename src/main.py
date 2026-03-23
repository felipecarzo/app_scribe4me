"""Orquestrador: hotkey -> grava -> transcreve -> cola."""

import atexit
import subprocess
import sys
import time
from pathlib import Path

import keyboard

from src.config import Config
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.clipboard import OutputHandler
from src.tray import TrayIcon, AppState


class SpeedOsper:
    """Orquestra gravacao, transcricao e saida de texto."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.recorder = Recorder(self.config)
        self.transcriber = Transcriber(self.config)
        self.output = OutputHandler(self.config)
        self._toggle_active = False
        self._ahk_process: subprocess.Popen | None = None
        self._tray = TrayIcon(on_quit=self._request_quit)
        self._quit_requested = False

    def _request_quit(self) -> None:
        """Callback do tray icon para encerrar."""
        self._quit_requested = True
        keyboard.press_and_release("ctrl+q")

    def _on_push_to_talk_press(self) -> None:
        """F20 press (Win+H via AHK) — inicia gravacao."""
        if not self.recorder.is_recording:
            print("[speedosper] Gravando (push-to-talk)...")
            self._tray.set_state(AppState.RECORDING)
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        """F20 release (Win+H solto via AHK) — para e transcreve."""
        if self.recorder.is_recording:
            t0 = time.perf_counter()
            self._tray.set_state(AppState.TRANSCRIBING)
            print("[speedosper] Processando...")
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)
            if text:
                self.output.send(text)
                elapsed = time.perf_counter() - t0
                print(f"\n>>> {text}")
                print(f"    ({elapsed:.1f}s total)\n")
            else:
                print("[speedosper] Nenhum texto detectado.")
            self._tray.set_state(AppState.IDLE)

    def _on_toggle(self) -> None:
        """F21 (Win+Shift+H via AHK) — alterna gravacao on/off."""
        if not self._toggle_active:
            self._toggle_active = True
            self._tray.set_state(AppState.RECORDING)
            print("[speedosper] Gravando (toggle ON)...")
            self.recorder.start()
        else:
            self._toggle_active = False
            t0 = time.perf_counter()
            self._tray.set_state(AppState.TRANSCRIBING)
            print("[speedosper] Processando...")
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)
            if text:
                self.output.send(text)
                elapsed = time.perf_counter() - t0
                print(f"\n>>> {text}")
                print(f"    ({elapsed:.1f}s total)\n")
            else:
                print("[speedosper] Nenhum texto detectado.")
            self._tray.set_state(AppState.IDLE)

    def _start_ahk(self) -> None:
        """Lanca o script AHK automaticamente."""
        # PyInstaller empacota em _MEIPASS; em dev, usa o caminho normal
        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent
        ahk_script = base / "scripts" / "speedosper.ahk"
        if not ahk_script.exists():
            print(f"[speedosper] AVISO: {ahk_script} nao encontrado. Win+H pode nao funcionar.")
            return

        try:
            self._ahk_process = subprocess.Popen(
                ["autohotkey", str(ahk_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            atexit.register(self._stop_ahk)
            print("[speedosper] AHK iniciado (Win+H interceptado).")
        except FileNotFoundError:
            print("[speedosper] AVISO: AutoHotkey nao encontrado no PATH. Instale com: winget install AutoHotkey.AutoHotkey")

    def _stop_ahk(self) -> None:
        """Encerra o processo AHK."""
        if self._ahk_process and self._ahk_process.poll() is None:
            self._ahk_process.terminate()

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        self._start_ahk()
        self._tray.start()

        print("[speedosper] Carregando modelo Whisper...")
        self.transcriber.load_model()
        self.transcriber.warm_up()

        print("[speedosper] Pronto!")
        print("  Push-to-talk: Win+H (segura e fala)")
        print("  Toggle:       Win+Shift+H (aperta pra iniciar/parar)")
        print(f"  Saida:        {self.config.output_mode}")
        print("  Sair:         Ctrl+Q")

        # Push-to-talk: F20 down/up (enviado pelo AHK quando Win+H e pressionado/solto)
        keyboard.on_press_key(self.config.hotkey_push_to_talk, lambda e: self._on_push_to_talk_press())
        keyboard.on_release_key(self.config.hotkey_push_to_talk, lambda e: self._on_push_to_talk_release())

        # Toggle: F21 (enviado pelo AHK quando Win+Shift+H e pressionado)
        keyboard.on_press_key(self.config.hotkey_toggle, lambda e: self._on_toggle())

        # Sair com Ctrl+Q
        print("[speedosper] Aguardando hotkey...")
        keyboard.wait("ctrl+q")
        print("[speedosper] Encerrando.")
        self._tray.stop()

        if self.recorder.is_recording:
            self.recorder.stop()


def main():
    config = Config()

    # Permitir trocar modo de saida via argumento
    if "--clipboard" in sys.argv:
        config.output_mode = "clipboard"
    elif "--cursor" in sys.argv:
        config.output_mode = "cursor"

    app = SpeedOsper(config)
    app.run()


if __name__ == "__main__":
    main()
