"""Testes para transcriber.py (faster-whisper)."""

from unittest.mock import patch, MagicMock

import numpy as np

from src.transcriber import Transcriber


def _mock_segments(text: str):
    """Cria mock de segmentos retornados pelo faster-whisper."""
    if not text.strip():
        return iter([])
    seg = MagicMock()
    seg.text = text
    return iter([seg])


class TestTranscriber:
    def test_initial_state(self, config):
        t = Transcriber(config)
        assert not t.is_loaded

    @patch("src.transcriber.WhisperModel")
    def test_load_model(self, mock_cls, config):
        t = Transcriber(config)
        t.load_model()
        assert t.is_loaded
        mock_cls.assert_called_once_with(
            config.model, device=config.device, compute_type="int8", cpu_threads=4,
        )

    @patch("src.transcriber.WhisperModel")
    def test_load_model_idempotent(self, mock_cls, config):
        t = Transcriber(config)
        t.load_model()
        t.load_model()
        assert mock_cls.call_count == 1

    @patch("src.transcriber.WhisperModel")
    def test_transcribe_short_audio_returns_empty(self, mock_cls, config, short_audio):
        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(short_audio)
        assert result == ""
        mock_cls.return_value.transcribe.assert_not_called()

    @patch("src.transcriber.WhisperModel")
    def test_transcribe_returns_text(self, mock_cls, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (_mock_segments("  Ola mundo.  "), None)
        mock_cls.return_value = mock_model

        t = Transcriber(config)
        t.load_model()
        result = t.transcribe(sample_audio)

        assert result == "Ola mundo."
        mock_model.transcribe.assert_called_once()

    @patch("src.transcriber.WhisperModel")
    def test_transcribe_auto_loads_model(self, mock_cls, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (_mock_segments("teste"), None)
        mock_cls.return_value = mock_model

        t = Transcriber(config)
        result = t.transcribe(sample_audio)

        assert result == "Teste"  # postprocess capitaliza primeira letra
        mock_cls.assert_called_once()

    @patch("src.transcriber.WhisperModel")
    def test_warm_up_runs_dummy_transcription(self, mock_cls, config):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (_mock_segments(""), None)
        mock_cls.return_value = mock_model

        t = Transcriber(config)
        t.warm_up()

        assert t.is_loaded
        mock_model.transcribe.assert_called_once()
        call_args = mock_model.transcribe.call_args
        audio_arg = call_args[0][0]
        assert len(audio_arg) == config.sample_rate

    @patch("src.transcriber.WhisperModel")
    def test_transcribe_uses_greedy_decoding(self, mock_cls, config, sample_audio):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (_mock_segments("teste"), None)
        mock_cls.return_value = mock_model

        t = Transcriber(config)
        t.load_model()
        t.transcribe(sample_audio)

        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["beam_size"] == 1
        assert call_kwargs["condition_on_previous_text"] is False
        assert call_kwargs["no_speech_threshold"] == 0.6
