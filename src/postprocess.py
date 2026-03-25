"""Pos-processamento de texto transcrito."""

import re


def postprocess(text: str) -> str:
    """Aplica correcoes de pontuacao e formatacao ao texto do Whisper.

    - Capitaliza inicio de frases
    - Remove espacos antes de pontuacao
    - Garante espaco apos pontuacao
    - Remove repeticoes consecutivas de pontuacao
    """
    if not text:
        return text

    # Remove espacos antes de pontuacao
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)

    # Garante espaco apos pontuacao (exceto fim de string)
    text = re.sub(r"([.,;:!?])([A-Za-zÀ-ÿ])", r"\1 \2", text)

    # Remove pontuacao duplicada (ex: "..," -> ".")
    text = re.sub(r"([.!?])[.!?,;:]+", r"\1", text)

    # Capitaliza inicio de frases (apos . ! ?)
    def _capitalize_after_punct(match):
        return match.group(1) + match.group(2).upper()

    text = re.sub(r"([.!?]\s+)([a-zà-ÿ])", _capitalize_after_punct, text)

    # Capitaliza primeira letra do texto
    if text and text[0].islower():
        text = text[0].upper() + text[1:]

    return text.strip()
