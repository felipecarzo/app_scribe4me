"""Testes para gui.py (QueueLogHandler + SpeedOsperGUI logica sem tkinter)."""

import logging
import queue
from unittest.mock import MagicMock, patch

import pytest

from src.gui import QueueLogHandler, SpeedOsperGUI


# --- QueueLogHandler ---

class TestQueueLogHandler:
    def test_emit_puts_formatted_message(self):
        q = queue.Queue(maxsize=10)
        handler = QueueLogHandler(q)
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        handler.emit(record)
        assert q.get_nowait() == "hello world"

    def test_emit_uses_formatter(self):
        q = queue.Queue(maxsize=10)
        handler = QueueLogHandler(q)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="cuidado", args=(), exc_info=None,
        )
        handler.emit(record)
        assert q.get_nowait() == "[WARNING] cuidado"

    def test_emit_does_not_block_when_queue_full(self):
        q = queue.Queue(maxsize=1)
        handler = QueueLogHandler(q)
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Enche a queue
        record1 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="first", args=(), exc_info=None,
        )
        handler.emit(record1)
        assert q.full()

        # Segundo emit nao deve bloquear — silenciosamente descartado
        record2 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="second", args=(), exc_info=None,
        )
        handler.emit(record2)  # nao levanta excecao

        # Apenas a primeira mensagem esta na queue
        assert q.get_nowait() == "first"
        assert q.empty()

    def test_emit_multiple_messages(self):
        q = queue.Queue(maxsize=100)
        handler = QueueLogHandler(q)
        handler.setFormatter(logging.Formatter("%(message)s"))

        for i in range(10):
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg=f"msg-{i}", args=(), exc_info=None,
            )
            handler.emit(record)

        messages = []
        while not q.empty():
            messages.append(q.get_nowait())
        assert messages == [f"msg-{i}" for i in range(10)]


# --- SpeedOsperGUI (logica sem tkinter) ---

class TestSpeedOsperGUIInit:
    """Testa construtor e atributos iniciais — sem start(), sem tkinter."""

    def _make_gui(self, **kwargs):
        q = queue.Queue(maxsize=100)
        defaults = dict(
            log_queue=q,
            profile_names=["A", "B"],
            mode_names=["scribe", "translate"],
            model_names=["large-v3", "medium"],
            current_profile="A",
            current_mode="scribe",
            current_model="large-v3",
        )
        defaults.update(kwargs)
        return SpeedOsperGUI(**defaults)

    def test_defaults(self):
        gui = self._make_gui()
        assert gui._current_profile == "A"
        assert gui._current_mode == "scribe"
        assert gui._current_model == "large-v3"
        assert gui._current_state == "Idle"
        assert gui._visible is False
        assert gui._root is None

    def test_callbacks_stored(self):
        cb_record = MagicMock()
        cb_profile = MagicMock()
        cb_mode = MagicMock()
        cb_model = MagicMock()
        gui = self._make_gui(
            on_record_toggle=cb_record,
            on_profile_change=cb_profile,
            on_mode_change=cb_mode,
            on_model_change=cb_model,
        )
        assert gui._on_record_toggle is cb_record
        assert gui._on_profile_change is cb_profile
        assert gui._on_mode_change is cb_mode
        assert gui._on_model_change is cb_model

    def test_default_lists_when_none(self):
        q = queue.Queue(maxsize=10)
        gui = SpeedOsperGUI(log_queue=q)
        assert gui._profile_names == ["Tech-Dev"]
        assert gui._mode_names == ["scribe", "translate", "voice"]
        assert gui._model_names == ["large-v3"]


class TestSpeedOsperGUINoRoot:
    """Testa metodos publicos quando _root e None (GUI nao iniciado)."""

    def _make_gui(self):
        q = queue.Queue(maxsize=100)
        return SpeedOsperGUI(log_queue=q)

    def test_update_state_without_root(self):
        gui = self._make_gui()
        gui.update_state("Gravando")
        assert gui._current_state == "Gravando"

    def test_update_profile_without_root(self):
        gui = self._make_gui()
        gui.update_profile("MyProfile")
        assert gui._current_profile == "MyProfile"

    def test_update_mode_without_root(self):
        gui = self._make_gui()
        gui.update_mode("translate")
        assert gui._current_mode == "translate"

    def test_update_model_without_root(self):
        gui = self._make_gui()
        gui.update_model("medium")
        assert gui._current_model == "medium"

    def test_update_profile_list_without_root(self):
        gui = self._make_gui()
        gui.update_profile_list(["X", "Y", "Z"])
        assert gui._profile_names == ["X", "Y", "Z"]

    def test_show_hide_toggle_without_root(self):
        """show/hide/toggle com root=None nao levanta excecao."""
        gui = self._make_gui()
        gui.show()
        gui.hide()
        gui.toggle()

    def test_stop_without_root(self):
        """stop com root=None nao levanta excecao."""
        gui = self._make_gui()
        gui.stop()

    def test_is_visible_default(self):
        gui = self._make_gui()
        assert gui.is_visible is False

    def test_toggle_calls_show_when_hidden(self):
        gui = self._make_gui()
        gui._visible = False
        gui.show = MagicMock()
        gui.hide = MagicMock()
        gui.toggle()
        gui.show.assert_called_once()
        gui.hide.assert_not_called()

    def test_toggle_calls_hide_when_visible(self):
        gui = self._make_gui()
        gui._visible = True
        gui.show = MagicMock()
        gui.hide = MagicMock()
        gui.toggle()
        gui.hide.assert_called_once()
        gui.show.assert_not_called()


class TestSpeedOsperGUICallbacks:
    """Testa callbacks internos sem tkinter."""

    def _make_gui(self, **kwargs):
        q = queue.Queue(maxsize=100)
        return SpeedOsperGUI(log_queue=q, **kwargs)

    def test_on_record_click_fires_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_record_toggle=cb)
        gui._on_record_click()
        cb.assert_called_once()

    def test_on_record_click_no_callback(self):
        """Sem callback configurado nao levanta excecao."""
        gui = self._make_gui()
        gui._on_record_click()

    def test_on_profile_select_fires_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_profile_change=cb)
        gui._var_profile = MagicMock()
        gui._var_profile.get.return_value = "MyProfile"
        gui._on_profile_select(None)
        cb.assert_called_once_with("MyProfile")

    def test_on_mode_select_fires_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_mode_change=cb)
        gui._var_mode = MagicMock()
        gui._var_mode.get.return_value = "translate"
        gui._on_mode_select(None)
        cb.assert_called_once_with("translate")

    def test_on_model_select_fires_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_model_change=cb)
        gui._var_model = MagicMock()
        gui._var_model.get.return_value = "medium"
        gui._on_model_select(None)
        cb.assert_called_once_with("medium")

    def test_on_profile_select_empty_value_no_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_profile_change=cb)
        gui._var_profile = MagicMock()
        gui._var_profile.get.return_value = ""
        gui._on_profile_select(None)
        cb.assert_not_called()

    def test_on_mode_select_empty_value_no_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_mode_change=cb)
        gui._var_mode = MagicMock()
        gui._var_mode.get.return_value = ""
        gui._on_mode_select(None)
        cb.assert_not_called()

    def test_on_model_select_empty_value_no_callback(self):
        cb = MagicMock()
        gui = self._make_gui(on_model_change=cb)
        gui._var_model = MagicMock()
        gui._var_model.get.return_value = ""
        gui._on_model_select(None)
        cb.assert_not_called()
