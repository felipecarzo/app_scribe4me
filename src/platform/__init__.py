"""Deteccao automatica de plataforma e export do backend correto.

Uso:
    from src.platform import platform

    data_dir = platform.config_dir("Scribe4me")
    ram = platform.get_ram_mb()
"""

import sys

if sys.platform == "win32":
    from src.platform._windows import WindowsBackend as _Backend
elif sys.platform == "darwin":
    from src.platform._macos import MacOSBackend as _Backend
else:
    from src.platform._linux import LinuxBackend as _Backend

platform = _Backend()
