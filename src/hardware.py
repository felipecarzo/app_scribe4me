"""Deteccao de hardware e recomendacao de modelo Whisper."""

import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger("scribe4me.hardware")

# Modelos Whisper: nome, tamanho do download, VRAM minima recomendada (MB), RAM minima (MB)
WHISPER_MODELS = {
    "tiny":   {"size": "~39 MB",   "vram_mb": 0,    "ram_mb": 2048,  "desc": "Ultra rapido, qualidade basica"},
    "base":   {"size": "~74 MB",   "vram_mb": 0,    "ram_mb": 2048,  "desc": "Rapido, qualidade razoavel"},
    "small":  {"size": "~244 MB",  "vram_mb": 2048,  "ram_mb": 4096,  "desc": "Equilibrado velocidade/qualidade"},
    "medium": {"size": "~769 MB",  "vram_mb": 4096,  "ram_mb": 8192,  "desc": "Boa qualidade, mais lento"},
    "large":  {"size": "~1.5 GB",  "vram_mb": 6144,  "ram_mb": 16384, "desc": "Melhor qualidade, requer GPU forte"},
}


@dataclass
class HardwareInfo:
    gpu_name: str | None = None
    gpu_vram_mb: int = 0
    cuda_available: bool = False
    ram_mb: int = 0
    cpu_cores: int = 0


def _detect_gpu_nvidia_smi() -> tuple[str | None, int]:
    """Detecta GPU via nvidia-smi (sem depender de torch)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            name, vram_str = line.split(",", 1)
            return name.strip(), int(vram_str.strip())
    except Exception:
        pass
    return None, 0


def _detect_cuda_available() -> bool:
    """Verifica se CUDA esta disponivel via ctranslate2."""
    try:
        import ctranslate2
        return "cuda" in ctranslate2.get_supported_compute_types("cuda")
    except Exception:
        return False


def detect_hardware() -> HardwareInfo:
    """Detecta GPU, VRAM, RAM e CPU do sistema."""
    info = HardwareInfo()
    info.cpu_cores = os.cpu_count() or 1

    # RAM total via ctypes (Windows)
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        info.ram_mb = int(stat.ullTotalPhys / (1024 * 1024))
    except Exception:
        info.ram_mb = 8192  # fallback

    # GPU via nvidia-smi
    gpu_name, gpu_vram = _detect_gpu_nvidia_smi()
    if gpu_name:
        info.gpu_name = gpu_name
        info.gpu_vram_mb = gpu_vram
        info.cuda_available = _detect_cuda_available()

    logger.info(
        "Hardware: GPU=%s (%d MB VRAM, CUDA=%s), RAM=%d MB, CPU=%d cores",
        info.gpu_name or "nenhuma", info.gpu_vram_mb,
        info.cuda_available, info.ram_mb, info.cpu_cores,
    )
    return info


def recommend_model(hw: HardwareInfo) -> str:
    """Recomenda o melhor modelo Whisper para o hardware detectado."""
    if hw.cuda_available and hw.gpu_vram_mb >= 6144:
        return "large"
    if hw.cuda_available and hw.gpu_vram_mb >= 4096:
        return "medium"
    if hw.cuda_available and hw.gpu_vram_mb >= 2048:
        return "small"
    if hw.ram_mb >= 8192:
        return "medium"
    if hw.ram_mb >= 4096:
        return "small"
    if hw.ram_mb >= 2048:
        return "base"
    return "tiny"


def model_label(name: str, recommended: str) -> str:
    """Gera label para o menu de selecao de modelo."""
    info = WHISPER_MODELS.get(name, {})
    label = f"{name.capitalize()}  ({info.get('size', '?')}) — {info.get('desc', '')}"
    if name == recommended:
        label += "  [RECOMENDADO]"
    return label
