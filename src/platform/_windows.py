"""Backend de plataforma para Windows."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Any


class WindowsBackend:
    """Implementacao Windows das operacoes de plataforma."""

    def config_dir(self, app_name: str) -> Path:
        """%LOCALAPPDATA%/<app_name>/"""
        return Path(os.environ.get("LOCALAPPDATA", ".")) / app_name

    def get_ram_mb(self) -> int:
        """RAM via kernel32.GlobalMemoryStatusEx."""
        try:
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
            return int(stat.ullTotalPhys / (1024 * 1024))
        except Exception:
            return 8192

    def acquire_single_instance(self, app_name: str) -> Any:
        """Mutex via kernel32.CreateMutexW."""
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, f"{app_name}_SingleInstance")
        last_error = ctypes.windll.kernel32.GetLastError()
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            print(f"{app_name} ja esta rodando. Encerrando.", file=sys.stderr)
            sys.exit(1)
        return mutex

    def show_error_dialog(self, title: str, message: str) -> None:
        """MessageBoxW via user32."""
        try:
            ctypes.windll.user32.MessageBoxW(
                0, message, title, 0x10,  # MB_ICONERROR
            )
        except Exception:
            pass

    def open_path(self, path: Path) -> None:
        """os.startfile (Windows nativo)."""
        os.startfile(str(path))
