"""Engine de comandos de voz para programacao (Code Mode).

Processa texto transcrito e converte comandos falados em acoes de codigo:
- Comandos estruturais: tab, enter, parenteses, chaves, etc.
- Code shortcuts: def, print, if, for, import, etc.
- Navegacao: desfazer, salvar, copiar, etc.
"""

import re
import logging
import unicodedata
from dataclasses import dataclass, field

logger = logging.getLogger("scribe4me.voice_commands")


@dataclass
class CommandResult:
    """Resultado do processamento de um comando."""

    text: str = ""
    keypress: str = ""           # nome da tecla (backspace, ctrl+z, etc.)
    consumed: bool = False       # True se o texto foi consumido como comando


@dataclass
class CommandDef:
    """Definicao de um comando de voz."""

    pattern: re.Pattern
    handler: object  # Callable
    description: str = ""


def _normalize(text: str) -> str:
    """Remove acentos e converte para minusculas para matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


class _OriginalMatch:
    """Wrapper de match que extrai grupos do texto original preservando casing."""

    def __init__(self, norm_match: re.Match, original: str):
        self._norm = norm_match
        self._original = original

    def group(self, n: int = 0) -> str:
        """Retorna grupo N usando posicoes do match normalizado sobre o original."""
        if n == 0:
            return self._original
        start, end = self._norm.span(n)
        return self._original[start:end]

    def groups(self):
        return tuple(self.group(i + 1) for i in range(len(self._norm.groups())))


class VoiceCommandEngine:
    """Processa texto transcrito e converte comandos em acoes de codigo."""

    def __init__(self):
        self._commands: list[CommandDef] = []
        self._register_structural()
        self._register_shortcuts()
        self._register_navigation()

    def process(self, text: str) -> list[CommandResult]:
        """Processa texto, retornando lista de resultados.

        Tenta casar comandos da esquerda para a direita.
        Texto nao reconhecido como comando e passado adiante.
        """
        if not text or not text.strip():
            return []

        results = []
        original = text.strip()
        normalized = _normalize(original)

        # Tenta casar o texto inteiro primeiro (comando simples)
        result = self._try_match(normalized, original)
        if result and result.consumed:
            logger.debug("Comando reconhecido: '%s' -> %s", original, result)
            return [result]

        # Se nao casou inteiro, tenta segmentar por pontuacao/separadores
        segments = self._split_segments(original)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            norm_seg = _normalize(segment)
            result = self._try_match(norm_seg, segment)
            if result and result.consumed:
                results.append(result)
            else:
                # Texto livre — passar adiante
                results.append(CommandResult(text=segment, consumed=False))

        return results if results else [CommandResult(text=original, consumed=False)]

    def _try_match(self, normalized: str, original: str) -> CommandResult | None:
        """Tenta casar texto contra todos os comandos.

        Faz match no normalizado mas tenta extrair grupos do original
        para preservar casing e acentos.
        """
        for cmd in self._commands:
            match = cmd.pattern.fullmatch(normalized)
            if match:
                # Tenta extrair grupos do original para preservar casing
                orig_match = cmd.pattern.fullmatch(original.lower())
                if orig_match and orig_match.groups():
                    # Reconstruir match com valores originais por posicao
                    return cmd.handler(_OriginalMatch(match, original))
                return cmd.handler(match)
        return None

    def _split_segments(self, text: str) -> list[str]:
        """Segmenta texto em comandos individuais.

        Separa por virgulas e pontos, que sao pausas naturais na fala.
        """
        # Separa por virgula, ponto, ponto-e-virgula (pausas naturais)
        parts = re.split(r"[,.\;]\s*", text)
        return [p for p in parts if p.strip()]

    # --- Registro de comandos ---

    def _register_structural(self):
        """Registra comandos estruturais (caracteres especiais)."""
        structural = [
            # Whitespace
            (r"tab(?:ulacao)?|indentar", "\t", "Insere tab"),
            (r"enter|nova linha|quebra linha|new line", "\n", "Insere nova linha"),
            (r"espaco|space", " ", "Insere espaco"),

            # Backspace (keypress, nao texto)
            (r"backspace|apagar|delete", None, "Apaga caractere"),

            # Delimitadores
            (r"abre parenteses?|open paren", "(", "Abre parenteses"),
            (r"fecha parenteses?|close paren", ")", "Fecha parenteses"),
            (r"abre chaves?|open brace", "{", "Abre chaves"),
            (r"fecha chaves?|close brace", "}", "Fecha chaves"),
            (r"abre colchetes?|open bracket", "[", "Abre colchetes"),
            (r"fecha colchetes?|close bracket", "]", "Fecha colchetes"),

            # Pontuacao
            (r"dois pontos|colon", ":", "Dois pontos"),
            (r"ponto e virgula|semicolon", ";", "Ponto e virgula"),
            (r"aspas|quote|abre aspas|open quote", '"', "Aspas"),
            (r"fecha aspas|close quote", '"', "Fecha aspas"),

            # Operadores
            (r"igual|equals", "=", "Igual"),
            (r"seta|arrow", "=>", "Arrow function"),
            (r"duplo igual|double equals", "==", "Comparacao"),
            (r"diferente|not equals", "!=", "Diferente"),
            (r"menor que|less than", "<", "Menor que"),
            (r"maior que|greater than", ">", "Maior que"),
            (r"barra|slash", "/", "Barra"),
            (r"contra barra|contrabarra|backslash", "\\", "Contra barra"),
            (r"hashtag|hash|cerquilha", "#", "Hash"),
            (r"arroba|at sign", "@", "Arroba"),
            (r"underline|underscore", "_", "Underscore"),
        ]

        for pattern_str, text_out, desc in structural:
            if text_out is None:
                # Keypress command
                self._commands.append(CommandDef(
                    pattern=re.compile(pattern_str),
                    handler=lambda m, k="backspace": CommandResult(keypress=k, consumed=True),
                    description=desc,
                ))
            else:
                self._commands.append(CommandDef(
                    pattern=re.compile(pattern_str),
                    handler=lambda m, t=text_out: CommandResult(text=t, consumed=True),
                    description=desc,
                ))

    def _register_shortcuts(self):
        """Registra code shortcuts (comandos compostos)."""
        shortcuts = [
            (r"def fun[cç](?:ao|ão) (\w+)",
             lambda m: CommandResult(text=f"def {m.group(1)}():\n\t", consumed=True),
             "Define funcao"),

            (r"print de (.+)",
             lambda m: CommandResult(text=f'print("{m.group(1)}")', consumed=True),
             "Print"),

            (r"if (.+)",
             lambda m: CommandResult(text=f"if {m.group(1)}:", consumed=True),
             "If statement"),

            (r"for (\w+) in (\w+)",
             lambda m: CommandResult(text=f"for {m.group(1)} in {m.group(2)}:", consumed=True),
             "For loop"),

            (r"import (\w+)",
             lambda m: CommandResult(text=f"import {m.group(1)}", consumed=True),
             "Import"),

            (r"from (\w+) import (\w+)",
             lambda m: CommandResult(text=f"from {m.group(1)} import {m.group(2)}", consumed=True),
             "From import"),

            (r"coment(?:a|á)rio (.+)",
             lambda m: CommandResult(text=f"# {m.group(1)}", consumed=True),
             "Comentario"),

            (r"classe (\w+)",
             lambda m: CommandResult(text=f"class {m.group(1)}:\n\t", consumed=True),
             "Define classe"),

            (r"retorna (.+)",
             lambda m: CommandResult(text=f"return {m.group(1)}", consumed=True),
             "Return"),

            (r"vari(?:a|á)vel (\w+) igual (.+)",
             lambda m: CommandResult(text=f"{m.group(1)} = {m.group(2)}", consumed=True),
             "Atribuicao"),
        ]

        for pattern_str, handler, desc in shortcuts:
            self._commands.append(CommandDef(
                pattern=re.compile(pattern_str),
                handler=handler,
                description=desc,
            ))

    def _register_navigation(self):
        """Registra comandos de navegacao/controle (keypresses)."""
        navigation = [
            (r"selecionar tudo|select all", "ctrl+a", "Selecionar tudo"),
            (r"desfazer|undo", "ctrl+z", "Desfazer"),
            (r"refazer|redo", "ctrl+y", "Refazer"),
            (r"salvar|save", "ctrl+s", "Salvar"),
            (r"copiar|copy", "ctrl+c", "Copiar"),
            (r"colar|paste", "ctrl+v", "Colar"),
            (r"recortar|cut", "ctrl+x", "Recortar"),
        ]

        for pattern_str, keypress, desc in navigation:
            self._commands.append(CommandDef(
                pattern=re.compile(pattern_str),
                handler=lambda m, k=keypress: CommandResult(keypress=k, consumed=True),
                description=desc,
            ))
