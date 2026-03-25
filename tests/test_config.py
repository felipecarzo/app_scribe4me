"""Testes para config.py."""

from src.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.model == "large"
    assert cfg.language == "pt"
    assert cfg.device == "cuda"
    assert cfg.output_mode == "cursor"
    assert cfg.sample_rate == 16000
    assert cfg.channels == 1
    assert cfg.hotkey_push_to_talk == "<ctrl>+<alt>+h"
    assert cfg.hotkey_toggle == "<ctrl>+<alt>+t"


def test_config_override():
    cfg = Config(model="tiny", device="cpu", output_mode="clipboard")
    assert cfg.model == "tiny"
    assert cfg.device == "cpu"
    assert cfg.output_mode == "clipboard"
