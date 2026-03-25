"""Teste de integracao: pipeline completo gravacao -> transcricao -> saida."""

from unittest.mock import patch, MagicMock, call

import numpy as np

from src.config import Config
from src.main import SpeedOsper


class TestPipeline:
    """Testa o fluxo completo simulando push-to-talk e toggle."""

    def _make_app(self):
        config = Config(model="tiny", device="cpu", output_mode="clipboard")
        with patch("src.transcriber.MotorBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.transcribe.return_value = "Texto transcrito com sucesso."
            mock_bridge.version.return_value = "0.1.0"
            mock_cls.return_value = mock_bridge

            app = SpeedOsper(config)
            app.transcriber.load_model()
        return app, mock_bridge

    @patch("src.recorder.sd.InputStream")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_push_to_talk_flow(self, mock_clip, mock_ctrl, mock_stream, sample_audio):
        """Simula: press -> grava -> release -> transcreve -> saida clipboard."""
        app, mock_bridge = self._make_app()

        # Press: inicia gravacao
        app._on_push_to_talk_press()
        assert app.recorder.is_recording

        # Simula audio chegando no buffer
        audio_chunk = sample_audio.reshape(-1, 1)
        app.recorder._audio_callback(audio_chunk, len(sample_audio), None, None)

        # Release: para, transcreve, envia
        app._on_push_to_talk_release()
        assert not app.recorder.is_recording

        mock_bridge.transcribe.assert_called_once()
        mock_clip.copy.assert_called_once_with("Texto transcrito com sucesso.")

    @patch("src.recorder.sd.InputStream")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_toggle_flow(self, mock_clip, mock_ctrl, mock_stream, sample_audio):
        """Simula: toggle ON -> grava -> toggle OFF -> transcreve -> saida."""
        app, mock_bridge = self._make_app()

        # Toggle ON
        app._on_toggle()
        assert app.recorder.is_recording
        assert app._toggle_active

        # Audio
        audio_chunk = sample_audio.reshape(-1, 1)
        app.recorder._audio_callback(audio_chunk, len(sample_audio), None, None)

        # Toggle OFF
        app._on_toggle()
        assert not app.recorder.is_recording
        assert not app._toggle_active

        mock_bridge.transcribe.assert_called_once()
        mock_clip.copy.assert_called_once_with("Texto transcrito com sucesso.")

    @patch("src.recorder.sd.InputStream")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_push_to_talk_no_audio(self, mock_clip, mock_ctrl, mock_stream):
        """Push-to-talk sem falar nada — nenhuma saida."""
        app, mock_bridge = self._make_app()

        app._on_push_to_talk_press()
        # Release imediato sem audio no buffer
        app._on_push_to_talk_release()

        mock_bridge.transcribe.assert_not_called()
        mock_clip.copy.assert_not_called()

    @patch("src.recorder.sd.InputStream")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_whisper_returns_empty(self, mock_clip, mock_ctrl, mock_stream, sample_audio):
        """Motor retorna vazio — nenhuma saida."""
        app, mock_bridge = self._make_app()
        mock_bridge.transcribe.return_value = "  "

        app._on_push_to_talk_press()
        audio_chunk = sample_audio.reshape(-1, 1)
        app.recorder._audio_callback(audio_chunk, len(sample_audio), None, None)
        app._on_push_to_talk_release()

        mock_clip.copy.assert_not_called()

    @patch("src.recorder.sd.InputStream")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_multiple_recordings(self, mock_clip, mock_ctrl, mock_stream, sample_audio):
        """Duas gravacoes sequenciais — cada uma gera saida independente."""
        app, mock_bridge = self._make_app()
        mock_bridge.transcribe.side_effect = [
            "Primeira frase.",
            "Segunda frase.",
        ]

        audio_chunk = sample_audio.reshape(-1, 1)

        # Primeira gravacao
        app._on_push_to_talk_press()
        app.recorder._audio_callback(audio_chunk, len(sample_audio), None, None)
        app._on_push_to_talk_release()

        # Segunda gravacao
        app._on_push_to_talk_press()
        app.recorder._audio_callback(audio_chunk, len(sample_audio), None, None)
        app._on_push_to_talk_release()

        assert mock_bridge.transcribe.call_count == 2
        assert mock_clip.copy.call_args_list == [
            call("Primeira frase."),
            call("Segunda frase."),
        ]
