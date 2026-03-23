"""Testes para clipboard.py (OutputHandler)."""

from unittest.mock import patch, MagicMock

from src.clipboard import OutputHandler


class TestOutputHandler:
    @patch("src.clipboard.Controller")
    def test_send_empty_is_noop(self, mock_ctrl, config):
        handler = OutputHandler(config)
        with patch("src.clipboard.pyperclip") as mock_clip:
            handler.send("")
            mock_clip.copy.assert_not_called()

    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_clipboard_mode(self, mock_clip, mock_ctrl, config):
        config.output_mode = "clipboard"
        handler = OutputHandler(config)
        handler.send("Ola mundo")
        mock_clip.copy.assert_called_once_with("Ola mundo")

    @patch("src.clipboard.time.sleep")
    @patch("src.clipboard.Controller")
    @patch("src.clipboard.pyperclip")
    def test_cursor_mode_copies_and_pastes(self, mock_clip, mock_ctrl_cls, mock_sleep, config):
        config.output_mode = "cursor"
        handler = OutputHandler(config)
        handler.send("Texto teste")

        mock_clip.copy.assert_called_once_with("Texto teste")
        # Verifica que Ctrl+V foi simulado
        kb = mock_ctrl_cls.return_value
        assert kb.press.call_count == 2  # ctrl + v
        assert kb.release.call_count == 2
