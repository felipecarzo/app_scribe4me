"""Testes para postprocess.py."""

from src.postprocess import postprocess


class TestPostprocess:
    def test_empty_string(self):
        assert postprocess("") == ""

    def test_already_correct(self):
        assert postprocess("Olá, tudo bem?") == "Olá, tudo bem?"

    def test_capitalize_first_letter(self):
        assert postprocess("olá mundo") == "Olá mundo"

    def test_capitalize_after_period(self):
        assert postprocess("primeira frase. segunda frase") == "Primeira frase. Segunda frase"

    def test_capitalize_after_exclamation(self):
        assert postprocess("que legal! vamos lá") == "Que legal! Vamos lá"

    def test_capitalize_after_question(self):
        assert postprocess("como vai? tudo bem") == "Como vai? Tudo bem"

    def test_remove_space_before_punctuation(self):
        assert postprocess("Olá , mundo .") == "Olá, mundo."

    def test_add_space_after_punctuation(self):
        assert postprocess("Olá,mundo.teste") == "Olá, mundo. Teste"

    def test_remove_duplicate_punctuation(self):
        assert postprocess("Teste...") == "Teste."
        assert postprocess("Teste!?!") == "Teste!"

    def test_complex_sentence(self):
        result = postprocess("olá , tudo bem ? sim , estou trabalhando . vamos lá")
        assert result == "Olá, tudo bem? Sim, estou trabalhando. Vamos lá"

    def test_accented_characters(self):
        assert postprocess("está funcionando. ótimo") == "Está funcionando. Ótimo"

    def test_preserves_already_capitalized(self):
        assert postprocess("Python é legal. JavaScript também.") == "Python é legal. JavaScript também."
