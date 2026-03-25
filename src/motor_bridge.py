"""Wrapper ctypes para motor_ayvu.dll (Motor Ayvu — Rust ONNX backend).

Expoe as funcoes C-ABI definidas em ffi.rs como metodos Python.
Audio: f32 mono 16kHz, normalizado em [-1.0, 1.0].
"""

import ctypes
import json
import logging
from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_float,
    c_size_t,
    c_uint32,
)
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger("speedosper")

# ── Structs C-ABI ────────────────────────────────────────────────────────────


class ScribeSynthResult(Structure):
    _fields_ = [
        ("samples", POINTER(c_float)),
        ("num_samples", c_size_t),
        ("sample_rate", c_uint32),
    ]


class ScribeVoiceResult(Structure):
    _fields_ = [
        ("samples", POINTER(c_float)),
        ("num_samples", c_size_t),
        ("sample_rate", c_uint32),
        ("source_text", c_char_p),
        ("translated_text", c_char_p),
        ("cache_hit", c_bool),
        ("quality_score", c_float),
    ]


class ScribeProsody(Structure):
    _fields_ = [
        ("pitch_hz", c_float),
        ("energy", c_float),
        ("zcr", c_float),
        ("duration_secs", c_float),
    ]


# ── Resultados Python ────────────────────────────────────────────────────────


class SynthResult:
    __slots__ = ("samples", "sample_rate")

    def __init__(self, samples: np.ndarray, sample_rate: int):
        self.samples = samples
        self.sample_rate = sample_rate


class TranslateResult:
    __slots__ = ("translation", "cache_hit", "quality_score")

    def __init__(self, translation: str, cache_hit: bool, quality_score: float):
        self.translation = translation
        self.cache_hit = cache_hit
        self.quality_score = quality_score


class VoiceResult:
    __slots__ = ("samples", "sample_rate", "source_text", "translated_text",
                 "cache_hit", "quality_score")

    def __init__(self, samples: np.ndarray, sample_rate: int,
                 source_text: str, translated_text: str,
                 cache_hit: bool, quality_score: float):
        self.samples = samples
        self.sample_rate = sample_rate
        self.source_text = source_text
        self.translated_text = translated_text
        self.cache_hit = cache_hit
        self.quality_score = quality_score


class ProsodyResult:
    __slots__ = ("pitch_hz", "energy", "zcr", "duration_secs")

    def __init__(self, pitch_hz: float, energy: float, zcr: float, duration_secs: float):
        self.pitch_hz = pitch_hz
        self.energy = energy
        self.zcr = zcr
        self.duration_secs = duration_secs


# ── Path da DLL ──────────────────────────────────────────────────────────────

# Ordem de busca:
# 1. Variavel de ambiente MOTOR_AYVU_DLL
# 2. Path padrao do build release
_DEFAULT_DLL_PATH = Path(r"D:\Documentos\Ti\projetos\app_ayvu\motor\target\release\motor.dll")


def _find_dll() -> Path:
    import os
    env = os.environ.get("MOTOR_AYVU_DLL")
    if env:
        p = Path(env)
        if p.exists():
            return p
        logger.warning("MOTOR_AYVU_DLL=%s nao encontrado, tentando path padrao.", env)
    if _DEFAULT_DLL_PATH.exists():
        return _DEFAULT_DLL_PATH
    raise FileNotFoundError(
        f"motor.dll nao encontrada. Defina MOTOR_AYVU_DLL ou compile o motor ayvu. "
        f"Tentou: {_DEFAULT_DLL_PATH}"
    )


# ── Bridge ───────────────────────────────────────────────────────────────────


class MotorBridge:
    """Interface Python para o Motor Ayvu via ctypes/FFI."""

    def __init__(self, dll_path: Optional[str | Path] = None):
        path = Path(dll_path) if dll_path else _find_dll()
        logger.info("Carregando motor ayvu: %s", path)
        self._dll = ctypes.CDLL(str(path))
        self._setup_signatures()
        logger.info("Motor ayvu carregado — versao %s", self.version())

    def _setup_signatures(self) -> None:
        dll = self._dll

        # scribe_motor_version() -> *mut c_char
        dll.scribe_motor_version.restype = c_char_p
        dll.scribe_motor_version.argtypes = []

        # scribe_transcribe(samples, num_samples, lang) -> *mut c_char
        dll.scribe_transcribe.restype = c_char_p
        dll.scribe_transcribe.argtypes = [POINTER(c_float), c_size_t, c_char_p]

        # scribe_translate(text, src_lang, tgt_lang) -> *mut c_char
        dll.scribe_translate.restype = c_char_p
        dll.scribe_translate.argtypes = [c_char_p, c_char_p, c_char_p]

        # scribe_synthesize(text, lang) -> *mut ScribeSynthResult
        dll.scribe_synthesize.restype = POINTER(ScribeSynthResult)
        dll.scribe_synthesize.argtypes = [c_char_p, c_char_p]

        # scribe_voice_translate(samples, num_samples, src_lang, tgt_lang) -> *mut ScribeVoiceResult
        dll.scribe_voice_translate.restype = POINTER(ScribeVoiceResult)
        dll.scribe_voice_translate.argtypes = [POINTER(c_float), c_size_t, c_char_p, c_char_p]

        # scribe_analyze_prosody(samples, num_samples) -> *mut ScribeProsody
        dll.scribe_analyze_prosody.restype = POINTER(ScribeProsody)
        dll.scribe_analyze_prosody.argtypes = [POINTER(c_float), c_size_t]

        # scribe_cache_stats() -> *mut c_char
        dll.scribe_cache_stats.restype = c_char_p
        dll.scribe_cache_stats.argtypes = []

        # Free functions
        dll.scribe_free_string.restype = None
        dll.scribe_free_string.argtypes = [c_char_p]

        dll.scribe_free_synth_result.restype = None
        dll.scribe_free_synth_result.argtypes = [POINTER(ScribeSynthResult)]

        dll.scribe_free_voice_result.restype = None
        dll.scribe_free_voice_result.argtypes = [POINTER(ScribeVoiceResult)]

        dll.scribe_free_prosody.restype = None
        dll.scribe_free_prosody.argtypes = [POINTER(ScribeProsody)]

    # ── API publica ──────────────────────────────────────────────────────────

    def version(self) -> str:
        result = self._dll.scribe_motor_version()
        if not result:
            return "(desconhecida)"
        return result.decode("utf-8")

    def transcribe(self, audio: np.ndarray, lang: Optional[str] = None) -> str:
        """Transcreve audio float32 mono 16kHz para texto."""
        audio = np.ascontiguousarray(audio, dtype=np.float32)
        samples_ptr = audio.ctypes.data_as(POINTER(c_float))
        lang_bytes = lang.encode("utf-8") if lang else None

        result = self._dll.scribe_transcribe(samples_ptr, len(audio), lang_bytes)
        if not result:
            return ""
        return result.decode("utf-8")

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> TranslateResult:
        """Traduz texto entre idiomas."""
        result = self._dll.scribe_translate(
            text.encode("utf-8"),
            src_lang.encode("utf-8"),
            tgt_lang.encode("utf-8"),
        )
        if not result:
            raise RuntimeError("Traducao falhou (motor retornou null)")
        data = json.loads(result.decode("utf-8"))
        return TranslateResult(
            translation=data["translation"],
            cache_hit=data["cache_hit"],
            quality_score=data["quality_score"],
        )

    def synthesize(self, text: str, lang: str) -> SynthResult:
        """Sintetiza texto para audio PCM f32."""
        ptr = self._dll.scribe_synthesize(
            text.encode("utf-8"),
            lang.encode("utf-8"),
        )
        if not ptr:
            raise RuntimeError("Sintese falhou (motor retornou null)")
        try:
            result = ptr.contents
            samples = np.ctypeslib.as_array(result.samples, shape=(result.num_samples,)).copy()
            return SynthResult(samples=samples, sample_rate=result.sample_rate)
        finally:
            self._dll.scribe_free_synth_result(ptr)

    def voice_translate(self, audio: np.ndarray, tgt_lang: str,
                        src_lang: Optional[str] = None) -> VoiceResult:
        """Pipeline completo: voz -> texto -> traducao -> TTS."""
        audio = np.ascontiguousarray(audio, dtype=np.float32)
        samples_ptr = audio.ctypes.data_as(POINTER(c_float))
        src_bytes = src_lang.encode("utf-8") if src_lang else None
        tgt_bytes = tgt_lang.encode("utf-8")

        ptr = self._dll.scribe_voice_translate(
            samples_ptr, len(audio), src_bytes, tgt_bytes,
        )
        if not ptr:
            raise RuntimeError("Voice translate falhou (motor retornou null)")
        try:
            r = ptr.contents
            samples = np.ctypeslib.as_array(r.samples, shape=(r.num_samples,)).copy()
            return VoiceResult(
                samples=samples,
                sample_rate=r.sample_rate,
                source_text=r.source_text.decode("utf-8") if r.source_text else "",
                translated_text=r.translated_text.decode("utf-8") if r.translated_text else "",
                cache_hit=r.cache_hit,
                quality_score=r.quality_score,
            )
        finally:
            self._dll.scribe_free_voice_result(ptr)

    def analyze_prosody(self, audio: np.ndarray) -> ProsodyResult:
        """Extrai features prosodicas do audio."""
        audio = np.ascontiguousarray(audio, dtype=np.float32)
        samples_ptr = audio.ctypes.data_as(POINTER(c_float))

        ptr = self._dll.scribe_analyze_prosody(samples_ptr, len(audio))
        if not ptr:
            raise RuntimeError("Analise de prosodia falhou (motor retornou null)")
        try:
            r = ptr.contents
            return ProsodyResult(
                pitch_hz=r.pitch_hz,
                energy=r.energy,
                zcr=r.zcr,
                duration_secs=r.duration_secs,
            )
        finally:
            self._dll.scribe_free_prosody(ptr)

    def cache_stats(self) -> dict:
        """Retorna estatisticas do cache de traducao."""
        result = self._dll.scribe_cache_stats()
        if not result:
            return {}
        return json.loads(result.decode("utf-8"))
