"""Fixtures compartilhadas para testes do scribe4me."""

import numpy as np
import pytest

from src.config import Config


@pytest.fixture
def config():
    """Config padrao para testes (modelo tiny para velocidade)."""
    return Config(model="tiny", device="cpu")


@pytest.fixture
def sample_audio():
    """Audio sintetico: 2 segundos de silencio a 16kHz (float32)."""
    return np.zeros(16000 * 2, dtype=np.float32)


@pytest.fixture
def short_audio():
    """Audio muito curto (abaixo do threshold de 0.3s)."""
    return np.zeros(100, dtype=np.float32)
