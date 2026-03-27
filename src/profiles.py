"""Sistema de profiles customizaveis para initial_prompt do Whisper.

Cada profile e um .txt em %LOCALAPPDATA%/Scribe4me/profiles/.
Formato: linha 1 = nome, linha 2 (opcional) = @code_mode, restante = prompt.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from src.config import APP_NAME

logger = logging.getLogger("scribe4me.profiles")

PROFILES_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / APP_NAME / "profiles"

# --- Prompts built-in ---

_PROMPT_GERAL = (
    "Ontem fui ao mercado comprar frutas e legumes. Depois, passei na farmácia "
    "para buscar o remédio que o médico receitou. A consulta foi rápida, mas "
    "ele pediu alguns exames de sangue. Preciso ligar para o laboratório e "
    "agendar para a semana que vem. Minha mãe perguntou se eu poderia ajudar "
    "com a mudança no sábado. Disse que sim, mas vou precisar de ajuda também."
)

_PROMPT_TECH = (
    "Fiz o deploy no staging e rodei o pipeline de CI/CD pelo GitHub Actions. "
    "O code review apontou que o endpoint da API precisa de rate limiting e throttling "
    "com token bucket no middleware. Vou commitar o fix na branch develop e abrir um "
    "pull request antes do merge na main. "
    "No frontend, o componente React com async/await no callback estava dando exception "
    "no try/catch. Rodei o debug com breakpoint e vi no stack trace que o import do "
    "módulo SQL do database ORM tinha um bug no query builder. "
    "O Kubernetes cluster no Docker precisa de um load balancer. Instalei via npm e pip "
    "no localhost. O framework do backend usa class, function, method com parâmetro "
    "e return tipados. Atualizei o changelog e o repository no Git."
)

_BUILTIN_PROFILES = [
    ("Geral", _PROMPT_GERAL, False),
    ("Tech-Dev", _PROMPT_TECH, False),
    ("Code Mode", _PROMPT_TECH, True),
]


@dataclass
class Profile:
    """Um profile de prompt para o Whisper."""

    name: str
    prompt: str
    code_mode: bool = False
    path: Path | None = None
    builtin: bool = False


def load_profile(path: Path) -> Profile:
    """Le um .txt e retorna Profile."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    lines = text.strip().splitlines()
    if not lines:
        return Profile(name=path.stem, prompt="", path=path)

    name = lines[0].strip()
    code_mode = False
    prompt_start = 1

    if len(lines) > 1 and lines[1].strip().lower() == "@code_mode":
        code_mode = True
        prompt_start = 2

    prompt = " ".join(line.strip() for line in lines[prompt_start:] if line.strip())

    return Profile(name=name, prompt=prompt, code_mode=code_mode, path=path)


def _save_builtin(name: str, prompt: str, code_mode: bool) -> Path:
    """Salva um profile built-in como .txt."""
    filename = name.replace("/", "-").replace(" ", "-") + ".txt"
    path = PROFILES_DIR / filename
    if path.exists():
        return path  # nao sobrescreve

    lines = [name]
    if code_mode:
        lines.append("@code_mode")
    lines.append(prompt)

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Profile built-in criado: %s", path)
    return path


def ensure_builtin_profiles() -> None:
    """Cria profiles built-in se nao existem (first-run)."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    for name, prompt, code_mode in _BUILTIN_PROFILES:
        _save_builtin(name, prompt, code_mode)


def list_profiles() -> list[Profile]:
    """Lista todos os profiles (built-in + custom)."""
    ensure_builtin_profiles()
    profiles = []
    builtin_names = {name for name, _, _ in _BUILTIN_PROFILES}

    for path in sorted(PROFILES_DIR.glob("*.txt")):
        try:
            profile = load_profile(path)
            profile.builtin = profile.name in builtin_names
            profiles.append(profile)
        except Exception as e:
            logger.warning("Erro ao carregar profile %s: %s", path, e)

    # Built-in primeiro, depois custom por nome
    profiles.sort(key=lambda p: (not p.builtin, p.name))
    return profiles


def get_profile_by_name(name: str) -> Profile | None:
    """Busca profile pelo nome."""
    for profile in list_profiles():
        if profile.name == name:
            return profile
    return None


def get_default_profile() -> Profile:
    """Retorna profile padrao (Tech-Dev)."""
    profile = get_profile_by_name("Tech-Dev")
    if profile:
        return profile
    # Fallback absoluto
    return Profile(name="Fallback", prompt=_PROMPT_TECH, builtin=True)
