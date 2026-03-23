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
        """Ctrl+H pressionado — inicia gravacao."""
        if not self.recorder.is_recording:
            print("[speedosper] Gravando (push-to-talk)...")
            self.recorder.start()

    def _on_push_to_talk_release(self) -> None:
        """Ctrl+H solto — para gravacao e transcreve."""
        if self.recorder.is_recording:
            print("[speedosper] Processando...")
            audio = self.recorder.stop()
            text = self.transcriber.transcribe(audio)
            if text:
                self.output.send(text)
            else:
                print("[speedosper] Nenhum texto detectado.")

    def _on_toggle(self) -> None:
        """Ctrl+Shift+H — alterna gravacao on/off."""
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
                self.output.send(text)
            else:
                print("[speedosper] Nenhum texto detectado.")

    def run(self) -> None:
        """Inicia o loop principal com hotkeys."""
        print("[speedosper] Carregando modelo Whisper...")
        self.transcriber.load_model()

        print(f"[speedosper] Pronto!")
        print(f"  Push-to-talk: {self.config.hotkey_push_to_talk} (segura e fala)")
        print(f"  Toggle:       {self.config.hotkey_toggle} (aperta pra iniciar/parar)")
        print(f"  Saida:        {self.config.output_mode}")
        print(f"  Sair:         Ctrl+Q")

        # Push-to-talk: segura pra gravar, solta pra transcrever
        keyboard.on_press_key(
            "h",
            lambda e: self._on_push_to_talk_press()
            if keyboard.is_pressed("ctrl") and not keyboard.is_pressed("shift")
            else None,
        )
        keyboard.on_release_key(
            "h",
            lambda e: self._on_push_to_talk_release(),
        )

        # Toggle: Ctrl+Shift+H
        keyboard.add_hotkey(
            self.config.hotkey_toggle,
            self._on_toggle,
            suppress=True,
        )

        # Sair com Ctrl+Q
        print("\n[speedosper] Aguardando hotkey...")
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
