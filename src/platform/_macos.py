"""Backend de plataforma para macOS."""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class MacOSBackend:
    """Implementacao macOS das operacoes de plataforma."""

    def config_dir(self, app_name: str) -> Path:
        """~/Library/Application Support/<app_name>/"""
        return Path.home() / "Library" / "Application Support" / app_name

    def get_ram_mb(self) -> int:
        """RAM via sysctl hw.memsize."""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return int(result.stdout.strip()) // (1024 * 1024)
        except Exception:
            pass
        return 8192

    def acquire_single_instance(self, app_name: str) -> Any:
        """File lock via fcntl.flock (mesmo mecanismo do Linux)."""
        lock_path = Path(f"/tmp/.{app_name.lower()}.lock")
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"{app_name} ja esta rodando. Encerrando.", file=sys.stderr)
            sys.exit(1)
        return lock_file

    def show_error_dialog(self, title: str, message: str) -> None:
        """Dialog via osascript (nativo macOS)."""
        try:
            script = f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon stop'
            subprocess.run(["osascript", "-e", script], timeout=30)
            return
        except Exception:
            pass
        print(f"{title}: {message}", file=sys.stderr)

    def open_path(self, path: Path) -> None:
        """open — abre com o programa padrao do macOS."""
        subprocess.Popen(["open", str(path)])
