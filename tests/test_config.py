"""Testes para config.py."""

from src.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.model == "large-v3"
    assert cfg.language == "pt"
    assert cfg.device == "cuda"
    assert cfg.output_mode == "cursor"
    assert cfg.sample_rate == 16000
    assert cfg.channels == 1
    assert cfg.beam_size == 1
    assert cfg.best_of == 3
    assert cfg.hotkey_push_to_talk == "<ctrl>+<alt>+h"
    assert cfg.hotkey_toggle == "<ctrl>+<alt>+t"


def test_config_override():
    cfg = Config(model="tiny", device="cpu", output_mode="clipboard")
    assert cfg.model == "tiny"
    assert cfg.device == "cpu"
    assert cfg.output_mode == "clipboard"


def test_config_active_profile_name_default():
    cfg = Config()
    assert cfg.active_profile_name == "Tech-Dev"


def test_config_active_profile_name_override():
    cfg = Config(active_profile_name="Geral")
    assert cfg.active_profile_name == "Geral"


def test_config_no_motor_dll_path():
    """motor_dll_path removido na versao publica."""
    cfg = Config()
    assert not hasattr(cfg, "motor_dll_path")


def test_config_no_mode():
    """AppMode removido na versao publica (STT only)."""
    cfg = Config()
    assert not hasattr(cfg, "mode")
    assert not hasattr(cfg, "target_language")
