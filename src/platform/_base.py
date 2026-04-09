"""Interface abstrata para operacoes especificas de plataforma."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class PlatformBackend(Protocol):
    """Contrato que cada backend de plataforma deve implementar."""

    def config_dir(self, app_name: str) -> Path:
        """Diretorio de dados/config do app (criado se nao existir)."""
        ...

    def get_ram_mb(self) -> int:
        """RAM fisica total em MB."""
        ...

    def acquire_single_instance(self, app_name: str) -> Any:
        """Garante instancia unica. Encerra o processo se ja houver outra.

        Retorna um objeto que deve ser mantido vivo (referencia) ate o fim do app.
        """
        ...

    def show_error_dialog(self, title: str, message: str) -> None:
        """Exibe dialogo de erro nativo (funciona sem console)."""
        ...

    def open_path(self, path: Path) -> None:
        """Abre arquivo ou diretorio com o programa padrao do sistema."""
        ...
