"""Testes para transcriber.py (Motor Ayvu via ctypes FFI)."""

from unittest.mock import patch, MagicMock

import numpy as np

from src.transcriber import Transcriber


class TestTranscriber:
    def test_initial_state(self, config):
        t = Transcriber(config)
        assert not t.is_loaded

    @patch("src.transcriber.MotorBridge")
    def test_load_model(self, mock_cls, config):
        t = Transcriber(config)
        t.load_model()
        assert t.is_loaded
        mock_cls.assert_called_once()

    @patch("src.transcriber.MotorBridge")
    def test_load_model_idempotent(self, mock_cls, config):
        t = Transcriber(config)
        t.load_model()
        t.load_model()
        assert mock_cls.call_count == 1

    @patch("src.transcriber.MotorBridge")
    def test_transcribe_short_audio_returns_empty(self, mock_cls, config, short_audio):
        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(short_audio)
        assert result == ""
        mock_cls.return_value.transcribe.assert_not_called()

    @patch("src.transcriber.MotorBridge")
    def test_transcribe_returns_text(self, mock_cls, config, sample_audio):
        mock_bridge = MagicMock()
        mock_bridge.transcribe.return_value = "  Ola mundo.  "
        mock_cls.return_value = mock_bridge

        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(sample_audio)

        assert result == "Ola mundo."
        mock_bridge.transcribe.assert_called_once()

    @patch("src.transcriber.MotorBridge")
    def test_transcribe_auto_loads_model(self, mock_cls, config, sample_audio):
        mock_bridge = MagicMock()
        mock_bridge.transcribe.return_value = "teste"
        mock_cls.return_value = mock_bridge

        t = Transcriber(config)
        result = t.transcribe(sample_audio)

        assert result == "Teste"  # postprocess capitaliza primeira letra
        mock_cls.assert_called_once()

    @patch("src.transcriber.MotorBridge")
    def test_warm_up_runs_dummy_transcription(self, mock_cls, config):
        mock_bridge = MagicMock()
        mock_bridge.transcribe.return_value = ""
        mock_cls.return_value = mock_bridge

        t = Transcriber(config)
        t.warm_up()

        assert t.is_loaded
        mock_bridge.transcribe.assert_called_once()
        call_args = mock_bridge.transcribe.call_args
        audio_arg = call_args[0][0]
        assert len(audio_arg) == config.sample_rate
