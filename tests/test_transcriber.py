"""Testes para transcriber.py."""

from unittest.mock import patch, MagicMock

import numpy as np

from src.transcriber import Transcriber


class TestTranscriber:
    def test_initial_state(self, config):
        t = Transcriber(config)
        assert not t.is_loaded

    @patch("src.transcriber.whisper.load_model")
    def test_load_model(self, mock_load, config):
        t = Transcriber(config)
        t.load_model()
        assert t.is_loaded
        mock_load.assert_called_once_with(config.model, device=config.device)

    @patch("src.transcriber.whisper.load_model")
    def test_load_model_idempotent(self, mock_load, config):
        t = Transcriber(config)
        t.load_model()
        t.load_model()
        assert mock_load.call_count == 1

    @patch("src.transcriber.whisper.load_model")
    def test_transcribe_short_audio_returns_empty(self, mock_load, config, short_audio):
        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(short_audio)
        assert result == ""
        mock_load.return_value.transcribe.assert_not_called()

    @patch("src.transcriber.whisper.load_model")
    def test_transcribe_returns_text(self, mock_load, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "  Ola mundo.  "}
        mock_load.return_value = mock_model

        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(sample_audio)

        assert result == "Ola mundo."
        mock_model.transcribe.assert_called_once()

    @patch("src.transcriber.whisper.load_model")
    def test_transcribe_auto_loads_model(self, mock_load, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "teste"}
        mock_load.return_value = mock_model

        t = Transcriber(config)
        # Nao chama load_model() explicitamente
        result = t.transcribe(sample_audio)

        assert result == "teste"
        mock_load.assert_called_once()

    @patch("src.transcriber.whisper.load_model")
    def test_warm_up_runs_dummy_transcription(self, mock_load, config):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": ""}
        mock_load.return_value = mock_model

        t = Transcriber(config)
        t.warm_up()

        assert t.is_loaded
        mock_model.transcribe.assert_called_once()
        # Verifica que o audio dummy tem 1s de duracao
        call_args = mock_model.transcribe.call_args
        audio_arg = call_args[0][0]
        assert len(audio_arg) == config.sample_rate

    @patch("src.transcriber.whisper.load_model")
    def test_transcribe_uses_greedy_decoding(self, mock_load, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "teste"}
        mock_load.return_value = mock_model

        t = Transcriber(config)
        t.load_model()
        t.transcribe(sample_audio)

        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["beam_size"] == 1
        assert call_kwargs["condition_on_previous_text"] is False
        assert call_kwargs["no_speech_threshold"] == 0.6
