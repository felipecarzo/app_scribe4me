"""Orquestrador: hotkey -> grava -> transcreve -> cola."""

import sys
import keyboard

from src.config import Config
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.clipboard import OutputHandler


class SpeedOsper:
    """Orquestra gravacao, transcricao e saida de texto."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.recorder = Recorder(self.config)
        self.transcriber = Transcriber(self.config)
        self.output = OutputHandler(self.config)
        self._toggle_active = False

    def _on_push_to_talk_press(self) -> None:
        """F20 press (Win+H via AHK) — inicia gravacao."""
        if not self.recorder.is_recording:
            print("[speedosper] Gravando (push-to-talk)...")
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        """F20 release (Win+H solto via AHK) — para e transcreve."""
        if self.recorder.is_recording:
            print("[speedosper] Processando...")
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)
            if text:
                print(f"\n>>> {text}\n")
                self.output.send(text)
            else:
                print("[speedosper] Nenhum texto detectado.")

    def _on_toggle(self) -> None:
        """F21 (Win+Shift+H via AHK) — alterna gravacao on/off."""
        if not self._toggle_active:
            self._toggle_active = True
            print("[speedosper] Gravando (toggle ON)...")
            self.recorder.start()
        else:
            self._toggle_active = False
            print("[speedosper] Processando...")
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)
            if text:
                print(f"\n>>> {text}\n")
                self.output.send(text)
            else:
                print("[speedosper] Nenhum texto detectado.")

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        print("[speedosper] Carregando modelo Whisper...")
        self.transcriber.load_model()

        print("[speedosper] Pronto!")
        print("  Push-to-talk: Win+H (segura e fala)")
        print("  Toggle:       Win+Shift+H (aperta pra iniciar/parar)")
        print(f"  Saida:        {self.config.output_mode}")
        print("  Sair:         Ctrl+Q")
        print()
        print("  IMPORTANTE: rode scripts/speedosper.ahk antes!")

        # Push-to-talk: F20 down/up (enviado pelo AHK quando Win+H e pressionado/solto)
        keyboard.on_press_key(self.config.hotkey_push_to_talk, lambda e: self._on_push_to_talk_press())
        keyboard.on_release_key(self.config.hotkey_push_to_talk, lambda e: self._on_push_to_talk_release())

        # Toggle: F21 (enviado pelo AHK quando Win+Shift+H e pressionado)
        keyboard.on_press_key(self.config.hotkey_toggle, lambda e: self._on_toggle())

        # Sair com Ctrl+Q
        print("[speedosper] Aguardando hotkey...")
        keyboard.wait("ctrl+q")
        print("[speedosper] Encerrando.")

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
