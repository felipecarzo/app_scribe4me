"""Backend de plataforma para Linux."""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class LinuxBackend:
    """Implementacao Linux das operacoes de plataforma."""

    def config_dir(self, app_name: str) -> Path:
        """$XDG_CONFIG_HOME/<app_name>/ ou ~/.config/<app_name>/"""
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / app_name

    def get_ram_mb(self) -> int:
        """RAM via /proc/meminfo."""
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Formato: "MemTotal:       16384000 kB"
                        kb = int(line.split()[1])
                        return kb // 1024
        except Exception:
            pass
        return 8192

    def acquire_single_instance(self, app_name: str) -> Any:
        """File lock via fcntl.flock."""
        lock_path = Path(f"/tmp/.{app_name.lower()}.lock")
        lock_file = open(lock_path, "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"{app_name} ja esta rodando. Encerrando.", file=sys.stderr)
            sys.exit(1)
        return lock_file

    def show_error_dialog(self, title: str, message: str) -> None:
        """Tenta zenity, depois xmessage, depois stderr."""
        for cmd in [
            ["zenity", "--error", "--title", title, "--text", message],
            ["xmessage", "-center", message],
        ]:
            try:
                subprocess.run(cmd, timeout=30)
                return
            except FileNotFoundError:
                continue
        print(f"{title}: {message}", file=sys.stderr)

    def open_path(self, path: Path) -> None:
        """xdg-open — abre com o programa padrao do sistema."""
        subprocess.Popen(["xdg-open", str(path)])
