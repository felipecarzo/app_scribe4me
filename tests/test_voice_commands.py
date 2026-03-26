"""Testes para voice_commands.py — engine de comandos de voz."""

from src.voice_commands import VoiceCommandEngine, CommandResult


def _engine():
    return VoiceCommandEngine()


# --- Texto livre (sem comandos) ---

def test_passthrough_normal_text():
    e = _engine()
    results = e.process("Olá mundo")
    assert len(results) == 1
    assert results[0].text == "Olá mundo"
    assert not results[0].consumed


def test_passthrough_with_commas():
    e = _engine()
    results = e.process("Olá, tudo bem?")
    # Segmenta por virgula — comportamento esperado
    assert len(results) == 2
    assert not results[0].consumed
    assert not results[1].consumed


def test_empty_text():
    e = _engine()
    assert e.process("") == []
    assert e.process("   ") == []


# --- Comandos estruturais ---

def test_tab():
    e = _engine()
    results = e.process("tab")
    assert len(results) == 1
    assert results[0].text == "\t"
    assert results[0].consumed


def test_tabulacao():
    e = _engine()
    results = e.process("tabulação")
    assert results[0].text == "\t"
    assert results[0].consumed


def test_indentar():
    e = _engine()
    results = e.process("indentar")
    assert results[0].text == "\t"
    assert results[0].consumed


def test_enter():
    e = _engine()
    results = e.process("enter")
    assert results[0].text == "\n"
    assert results[0].consumed


def test_nova_linha():
    e = _engine()
    results = e.process("nova linha")
    assert results[0].text == "\n"
    assert results[0].consumed


def test_espaco():
    e = _engine()
    results = e.process("espaço")
    assert results[0].text == " "
    assert results[0].consumed


def test_backspace():
    e = _engine()
    results = e.process("backspace")
    assert results[0].keypress == "backspace"
    assert results[0].consumed


def test_apagar():
    e = _engine()
    results = e.process("apagar")
    assert results[0].keypress == "backspace"
    assert results[0].consumed


def test_abre_parenteses():
    e = _engine()
    results = e.process("abre parênteses")
    assert results[0].text == "("
    assert results[0].consumed


def test_fecha_parenteses():
    e = _engine()
    results = e.process("fecha parênteses")
    assert results[0].text == ")"
    assert results[0].consumed


def test_abre_chaves():
    e = _engine()
    results = e.process("abre chaves")
    assert results[0].text == "{"
    assert results[0].consumed


def test_fecha_chaves():
    e = _engine()
    results = e.process("fecha chaves")
    assert results[0].text == "}"
    assert results[0].consumed


def test_abre_colchetes():
    e = _engine()
    results = e.process("abre colchetes")
    assert results[0].text == "["
    assert results[0].consumed


def test_fecha_colchetes():
    e = _engine()
    results = e.process("fecha colchetes")
    assert results[0].text == "]"
    assert results[0].consumed


def test_dois_pontos():
    e = _engine()
    results = e.process("dois pontos")
    assert results[0].text == ":"
    assert results[0].consumed


def test_ponto_e_virgula():
    e = _engine()
    results = e.process("ponto e vírgula")
    assert results[0].text == ";"
    assert results[0].consumed


def test_aspas():
    e = _engine()
    results = e.process("aspas")
    assert results[0].text == '"'
    assert results[0].consumed


def test_igual():
    e = _engine()
    results = e.process("igual")
    assert results[0].text == "="
    assert results[0].consumed


def test_seta():
    e = _engine()
    results = e.process("seta")
    assert results[0].text == "=>"
    assert results[0].consumed


def test_arrow():
    e = _engine()
    results = e.process("arrow")
    assert results[0].text == "=>"
    assert results[0].consumed


def test_menor_que():
    e = _engine()
    results = e.process("menor que")
    assert results[0].text == "<"
    assert results[0].consumed


def test_maior_que():
    e = _engine()
    results = e.process("maior que")
    assert results[0].text == ">"
    assert results[0].consumed


def test_hashtag():
    e = _engine()
    results = e.process("hashtag")
    assert results[0].text == "#"
    assert results[0].consumed


def test_underscore():
    e = _engine()
    results = e.process("underscore")
    assert results[0].text == "_"
    assert results[0].consumed


# --- Code shortcuts ---

def test_def_funcao():
    e = _engine()
    results = e.process("def função calcular")
    assert results[0].text == "def calcular():\n\t"
    assert results[0].consumed


def test_print_de():
    e = _engine()
    results = e.process("print de hello world")
    assert results[0].text == 'print("hello world")'
    assert results[0].consumed


def test_if_statement():
    e = _engine()
    results = e.process("if x > 0")
    assert results[0].text == "if x > 0:"
    assert results[0].consumed


def test_for_loop():
    e = _engine()
    results = e.process("for item in lista")
    assert results[0].text == "for item in lista:"
    assert results[0].consumed


def test_import_module():
    e = _engine()
    results = e.process("import os")
    assert results[0].text == "import os"
    assert results[0].consumed


def test_from_import():
    e = _engine()
    results = e.process("from os import path")
    assert results[0].text == "from os import path"
    assert results[0].consumed


def test_comentario():
    e = _engine()
    results = e.process("comentário isso é um teste")
    assert results[0].text == "# isso é um teste"
    assert results[0].consumed


def test_classe():
    e = _engine()
    results = e.process("classe Animal")
    assert results[0].text == "class Animal:\n\t"
    assert results[0].consumed


def test_retorna():
    e = _engine()
    results = e.process("retorna resultado")
    assert results[0].text == "return resultado"
    assert results[0].consumed


def test_variavel():
    e = _engine()
    results = e.process("variável x igual 10")
    assert results[0].text == "x = 10"
    assert results[0].consumed


# --- Navegacao ---

def test_desfazer():
    e = _engine()
    results = e.process("desfazer")
    assert results[0].keypress == "ctrl+z"
    assert results[0].consumed


def test_salvar():
    e = _engine()
    results = e.process("salvar")
    assert results[0].keypress == "ctrl+s"
    assert results[0].consumed


def test_selecionar_tudo():
    e = _engine()
    results = e.process("selecionar tudo")
    assert results[0].keypress == "ctrl+a"
    assert results[0].consumed


def test_copiar():
    e = _engine()
    results = e.process("copiar")
    assert results[0].keypress == "ctrl+c"
    assert results[0].consumed


def test_undo_alias():
    e = _engine()
    results = e.process("undo")
    assert results[0].keypress == "ctrl+z"
    assert results[0].consumed


# --- Case/accent insensitive ---

def test_case_insensitive():
    e = _engine()
    results = e.process("TAB")
    assert results[0].text == "\t"
    assert results[0].consumed


def test_accent_insensitive():
    e = _engine()
    results = e.process("tabulacao")
    assert results[0].text == "\t"
    assert results[0].consumed


# --- Multi-comando segmentado ---

def test_multi_command_tab_enter():
    e = _engine()
    results = e.process("tab, enter, tab")
    assert len(results) == 3
    assert results[0].text == "\t"
    assert results[1].text == "\n"
    assert results[2].text == "\t"
    assert all(r.consumed for r in results)


def test_multi_command_mixed():
    e = _engine()
    results = e.process("tab, hello world")
    assert len(results) == 2
    assert results[0].text == "\t"
    assert results[0].consumed
    assert results[1].text == "hello world"
    assert not results[1].consumed


# --- _OriginalMatch preserva casing ---

def test_classe_preserves_casing():
    e = _engine()
    results = e.process("classe MinhaClasse")
    assert results[0].text == "class MinhaClasse:\n\t"


def test_def_preserves_casing():
    e = _engine()
    results = e.process("def função Calcular")
    assert results[0].text == "def Calcular():\n\t"


def test_for_preserves_casing():
    e = _engine()
    results = e.process("for Item in Lista")
    assert results[0].text == "for Item in Lista:"
