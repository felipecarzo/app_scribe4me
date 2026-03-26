# VOC-PLAN — Voice Coding (Programacao por Voz)

> Feature: Permitir programadores escreverem codigo usando comandos de voz.
> Criado: 2026-03-26
> Status: Planejamento

---

## Resumo da Arquitetura Atual

```
[Microfone] -> recorder.py -> audio float32
    -> transcriber.py (faster-whisper + initial_prompt + VAD)
    -> postprocess.py (pontuacao, capitalizacao)
    -> clipboard.py / OutputHandler (cursor paste ou clipboard)
```

O pipeline atual e linear: audio entra, texto sai. Os voice commands precisam
de uma camada intermediaria entre o postprocess e o output, que interpreta
o texto transcrito e converte comandos falados em acoes de codigo.

---

## Arquitetura Proposta

```
[Microfone] -> recorder.py -> audio float32
    -> transcriber.py (initial_prompt expandido - VOC-01)
    -> postprocess.py (pontuacao, capitalizacao - inalterado)
    -> voice_commands.py (NOVO - VOC-02/03)
        |-- se code_mode ativo: interpreta comandos -> texto/acoes
        |-- se code_mode inativo: passa texto direto (bypass)
    -> clipboard.py / OutputHandler (cursor paste ou clipboard)
        |-- extendido para suportar keypresses (VOC-04)
```

### Decisoes Arquiteturais

1. **Novo modulo `src/voice_commands.py`** — toda a logica de comandos isolada.
   Nao polui postprocess.py (que deve continuar fazendo apenas cleanup de pontuacao).

2. **Regex-based command matching** — comandos sao definidos como lista de
   `(pattern, action)`. Facil de extender, sem dependencias externas, rapido.

3. **Code Mode como flag no Config** — `code_mode: bool = False` no dataclass.
   O tray toggle simplesmente altera essa flag. Sem novo AppMode enum
   (evita quebrar o pipeline scribe/translate/voice que ja existe).

4. **OutputHandler extendido** — precisa enviar keypresses (Ctrl+Z, Ctrl+S, etc.)
   alem de texto. Novo metodo `send_keypress()` no clipboard.py.

---

## Sprint 8 — Voice Coding: Layer 1 (Prompt Tecnico)

| ID | Task | Complexidade | Depende de | Desbloqueia | Arquivos |
|---|---|---|---|---|---|
| VOC-01 | Expandir initial_prompt com vocabulario de programacao | Baixa | — | VOC-02 | `src/transcriber.py` |

### VOC-01 — Initial Prompt Tecnico

**Objetivo:** Melhorar o reconhecimento de termos tecnicos pelo Whisper,
expandindo o `_PUNCTUATION_PROMPT` com vocabulario de programacao.

**Restricao critica:** O initial_prompt do faster-whisper tem limite de ~224 tokens.
O paragrafo precisa ser coerente (nao uma lista) e usar o maximo de termos
naturalmente.

**Termos obrigatorios a incluir:**
- DevOps: CI/CD, deploy, Docker, Kubernetes, pipeline, staging
- Git: commit, branch, merge, pull request, repository, GitHub
- Backend: endpoint, API, middleware, database, SQL, query, backend, framework
- Frontend: frontend, React, component, CSS, DOM
- Linguagem: function, class, variable, method, parameter, return, import, module, package
- Ferramentas: npm, pip, localhost, debug, breakpoint, stack trace
- Patterns: async, await, callback, try/catch, exception, refactoring
- Infra: token bucket, rate limiting, throttling, load balancer

**Estrategia:** Escrever 2-3 paragrafos curtos simulando um dev falando sobre
seu dia, usando os termos naturalmente. Testar que o token count fica abaixo de 224.

**Criterio de aceite:**
- [ ] Prompt contem pelo menos 40 termos tecnicos distintos
- [ ] Token count <= 224 (verificar com tokenizer do Whisper)
- [ ] Transcricao de "eu fiz o deploy" reconhece "deploy" (nao "the play")
- [ ] Transcricao de "abri um pull request" reconhece "pull request"
- [ ] Testes existentes continuam passando

---

## Sprint 9 — Voice Coding: Layer 2 (Comandos de Voz)

| ID | Task | Complexidade | Depende de | Desbloqueia | Arquivos |
|---|---|---|---|---|---|
| VOC-02 | Criar modulo voice_commands.py com engine de comandos | Media | VOC-01 | VOC-03, VOC-04 | `src/voice_commands.py` (NOVO) |
| VOC-03 | Implementar todos os comandos estruturais e code shortcuts | Media | VOC-02 | VOC-05 | `src/voice_commands.py` |
| VOC-04 | Extender OutputHandler para keypresses (navegacao/controle) | Baixa | VOC-02 | VOC-05 | `src/clipboard.py` |
| VOC-05 | Integrar voice_commands no pipeline do transcriber/main | Baixa | VOC-03, VOC-04 | VOC-06 | `src/transcriber.py`, `src/main.py` |

### VOC-02 — Engine de Comandos de Voz

**Objetivo:** Criar `src/voice_commands.py` com a infraestrutura para
reconhecer e processar comandos falados.

**Design:**

```python
@dataclass
class CommandResult:
    """Resultado do processamento de um comando."""
    text: str = ""           # texto a inserir (pode conter \t, \n)
    keypress: tuple | None = None  # (Key, modifiers) para simular
    consumed: bool = False   # True se o texto foi consumido como comando

class VoiceCommandEngine:
    """Processa texto transcrito e converte comandos em acoes."""

    def __init__(self):
        self._commands: list[tuple[re.Pattern, Callable]] = []
        self._register_defaults()

    def process(self, text: str) -> list[CommandResult]:
        """Processa texto, retornando lista de resultados.

        Se nenhum comando for reconhecido, retorna o texto original.
        Se o texto contiver mix de comandos e texto livre,
        processa sequencialmente.
        """
        ...
```

**Principios:**
- Comandos sao case-insensitive e accent-insensitive
- Cada comando e um `(regex_pattern, handler_function)`
- Handlers retornam `CommandResult`
- O engine processa o texto da esquerda para a direita,
  tentando casar comandos e passando texto livre adiante
- Comandos em portugues sao primarios, aliases em ingles sao opcionais

**Criterio de aceite:**
- [ ] `VoiceCommandEngine` instancia sem erros
- [ ] `process("texto normal")` retorna texto inalterado
- [ ] `process("tab")` retorna `CommandResult(text="\t", consumed=True)`
- [ ] Testes unitarios para o engine (>= 10 casos)

### VOC-03 — Comandos Estruturais e Code Shortcuts

**Objetivo:** Implementar todos os comandos definidos nos requisitos.

**Comandos estruturais (texto -> caractere):**

| Comando falado | Aliases | Resultado |
|---|---|---|
| "tab" / "tabulacao" / "indentar" | — | `\t` |
| "enter" / "nova linha" / "quebra linha" | "new line" | `\n` |
| "espaco" | "space" | ` ` |
| "backspace" / "apagar" | "delete" | keypress: Backspace |
| "abre parenteses" | "open paren" | `(` |
| "fecha parenteses" | "close paren" | `)` |
| "abre chaves" | "open brace" | `{` |
| "fecha chaves" | "close brace" | `}` |
| "abre colchetes" | "open bracket" | `[` |
| "fecha colchetes" | "close bracket" | `]` |
| "dois pontos" | "colon" | `:` |
| "ponto e virgula" | "semicolon" | `;` |
| "aspas" | "quote" | `"` |
| "fecha aspas" | "close quote" | `"` |
| "igual" | "equals" | `=` |
| "seta" / "arrow" | — | `=>` |
| "ponto" | "dot" | `.` |
| "virgula" | "comma" | `,` |
| "menor que" | "less than" | `<` |
| "maior que" | "greater than" | `>` |
| "barra" | "slash" | `/` |
| "contra barra" | "backslash" | `\\` |

**Code shortcuts (comandos compostos):**

| Comando | Regex | Resultado |
|---|---|---|
| "def funcao [name]" | `def fun[cç][aã]o (\w+)` | `def name():\n\t` |
| "print de [text]" | `print de (.+)` | `print("text")` |
| "if [cond]" | `if (.+)` | `if cond:` |
| "for [var] in [iter]" | `for (\w+) in (\w+)` | `for var in iter:` |
| "import [mod]" | `import (\w+)` | `import mod` |
| "comentario [text]" | `coment[aá]rio (.+)` | `# text` |
| "classe [name]" | `classe (\w+)` | `class name:\n\t` |
| "retorna [val]" | `retorna (.+)` | `return val` |

**Desafio principal:** Distinguir quando "tab" e um comando vs. quando o usuario
esta falando sobre "tab" como palavra. Solucao: em code_mode, SEMPRE interpretar
como comando. Se o usuario quiser a palavra literal, desativa code_mode.

**Criterio de aceite:**
- [ ] Todos os comandos estruturais da tabela acima funcionam
- [ ] Todos os code shortcuts da tabela acima funcionam
- [ ] Aliases em ingles funcionam para cada comando
- [ ] Testes unitarios para cada comando (>= 30 casos)
- [ ] Comandos compostos extraem parametros corretamente
  (ex: "def funcao calcular" -> `def calcular():`)

### VOC-04 — OutputHandler com Keypresses

**Objetivo:** Extender `OutputHandler` em `src/clipboard.py` para enviar
keypresses individuais (Backspace, Ctrl+Z, etc.).

**Alteracoes em clipboard.py:**

```python
class OutputHandler:
    # ... metodos existentes ...

    def send_keypress(self, key: Key, modifiers: list[Key] | None = None) -> None:
        """Simula pressionamento de tecla (para comandos de navegacao)."""
        if modifiers:
            for mod in modifiers:
                self._keyboard.press(mod)
        self._keyboard.press(key)
        self._keyboard.release(key)
        if modifiers:
            for mod in reversed(modifiers):
                self._keyboard.release(mod)

    def send_command_results(self, results: list[CommandResult]) -> None:
        """Processa lista de CommandResult — texto e/ou keypresses."""
        for result in results:
            if result.keypress:
                self.send_keypress(*result.keypress)
            elif result.text:
                # Para caracteres especiais (\t, \n), usa type() do pynput
                self._keyboard.type(result.text)
```

**Comandos de navegacao/controle:**

| Comando | Resultado |
|---|---|
| "selecionar tudo" / "select all" | Ctrl+A |
| "desfazer" / "undo" | Ctrl+Z |
| "refazer" / "redo" | Ctrl+Y |
| "salvar" / "save" | Ctrl+S |
| "copiar" / "copy" | Ctrl+C |
| "colar" / "paste" | Ctrl+V |
| "recortar" / "cut" | Ctrl+X |

**Criterio de aceite:**
- [ ] `send_keypress(Key.backspace)` funciona
- [ ] `send_keypress(Key.a, [Key.ctrl])` funciona (select all)
- [ ] `send_command_results()` processa mix de texto e keypresses
- [ ] Testes existentes de OutputHandler continuam passando

### VOC-05 — Integracao no Pipeline

**Objetivo:** Conectar o voice_commands.py no fluxo existente.

**Alteracoes:**

1. **`src/config.py`** — Adicionar `code_mode: bool = False` ao Config dataclass.

2. **`src/main.py`** — No metodo `_pipeline_scribe()`:
   ```python
   def _pipeline_scribe(self, audio) -> str:
       text = self.transcriber.transcribe(audio)
       if self.config.code_mode:
           results = self._voice_engine.process(text)
           self.output.send_command_results(results)
           return ""  # ja enviou via command_results
       return text
   ```

3. **`src/main.py`** — Instanciar `VoiceCommandEngine` no `__init__` do SpeedOsper.

**Decisao:** O code_mode opera como um filtro sobre o modo scribe.
Se `mode=SCRIBE` e `code_mode=True`, os comandos sao processados.
Se `mode=TRANSLATE`, code_mode e ignorado (nao faz sentido traduzir comandos).

**Criterio de aceite:**
- [ ] Com code_mode=False, pipeline funciona identico ao atual
- [ ] Com code_mode=True, "tab enter print de hello" gera `\tprint("hello")`
- [ ] Modos translate e voice ignoram code_mode
- [ ] Teste de integracao do pipeline completo

---

## Sprint 10 — Voice Coding: Layer 3 (Toggle + Tray + Polish)

| ID | Task | Complexidade | Depende de | Desbloqueia | Arquivos |
|---|---|---|---|---|---|
| VOC-06 | Toggle de Code Mode no tray menu | Baixa | VOC-05 | VOC-07 | `src/tray.py`, `src/main.py` |
| VOC-07 | Hotkey dedicada para toggle code mode | Baixa | VOC-06 | VOC-08 | `src/config.py`, `src/main.py` |
| VOC-08 | Feedback visual de code mode (cor/icone diferenciado) | Baixa | VOC-06 | VOC-09 | `src/tray.py` |
| VOC-09 | Testes end-to-end + documentacao | Media | VOC-08 | — | `tests/`, `docs/` |

### VOC-06 — Toggle no Tray Menu

**Objetivo:** Adicionar checkbox "Code Mode" no menu do system tray.

**Alteracoes em `src/tray.py`:**
- Novo item no menu: `"Code Mode [OFF]"` (checkbox toggle)
- Callback `on_code_mode_toggle` passado pelo SpeedOsper
- Item aparece logo abaixo do seletor de modo
- Checkbox reflete estado atual de `config.code_mode`

**Alteracoes em `src/main.py`:**
- Novo callback `_toggle_code_mode()` que altera `config.code_mode`
- Passa callback ao TrayIcon no construtor
- Notificacao: "Code Mode: ON/OFF"

**Criterio de aceite:**
- [ ] Item "Code Mode" aparece no menu do tray
- [ ] Click alterna entre ON e OFF
- [ ] Estado persiste durante a sessao
- [ ] Notificacao confirma a troca

### VOC-07 — Hotkey para Code Mode

**Objetivo:** Atalho de teclado para ligar/desligar code mode sem abrir o menu.

**Proposta:** `Ctrl+Alt+C` (C de Code). Adicionar ao config.py:
```python
hotkey_code_mode: str = "<ctrl>+<alt>+c"
```

**Alteracoes em `src/main.py`:**
- Novo VK code: `_VK_C = 67`
- Handler em `_on_press`: Ctrl+Alt+C -> `_toggle_code_mode()`

**Criterio de aceite:**
- [ ] Ctrl+Alt+C alterna code mode
- [ ] Hotkey funciona mesmo quando tray menu esta fechado
- [ ] Nao conflita com hotkeys existentes (H, T, Q)

### VOC-08 — Feedback Visual

**Objetivo:** Indicar visualmente quando code mode esta ativo.

**Proposta:** Quando code_mode=True e estado=IDLE, usar cor diferenciada.
Opcoes:
- (A) Borda/anel ao redor do circulo verde (mais sutil)
- (B) Cor diferente: ciano (#00BCD4) quando IDLE + code_mode
- (C) Icone com "C" desenhado no centro

**Recomendacao:** Opcao B — simples de implementar, visualmente claro.
Adicionar ao `_COLORS` uma variante `IDLE_CODE`.

**Criterio de aceite:**
- [ ] Icone muda de cor quando code mode e ativado
- [ ] Tooltip inclui "[Code]" quando ativo
- [ ] Ao desativar code mode, volta ao verde padrao

### VOC-09 — Testes E2E e Documentacao

**Objetivo:** Garantir que tudo funciona junto e documentar os comandos.

**Testes:**
- [ ] Teste E2E: gravar "tab tab print de hello enter" em code mode
- [ ] Teste E2E: mesmo texto em mode normal (deve aparecer literal)
- [ ] Teste de regressao: todos os modos existentes (scribe, translate, voice)
- [ ] Teste de latencia: code mode nao adiciona >10ms ao pipeline
- [ ] Teste de todos os comandos com audio real (manual)

**Documentacao:**
- [ ] Lista completa de comandos no README ou help
- [ ] Hotkeys atualizadas no tray tooltip

---

## Grafo de Dependencias

```
VOC-01 (prompt)
   |
   v
VOC-02 (engine) ----+
   |                 |
   v                 v
VOC-03 (comandos)  VOC-04 (keypresses)
   |                 |
   +--------+--------+
            |
            v
         VOC-05 (integracao)
            |
            v
         VOC-06 (tray toggle)
            |
            v
         VOC-07 (hotkey)
            |
            v
         VOC-08 (visual)
            |
            v
         VOC-09 (E2E + docs)
```

---

## Estimativa de Esforco

| Sprint | Tasks | Complexidade total | Sessoes estimadas |
|---|---|---|---|
| Sprint 8 | VOC-01 | Baixa | 1 sessao |
| Sprint 9 | VOC-02, VOC-03, VOC-04, VOC-05 | Media-Alta | 2-3 sessoes |
| Sprint 10 | VOC-06, VOC-07, VOC-08, VOC-09 | Media | 1-2 sessoes |
| **Total** | **9 tasks** | — | **4-6 sessoes** |

---

## Riscos e Mitigacoes

| Risco | Impacto | Mitigacao |
|---|---|---|
| Whisper transcreve comando errado (ex: "tab" -> "tape") | Alto | Initial prompt com termos + fallback com fuzzy matching |
| Latencia do regex processing | Baixo | Regex pre-compilado, lista curta (~30 patterns) |
| Conflito entre texto livre e comandos | Medio | Code mode e explicito (toggle) — usuario sabe quando esta ativo |
| Backspace/keypresses nao funcionam em todos os apps | Medio | Documentar limitacoes; cursor paste ja funciona via Ctrl+V |
| Token limit do initial_prompt estourado | Baixo | Testar com tokenizer antes de commitar |

---

## Ordem de Implementacao Recomendada

1. **VOC-01** — Quick win, melhora imediata na transcricao de termos tech
2. **VOC-02** — Infraestrutura do engine (testavel isoladamente)
3. **VOC-03** — Comandos (testavel com unit tests, sem integrar no app)
4. **VOC-04** — Keypresses no OutputHandler (testavel isoladamente)
5. **VOC-05** — Cola tudo junto (primeiro teste funcional real)
6. **VOC-06 a VOC-09** — UI e polimento

Cada task e independentemente testavel. Nenhuma task quebra funcionalidade existente
ate VOC-05 (que e o ponto de integracao).

---

*Plano criado por: Planner Agent | 2026-03-26*
