"""Testes para config.py."""

from src.config import Config, AppMode, SUPPORTED_LANGUAGES


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
    assert cfg.mode == AppMode.SCRIBE
    assert cfg.target_language == "en"


def test_config_override():
    cfg = Config(model="tiny", device="cpu", output_mode="clipboard")
    assert cfg.model == "tiny"
    assert cfg.device == "cpu"
    assert cfg.output_mode == "clipboard"


def test_app_mode_enum():
    assert AppMode.SCRIBE.value == "scribe"
    assert AppMode.TRANSLATE.value == "translate"
    assert AppMode.VOICE.value == "voice"
    assert AppMode("translate") == AppMode.TRANSLATE


def test_supported_languages():
    assert "pt" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert len(SUPPORTED_LANGUAGES) >= 5


def test_config_mode_override():
    cfg = Config(mode=AppMode.TRANSLATE, target_language="es")
    assert cfg.mode == AppMode.TRANSLATE
    assert cfg.target_language == "es"
