"""Testes para tray.py (TrayIcon)."""

from unittest.mock import patch, MagicMock

from src.tray import TrayIcon, AppState, _create_icon_image, _COLORS


class TestTrayIcon:
    def test_create_icon_image_returns_rgba(self):
        img = _create_icon_image("#FF0000", size=32)
        assert img.size == (32, 32)
        assert img.mode == "RGBA"

    def test_all_states_have_colors_and_tooltips(self):
        from src.tray import _TOOLTIPS
        for state in AppState:
            assert state in _COLORS
            assert state in _TOOLTIPS

    @patch("src.tray.pystray.Icon")
    def test_start_creates_icon(self, mock_icon_cls):
        tray = TrayIcon()
        tray.start()
        mock_icon_cls.assert_called_once()

    @patch("src.tray.pystray.Icon")
    def test_set_state_updates_icon(self, mock_icon_cls):
        tray = TrayIcon()
        tray.start()
        icon_instance = mock_icon_cls.return_value

        tray.set_state(AppState.RECORDING)
        assert icon_instance.icon is not None
        assert "Gravando" in icon_instance.title

        tray.set_state(AppState.TRANSCRIBING)
        assert "Transcrevendo" in icon_instance.title

        tray.set_state(AppState.IDLE)
        assert "Pronto" in icon_instance.title

    @patch("src.tray.pystray.Icon")
    def test_stop(self, mock_icon_cls):
        tray = TrayIcon()
        tray.start()
        tray.stop()
        mock_icon_cls.return_value.stop.assert_called_once()

    @patch("src.tray.pystray.Icon")
    def test_quit_callback(self, mock_icon_cls):
        quit_called = []
        tray = TrayIcon(on_quit=lambda: quit_called.append(True))
        tray._quit_clicked(None, None)
        assert quit_called == [True]
