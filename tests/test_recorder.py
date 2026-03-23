"""Testes para recorder.py."""

from unittest.mock import patch, MagicMock

import numpy as np

from src.recorder import Recorder


class TestRecorder:
    def test_initial_state(self, config):
        rec = Recorder(config)
        assert not rec.is_recording

    def test_stop_without_start_returns_empty(self, config):
        rec = Recorder(config)
        audio = rec.stop()
        assert len(audio) == 0
        assert audio.dtype == np.float32

    @patch("src.recorder.sd.InputStream")
    def test_start_creates_stream(self, mock_stream_cls, config):
        rec = Recorder(config)
        rec.start()
        assert rec.is_recording
        mock_stream_cls.assert_called_once()
        mock_stream_cls.return_value.start.assert_called_once()

    @patch("src.recorder.sd.InputStream")
    def test_start_twice_is_noop(self, mock_stream_cls, config):
        rec = Recorder(config)
        rec.start()
        rec.start()
        assert mock_stream_cls.call_count == 1

    @patch("src.recorder.sd.InputStream")
    def test_stop_returns_concatenated_audio(self, mock_stream_cls, config):
        rec = Recorder(config)
        rec.start()

        # Simula audio callback com dois chunks
        chunk1 = np.ones((1600, 1), dtype=np.float32) * 0.5
        chunk2 = np.ones((1600, 1), dtype=np.float32) * -0.3
        rec._audio_callback(chunk1, 1600, None, None)
        rec._audio_callback(chunk2, 1600, None, None)

        audio = rec.stop()
        assert not rec.is_recording
        assert len(audio) == 3200
        assert audio.dtype == np.float32

    @patch("src.recorder.sd.InputStream")
    def test_stop_clears_buffer(self, mock_stream_cls, config):
        rec = Recorder(config)
        rec.start()
        rec._audio_callback(np.ones((800, 1), dtype=np.float32), 800, None, None)
        rec.stop()

        # Segunda gravacao deve comecar com buffer limpo
        rec.start()
        audio = rec.stop()
        assert len(audio) == 0
