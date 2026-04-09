"""Backends de transcricao via API externa (OpenAI, Groq, Gemini, Deepgram)."""

import base64
import io
import logging
import time

import httpx
import numpy as np
import soundfile as sf

from src.postprocess import postprocess

logger = logging.getLogger("scribe4me")

# Tempo minimo de audio para enviar a API (evita chamadas com silencio)
_MIN_DURATION_SEC = 0.3


def _audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Converte array float32 (mono, 16kHz) para bytes WAV em memoria."""
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


class OpenAITranscriber:
    """Transcricao via OpenAI Whisper API (/v1/audio/transcriptions)."""

    _URL = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(self, api_key: str, language: str = "pt"):
        self._api_key = api_key
        self._language = language[:2]  # "pt-BR" -> "pt"

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if len(audio) < sample_rate * _MIN_DURATION_SEC:
            return ""
        wav = _audio_to_wav_bytes(audio, sample_rate)
        t0 = time.perf_counter()
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                self._URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.wav", wav, "audio/wav")},
                data={"model": "whisper-1", "language": self._language},
            )
        resp.raise_for_status()
        text = postprocess(resp.json().get("text", "").strip())
        logger.info("OpenAI transcribed in %.2fs", time.perf_counter() - t0)
        return text


class GroqTranscriber:
    """Transcricao via Groq (Whisper large-v3) — mesma API do OpenAI."""

    _URL = "https://api.groq.com/openai/v1/audio/transcriptions"

    def __init__(self, api_key: str, language: str = "pt"):
        self._api_key = api_key
        self._language = language[:2]

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if len(audio) < sample_rate * _MIN_DURATION_SEC:
            return ""
        wav = _audio_to_wav_bytes(audio, sample_rate)
        t0 = time.perf_counter()
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                self._URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.wav", wav, "audio/wav")},
                data={
                    "model": "whisper-large-v3",
                    "language": self._language,
                    "response_format": "json",
                },
            )
        resp.raise_for_status()
        text = postprocess(resp.json().get("text", "").strip())
        logger.info("Groq transcribed in %.2fs", time.perf_counter() - t0)
        return text


class GeminiTranscriber:
    """Transcricao via Gemini (audio inline, modelo flash)."""

    _URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    _PROMPT = (
        "Transcreva fielmente o audio a seguir em portugues brasileiro. "
        "Retorne apenas o texto transcrito, sem comentarios, sem aspas, "
        "sem explicacoes adicionais."
    )

    def __init__(self, api_key: str, language: str = "pt"):
        self._api_key = api_key

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if len(audio) < sample_rate * _MIN_DURATION_SEC:
            return ""
        wav = _audio_to_wav_bytes(audio, sample_rate)
        b64 = base64.b64encode(wav).decode()
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self._PROMPT},
                        {"inline_data": {"mime_type": "audio/wav", "data": b64}},
                    ]
                }
            ]
        }
        t0 = time.perf_counter()
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                self._URL,
                params={"key": self._api_key},
                json=payload,
            )
        resp.raise_for_status()
        candidates = resp.json().get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        raw = " ".join(p.get("text", "") for p in parts).strip()
        text = postprocess(raw)
        logger.info("Gemini transcribed in %.2fs", time.perf_counter() - t0)
        return text


class DeepgramBatchTranscriber:
    """Transcricao via Deepgram (Nova-3, batch REST)."""

    _URL = "https://api.deepgram.com/v1/listen"

    def __init__(self, api_key: str, language: str = "pt-BR"):
        self._api_key = api_key
        self._language = language

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if len(audio) < sample_rate * _MIN_DURATION_SEC:
            return ""
        wav = _audio_to_wav_bytes(audio, sample_rate)
        params = {
            "model": "nova-2",
            "language": self._language,
            "punctuate": "true",
            "smart_format": "true",
        }
        t0 = time.perf_counter()
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                self._URL,
                headers={
                    "Authorization": f"Token {self._api_key}",
                    "Content-Type": "audio/wav",
                },
                params=params,
                content=wav,
            )
        resp.raise_for_status()
        channels = resp.json().get("results", {}).get("channels", [])
        if not channels:
            return ""
        alts = channels[0].get("alternatives", [])
        raw = alts[0].get("transcript", "").strip() if alts else ""
        text = postprocess(raw)
        logger.info("Deepgram batch transcribed in %.2fs", time.perf_counter() - t0)
        return text


def create_api_transcriber(backend: str, api_keys: dict[str, str], language: str = "pt"):
    """Factory — retorna o transcriber correto para o backend solicitado.

    Retorna None se o backend for 'local' ou se a key estiver ausente.
    """
    if backend == "local":
        return None

    key = api_keys.get(backend, "").strip()
    if not key:
        logger.warning("Backend '%s' selecionado mas API key nao configurada.", backend)
        return None

    if backend == "openai":
        return OpenAITranscriber(key, language)
    if backend == "groq":
        return GroqTranscriber(key, language)
    if backend == "gemini":
        return GeminiTranscriber(key, language)
    if backend == "deepgram":
        lang = "pt-BR" if language.startswith("pt") else language
        return DeepgramBatchTranscriber(key, lang)

    logger.warning("Backend desconhecido: '%s'", backend)
    return None
