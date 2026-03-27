"""Testes para profiles.py — sistema de profiles customizaveis."""

import os
import textwrap
from pathlib import Path

import pytest

from src.profiles import (
    Profile,
    load_profile,
    list_profiles,
    get_profile_by_name,
    get_default_profile,
    ensure_builtin_profiles,
    _save_builtin,
    _BUILTIN_PROFILES,
    PROFILES_DIR,
)


@pytest.fixture
def tmp_profiles_dir(tmp_path, monkeypatch):
    """Redireciona PROFILES_DIR para diretorio temporario."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    monkeypatch.setattr("src.profiles.PROFILES_DIR", profiles_dir)
    return profiles_dir


# --- Profile dataclass ---

class TestProfileDataclass:
    def test_defaults(self):
        p = Profile(name="Test", prompt="hello")
        assert p.name == "Test"
        assert p.prompt == "hello"
        assert p.code_mode is False
        assert p.path is None
        assert p.builtin is False

    def test_code_mode(self):
        p = Profile(name="Code", prompt="x", code_mode=True)
        assert p.code_mode is True

    def test_builtin_flag(self):
        p = Profile(name="B", prompt="y", builtin=True)
        assert p.builtin is True


# --- load_profile ---

class TestLoadProfile:
    def test_load_basic(self, tmp_path):
        f = tmp_path / "basic.txt"
        f.write_text("Meu Profile\nEste e o prompt completo.", encoding="utf-8")
        p = load_profile(f)
        assert p.name == "Meu Profile"
        assert p.prompt == "Este e o prompt completo."
        assert p.code_mode is False
        assert p.path == f

    def test_load_code_mode(self, tmp_path):
        f = tmp_path / "code.txt"
        f.write_text("Code Profile\n@code_mode\nPrompt para codigo.", encoding="utf-8")
        p = load_profile(f)
        assert p.name == "Code Profile"
        assert p.code_mode is True
        assert p.prompt == "Prompt para codigo."

    def test_load_code_mode_case_insensitive(self, tmp_path):
        f = tmp_path / "code2.txt"
        f.write_text("Code2\n@Code_Mode\nPrompt.", encoding="utf-8")
        p = load_profile(f)
        assert p.code_mode is True

    def test_load_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        p = load_profile(f)
        assert p.name == "empty"
        assert p.prompt == ""

    def test_load_multiline_prompt(self, tmp_path):
        f = tmp_path / "multi.txt"
        content = "Multi\nLinha um.\nLinha dois.\nLinha tres."
        f.write_text(content, encoding="utf-8")
        p = load_profile(f)
        assert p.name == "Multi"
        assert p.prompt == "Linha um. Linha dois. Linha tres."

    def test_load_latin1_fallback(self, tmp_path):
        f = tmp_path / "latin.txt"
        # Escreve em latin-1 (byte 0xe9 = e com acento nao e UTF-8 valido sozinho)
        f.write_bytes(b"Caf\xe9\nPrompt caf\xe9.")
        p = load_profile(f)
        assert "Caf" in p.name
        assert "caf" in p.prompt

    def test_load_name_only(self, tmp_path):
        f = tmp_path / "nameonly.txt"
        f.write_text("Apenas Nome", encoding="utf-8")
        p = load_profile(f)
        assert p.name == "Apenas Nome"
        assert p.prompt == ""

    def test_load_blank_lines_skipped(self, tmp_path):
        f = tmp_path / "blanks.txt"
        f.write_text("Profile\n\nLinha A\n\nLinha B\n", encoding="utf-8")
        p = load_profile(f)
        assert p.prompt == "Linha A Linha B"


# --- _save_builtin ---

class TestSaveBuiltin:
    def test_creates_file(self, tmp_profiles_dir):
        path = _save_builtin("Test Profile", "prompt text", False)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Test Profile" in content
        assert "prompt text" in content
        assert "@code_mode" not in content

    def test_creates_file_with_code_mode(self, tmp_profiles_dir):
        path = _save_builtin("Code", "prompt", True)
        content = path.read_text(encoding="utf-8")
        assert "@code_mode" in content

    def test_does_not_overwrite(self, tmp_profiles_dir):
        path = _save_builtin("NoOverwrite", "original", False)
        original_content = path.read_text(encoding="utf-8")
        _save_builtin("NoOverwrite", "modified", False)
        assert path.read_text(encoding="utf-8") == original_content

    def test_filename_sanitization(self, tmp_profiles_dir):
        path = _save_builtin("A/B C", "prompt", False)
        assert path.name == "A-B-C.txt"


# --- ensure_builtin_profiles ---

class TestEnsureBuiltinProfiles:
    def test_creates_all_builtins(self, tmp_profiles_dir):
        ensure_builtin_profiles()
        files = list(tmp_profiles_dir.glob("*.txt"))
        assert len(files) >= len(_BUILTIN_PROFILES)

    def test_idempotent(self, tmp_profiles_dir):
        ensure_builtin_profiles()
        ensure_builtin_profiles()
        files = list(tmp_profiles_dir.glob("*.txt"))
        assert len(files) == len(_BUILTIN_PROFILES)


# --- list_profiles ---

class TestListProfiles:
    def test_lists_builtins(self, tmp_profiles_dir):
        profiles = list_profiles()
        names = [p.name for p in profiles]
        for bname, _, _ in _BUILTIN_PROFILES:
            assert bname in names

    def test_builtins_first(self, tmp_profiles_dir):
        profiles = list_profiles()
        # Todos os builtins devem vir antes dos custom
        builtin_count = sum(1 for p in profiles if p.builtin)
        for i in range(builtin_count):
            assert profiles[i].builtin is True

    def test_includes_custom(self, tmp_profiles_dir):
        ensure_builtin_profiles()
        custom = tmp_profiles_dir / "Custom.txt"
        custom.write_text("Custom Profile\nMy prompt.", encoding="utf-8")
        profiles = list_profiles()
        names = [p.name for p in profiles]
        assert "Custom Profile" in names

    def test_custom_not_builtin(self, tmp_profiles_dir):
        ensure_builtin_profiles()
        custom = tmp_profiles_dir / "Custom.txt"
        custom.write_text("Custom Profile\nMy prompt.", encoding="utf-8")
        profiles = list_profiles()
        custom_p = [p for p in profiles if p.name == "Custom Profile"][0]
        assert custom_p.builtin is False

    def test_bad_file_skipped(self, tmp_profiles_dir):
        """Arquivo corrompido nao impede listagem."""
        ensure_builtin_profiles()
        bad = tmp_profiles_dir / "bad.txt"
        # Cria arquivo que vai ser legivel mas testa robustez
        bad.write_bytes(b"\x00\x01\x02")
        profiles = list_profiles()
        # Deve ter pelo menos os builtins (bad pode ou nao aparecer, nao deve crashar)
        assert len(profiles) >= len(_BUILTIN_PROFILES)


# --- get_profile_by_name ---

class TestGetProfileByName:
    def test_found(self, tmp_profiles_dir):
        p = get_profile_by_name("Tech-Dev")
        assert p is not None
        assert p.name == "Tech-Dev"

    def test_not_found(self, tmp_profiles_dir):
        p = get_profile_by_name("NaoExiste")
        assert p is None

    def test_geral(self, tmp_profiles_dir):
        p = get_profile_by_name("Geral")
        assert p is not None
        assert p.code_mode is False

    def test_code_mode_profile(self, tmp_profiles_dir):
        p = get_profile_by_name("Code Mode")
        assert p is not None
        assert p.code_mode is True


# --- get_default_profile ---

class TestGetDefaultProfile:
    def test_returns_tech_dev(self, tmp_profiles_dir):
        p = get_default_profile()
        assert p.name == "Tech-Dev"

    def test_fallback_when_no_profiles(self, tmp_profiles_dir):
        """Se PROFILES_DIR estiver vazio e builtins falharem, retorna fallback."""
        # Sobrescreve ensure_builtin para simular falha
        import src.profiles as mod
        original = mod.ensure_builtin_profiles

        def broken():
            pass  # nao cria nada

        mod.ensure_builtin_profiles = broken
        try:
            # Limpa diretorio
            for f in tmp_profiles_dir.glob("*.txt"):
                f.unlink()
            p = get_default_profile()
            # Deve retornar o Fallback absoluto
            assert p.name == "Fallback"
            assert p.builtin is True
        finally:
            mod.ensure_builtin_profiles = original
