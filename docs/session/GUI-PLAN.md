# GUI-PLAN — Profiles + GUI Window + Microphone Icon

> Features: Custom Prompt Profiles, GUI Window (tkinter), Microphone Tray Icon
> Criado: 2026-03-26
> Status: Planejamento

---

## Resumo da Arquitetura Atual

```
[Microfone] -> recorder.py -> audio float32
    -> transcriber.py (faster-whisper + _PUNCTUATION_PROMPT hardcoded + VAD)
    -> postprocess.py
    -> voice_commands.py (se code_mode ativo)
    -> clipboard.py / OutputHandler

[Tray] -> tray.py (pystray)
    -> icone circular colorido (PIL, 64x64)
    -> menu: modelo, modo, idioma, code mode toggle, copiar, log, sair

[Config] -> config.py (dataclass)
    -> code_mode: bool (flag simples)
    -> nenhum sistema de profiles
```

**Pontos de impacto:**
- `_PUNCTUATION_PROMPT` em `transcriber.py` (linha 21-32) e hardcoded — precisa virar dinamico
- `code_mode` no `config.py` (linha 50) e um bool simples — precisa virar um profile
- `_create_icon_image()` em `tray.py` (linha 46-52) desenha apenas um circulo — precisa virar microfone
- Nao existe nenhuma janela GUI — tudo e tray-only
- O tray menu no `tray.py` ja tem toggle de code mode (linha 142-156) — sera substituido por profile selector

---

## Arquitetura Proposta

```
[Profiles]
    %LOCALAPPDATA%/SpeedOsper/profiles/
        Geral.txt          <- prompt neutro (atual _PUNCTUATION_PROMPT)
        Tech-Dev.txt       <- prompt turbo tech (atual)
        Code-Mode.txt      <- prompt + flag code_mode=true
        *.txt              <- profiles do usuario

[Pipeline alterado]
    config.py -> active_profile: Profile (substitui code_mode: bool)
    transcriber.py -> _PUNCTUATION_PROMPT carregado do profile ativo
    main.py -> profile selector callback no tray
    tray.py -> submenu de profiles (substitui code mode toggle)

[GUI Window - NOVO]
    src/gui.py -> tkinter window (thread separada)
        -> log panel (tail do speedosper.log)
        -> botao gravar, dropdown profile, dropdown modo/modelo
        -> status bar (estado, modelo, profile)
    main.py -> instancia GUI opcionalmente
    tray.py -> double-click abre/fecha janela

[Icon]
    tray.py -> _create_icon_image() redesenhado com silhueta de microfone
```

---

## Decisoes Arquiteturais (requerem aprovacao)

### DA-01: Formato do arquivo de profile

**Proposta:** `.txt` puro. Primeira linha = nome do profile. Segunda linha em diante = texto do prompt. Linha especial `@code_mode` ativa voice commands.

```
Tech/Dev
Fiz o deploy no staging e rodei o pipeline de CI/CD pelo GitHub Actions.
O code review apontou que o endpoint da API precisa de rate limiting...
```

```
Code Mode
@code_mode
Fiz o deploy no staging e rodei o pipeline de CI/CD...
```

**Alternativa:** JSON ou TOML para metadados extras (nome, descricao, flags).

**Tradeoff:** TXT e mais simples para usuarios criarem, mas limita extensibilidade futura. JSON seria mais robusto mas assusta usuarios nao-tecnicos.

**Recomendacao:** TXT com convencao de `@` para flags na segunda linha. Se precisar de mais metadados no futuro, migra para TOML.

### DA-02: GUI framework

**Proposta:** tkinter (stdlib). Zero dependencias extras. Thread separada.

**Alternativa:** Dear PyGui (mais bonito, GPU-accelerated) ou PyQt (mais completo).

**Tradeoff:** tkinter e feio mas funciona em qualquer Python. PyQt adiciona ~80MB de dependencias. Dear PyGui adiciona ~20MB.

**Recomendacao:** tkinter. O app ja tem muitas dependencias (whisper, CUDA, PIL, pystray). A janela e auxiliar, nao o foco.

### DA-03: Como o GUI le os logs

**Opcao A:** Tail do arquivo `speedosper.log` (polling a cada 500ms).
**Opcao B:** Logging handler customizado que envia para uma queue, GUI le da queue.

**Tradeoff:** A e mais simples mas tem delay e I/O. B e real-time e eficiente mas acopla o GUI ao logging.

**Recomendacao:** Opcao B — adicionar um `QueueHandler` ao logging. O GUI le da queue. Sem I/O extra, real-time.

### DA-04: Profile storage location

**Proposta:** `%LOCALAPPDATA%/SpeedOsper/profiles/`. Mesmo diretorio pai dos logs.

**Alternativa:** Relativo ao executavel (pasta `profiles/` ao lado do .exe).

**Tradeoff:** LOCALAPPDATA e o padrao Windows para dados de app. Ao lado do .exe facilita backup mas pode ter problemas de permissao em Program Files.

**Recomendacao:** LOCALAPPDATA. Consistente com onde os logs ja estao.

---

## Sprint 11 — Custom Prompt Profiles + Microphone Icon

| ID | Task | Complexidade | Depende de | Desbloqueia | Arquivos |
|---|---|---|---|---|---|
| PRF-01 | Criar modulo `src/profiles.py` — load/save/list profiles | Media | — | PRF-02 | `src/profiles.py` (NOVO) |
| PRF-02 | Criar profiles built-in e first-run bootstrap | Baixa | PRF-01 | PRF-03 | `src/profiles.py` |
| PRF-03 | Integrar profile ativo no transcriber (prompt dinamico) | Media | PRF-02 | PRF-04 | `src/transcriber.py`, `src/config.py` |
| PRF-04 | Profile selector no tray menu (substitui code mode toggle) | Media | PRF-03 | PRF-05 | `src/tray.py`, `src/main.py` |
| PRF-05 | Code Mode como profile especial (ativa voice_commands) | Baixa | PRF-04 | GUI-01 | `src/main.py` |
| ICO-01 | Redesenhar icone do tray com silhueta de microfone | Baixa | — | GUI-04 | `src/tray.py` |

### PRF-01 — Modulo de Profiles

**Objetivo:** Criar `src/profiles.py` com a infraestrutura de profiles.

**Design:**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Profile:
    name: str              # nome exibido no menu
    prompt: str            # texto do initial_prompt para Whisper
    code_mode: bool        # se True, ativa voice_commands
    path: Path | None      # caminho do arquivo (None para built-in em memoria)
    builtin: bool = False  # True para profiles que o app cria automaticamente

PROFILES_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / "SpeedOsper" / "profiles"

def load_profile(path: Path) -> Profile:
    """Le um .txt e retorna Profile."""
    ...

def list_profiles() -> list[Profile]:
    """Lista todos os profiles (built-in + custom)."""
    ...

def ensure_builtin_profiles() -> None:
    """Cria profiles built-in se nao existem."""
    ...

def get_default_profile() -> Profile:
    """Retorna o profile 'Geral' (fallback)."""
    ...
```

**Formato do .txt:**
```
Geral
Fiz o deploy no staging e rodei o pipeline de CI/CD pelo GitHub Actions. O code review apontou que o endpoint da API precisa de rate limiting e throttling com token bucket no middleware...
```

Linha 1: nome.
Linha 2 (opcional): `@code_mode` (flag).
Restante: texto do prompt.

**Criterio de aceite:**
- [ ] `load_profile()` le um .txt e retorna Profile correto
- [ ] `list_profiles()` retorna built-in + custom
- [ ] `ensure_builtin_profiles()` cria arquivos no first-run
- [ ] Profile com `@code_mode` tem `code_mode=True`
- [ ] Testes unitarios (>= 8 casos)

### PRF-02 — Profiles Built-in e Bootstrap

**Objetivo:** Criar os 3 profiles default e garantir que existem no first-run.

**Profiles built-in:**

| Nome | Prompt | code_mode | Descricao |
|---|---|---|---|
| Geral | Prompt neutro com pontuacao basica (portugues conversacional) | False | Para ditado geral, emails, mensagens |
| Tech/Dev | Prompt turbo com vocabulario tech (atual `_PUNCTUATION_PROMPT`) | False | Para developers ditando texto tech |
| Code Mode | Mesmo prompt do Tech/Dev + flag `@code_mode` | True | Para programacao por voz com comandos |

**O prompt "Geral" (novo):**
Um paragrafo neutro, sem jargao tech. Algo como:
```
Ontem fui ao mercado comprar frutas e legumes. Depois, passei na farmacia
para buscar o remedio que o medico receitou. A consulta foi rapida, mas
ele pediu alguns exames de sangue. Preciso ligar para o laboratorio e
agendar para a semana que vem. Minha mae perguntou se eu poderia ajudar
com a mudanca no sabado. Disse que sim, mas vou precisar de ajuda tambem.
```

**Bootstrap flow:**
1. `ensure_builtin_profiles()` chamado no `main()` antes de criar SpeedOsper
2. Verifica se PROFILES_DIR existe; cria se nao
3. Para cada built-in, verifica se o .txt existe; cria se nao
4. Se o .txt ja existe, nao sobrescreve (usuario pode ter editado)

**Criterio de aceite:**
- [ ] First-run cria 3 arquivos .txt em `%LOCALAPPDATA%/SpeedOsper/profiles/`
- [ ] Re-execucao nao sobrescreve profiles existentes
- [ ] Cada profile tem o formato correto (nome na primeira linha)
- [ ] Profile "Code Mode" inclui flag `@code_mode`

### PRF-03 — Integrar Profile no Transcriber

**Objetivo:** `_PUNCTUATION_PROMPT` deixa de ser constante e passa a vir do profile ativo.

**Alteracoes:**

1. **`src/config.py`:**
   - Remover `code_mode: bool` (substituido por `Profile.code_mode`)
   - Adicionar `active_profile_name: str = "Tech/Dev"` (default para manter compatibilidade)
   - Importar e usar Profile

2. **`src/transcriber.py`:**
   - `_PUNCTUATION_PROMPT` vira fallback (usado se nenhum profile carregado)
   - `transcribe()` recebe o prompt do profile ativo via `self.config`
   - Nao mais hardcoded — o prompt vem de `config.active_profile.prompt`

3. **`src/main.py`:**
   - SpeedOsper carrega o profile ativo no init
   - Passa o prompt para o transcriber

**Criterio de aceite:**
- [ ] Trocar profile muda o initial_prompt do Whisper
- [ ] Profile "Geral" usa prompt neutro
- [ ] Profile "Tech/Dev" usa prompt tech (mesmo resultado de antes)
- [ ] Fallback para _PUNCTUATION_PROMPT se profile invalido
- [ ] Testes de regressao passam

### PRF-04 — Profile Selector no Tray Menu

**Objetivo:** Substituir o toggle de code mode por um submenu de profiles.

**Alteracoes em `src/tray.py`:**
- Remover item "Code Mode: ON/OFF" (linha 142-156)
- Adicionar submenu "Profile: [nome]" com radio buttons (um por profile)
- Radio button indica profile ativo
- Callback `on_profile_change(profile_name: str)` passado pelo SpeedOsper

**Alteracoes em `src/main.py`:**
- Novo callback `_change_profile(profile_name: str)`
- Recarrega prompt no transcriber
- Se profile tem `code_mode=True`, ativa voice_commands
- Se profile tem `code_mode=False`, desativa
- Notificacao: "Profile: [nome]"

**Menu resultante:**
```
SpeedOsper
---
Ctrl+Alt+H — Gravar (segura e fala)
Ctrl+Alt+T — Toggle (iniciar/parar)
Ctrl+Q     — Sair
---
Profile: Tech/Dev  >  [*] Geral
                      [ ] Tech/Dev
                      [ ] Code Mode
                      [ ] Medico (custom)
Modo: Scribe       >  ...
Idioma alvo: EN    >  ...
Modelo: Large-v3   >  ...
---
Copiar ultimo texto
Abrir log
---
Sair
```

**Criterio de aceite:**
- [ ] Submenu de profiles aparece no tray
- [ ] Trocar profile muda o prompt do Whisper
- [ ] Profile "Code Mode" ativa voice commands automaticamente
- [ ] Profiles custom (.txt criados pelo usuario) aparecem no menu
- [ ] Hotkey Ctrl+Alt+C removida (nao faz mais sentido)

### PRF-05 — Code Mode como Profile Especial

**Objetivo:** Garantir que a transicao de `code_mode: bool` para profiles funcione.

**Alteracoes:**
- `config.code_mode` removido (ja feito em PRF-03)
- Checar `config.active_profile.code_mode` em vez de `config.code_mode`
- `_pipeline_scribe()` em main.py usa `self._active_profile.code_mode`
- `_toggle_code_mode()` removido de main.py
- Hotkey Ctrl+Alt+C removida do listener
- Tray: cor ciano quando profile com code_mode esta ativo (manter comportamento visual)

**Criterio de aceite:**
- [ ] Selecionar profile "Code Mode" ativa voice commands
- [ ] Selecionar qualquer outro profile desativa voice commands
- [ ] Icone fica ciano quando profile com code_mode ativo
- [ ] Hotkey Ctrl+Alt+C nao faz mais nada (ou e reatribuida)
- [ ] Testes de regressao do voice coding passam

### ICO-01 — Icone de Microfone no Tray

**Objetivo:** Substituir o circulo colorido por um icone de microfone minimalista.

**Design:**
- Canvas 64x64 RGBA
- Circulo preenchido com cor do estado (mesmo esquema de cores atual)
- Silhueta de microfone em branco por cima:
  - Corpo: retangulo arredondado (20x28px, centralizado, topo)
  - Cabeça: semi-circulo no topo do corpo (raio ~10px)
  - Base: arco inferior (meia-lua) abaixo do corpo
  - Pedestal: linha vertical curta + base horizontal
- Tudo desenhado com PIL (ImageDraw)

**Fallback:** Se nao ficar legivel em 16x16, manter circulo com ponto central (dot) para diferenciar.

**Alteracoes em `src/tray.py`:**
- Reescrever `_create_icon_image()` com desenho do microfone
- Manter `_create_blank_image()` inalterado (usado no blink)
- Testar visualmente em resolucoes 16x16, 32x32, 64x64

**Criterio de aceite:**
- [ ] Icone mostra silhueta de microfone reconhecivel
- [ ] Cores mudam corretamente por estado (verde, vermelho, amarelo, azul, roxo, ciano)
- [ ] Visivel e reconhecivel em 16x16 (tamanho real do tray no Windows)
- [ ] Se 16x16 nao fica bom, fallback para circulo com dot
- [ ] Blink (loading/transcribing) continua funcionando

---

## Sprint 12 — GUI Window

| ID | Task | Complexidade | Depende de | Desbloqueia | Arquivos |
|---|---|---|---|---|---|
| GUI-01 | Criar `src/gui.py` — janela basica tkinter (thread separada) | Media | PRF-05 | GUI-02 | `src/gui.py` (NOVO) |
| GUI-02 | Log panel com QueueHandler (real-time) | Media | GUI-01 | GUI-03 | `src/gui.py`, `src/main.py` |
| GUI-03 | Barra de controles (gravar, profile, modo, modelo) | Alta | GUI-02 | GUI-04 | `src/gui.py` |
| GUI-04 | Status bar + double-click tray integration | Media | GUI-03, ICO-01 | GUI-05 | `src/gui.py`, `src/tray.py` |
| GUI-05 | Dark theme + polimento visual | Baixa | GUI-04 | — | `src/gui.py` |

### GUI-01 — Janela Basica tkinter

**Objetivo:** Criar `src/gui.py` com a janela principal rodando em thread separada.

**Design:**

```python
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue

class SpeedOsperGUI:
    """Janela principal do SpeedOsper (opcional — app funciona sem ela)."""

    def __init__(self, log_queue: queue.Queue, callbacks: dict):
        self._log_queue = log_queue
        self._callbacks = callbacks  # on_record, on_profile_change, etc.
        self._root: tk.Tk | None = None
        self._thread: threading.Thread | None = None
        self._visible = False

    def start(self) -> None:
        """Inicia a janela em thread separada."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        """Loop principal do tkinter."""
        self._root = tk.Tk()
        self._root.title("SpeedOsper")
        self._root.geometry("600x400")
        self._root.protocol("WM_DELETE_WINDOW", self.hide)
        self._build_ui()
        self._poll_log_queue()
        self._root.mainloop()

    def show(self) -> None:
        """Mostra a janela."""
        if self._root:
            self._root.after(0, self._root.deiconify)
            self._visible = True

    def hide(self) -> None:
        """Esconde a janela (minimiza pro tray)."""
        if self._root:
            self._root.after(0, self._root.withdraw)
            self._visible = False

    def toggle(self) -> None:
        """Alterna visibilidade."""
        if self._visible:
            self.hide()
        else:
            self.show()
```

**Regra critica:** tkinter nao e thread-safe. Todas as operacoes de UI devem usar `root.after()` para despachar para a thread do tkinter.

**Criterio de aceite:**
- [ ] Janela abre sem crashar o app
- [ ] Fechar a janela esconde (nao mata o processo)
- [ ] App continua funcionando normalmente com janela aberta
- [ ] App funciona normalmente se janela nunca for aberta
- [ ] Thread do tkinter nao bloqueia o tray nem o listener

### GUI-02 — Log Panel com QueueHandler

**Objetivo:** Mostrar log em tempo real na janela.

**Design:**

1. **QueueHandler** (adicionado ao logging system em `main.py`):
```python
import logging
import queue

class QueueLogHandler(logging.Handler):
    """Handler que envia log records para uma queue."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self._queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self._queue.put_nowait(msg)
        except queue.Full:
            pass  # descarta se queue cheia (evita backpressure)
```

2. **Log panel** no GUI: `ScrolledText` widget que le da queue a cada 100ms via `root.after()`.

3. **Queue size:** 1000 mensagens max (ring buffer semantics — descarta velhas).

**Alteracoes em `src/main.py`:**
- Criar `queue.Queue(maxsize=1000)` no setup
- Adicionar `QueueLogHandler` ao logging
- Passar queue para o GUI

**Criterio de aceite:**
- [ ] Log aparece em tempo real na janela
- [ ] Scroll automatico para o final
- [ ] Performance OK com muitas mensagens (>1000 linhas)
- [ ] Queue nao bloqueia o logger se GUI estiver lento
- [ ] Se GUI nao esta aberto, queue descarta mensagens antigas

### GUI-03 — Barra de Controles

**Objetivo:** Botoes e dropdowns para controlar o app pela janela.

**Layout:**
```
+-------------------------------------------------------+
|  [  GRAVAR  ]  | Profile: [dropdown] | Modo: [dropdown] |
|                 | Modelo:  [dropdown] |                  |
+-------------------------------------------------------+
|                                                         |
|  [Log panel - ScrolledText]                            |
|                                                         |
+-------------------------------------------------------+
|  Estado: Idle  |  Modelo: large-v3  |  Profile: Tech   |
+-------------------------------------------------------+
```

**Controles:**
- **Botao Gravar:** Grande, toggles recording (equivale a Ctrl+Alt+H press/release). Muda de cor: verde (idle) -> vermelho (gravando).
- **Dropdown Profile:** Lista todos os profiles. Ao mudar, chama callback `on_profile_change`.
- **Dropdown Modo:** Scribe / Translate / Voice. Chama `on_mode_change`.
- **Dropdown Modelo:** Lista modelos Whisper. Chama `on_model_change`.

**Sincronizacao:** Quando o usuario muda algo pelo tray menu, o GUI deve refletir. Usar um metodo `update_state()` que o SpeedOsper chama.

**Criterio de aceite:**
- [ ] Botao Gravar inicia/para gravacao
- [ ] Botao muda de cor com o estado
- [ ] Dropdowns refletem estado atual
- [ ] Mudar dropdown no GUI atualiza o tray menu
- [ ] Mudar no tray menu atualiza o dropdown no GUI
- [ ] Todos os callbacks funcionam corretamente

### GUI-04 — Status Bar + Tray Integration

**Objetivo:** Barra de status inferior e double-click no tray para abrir/fechar.

**Status bar:**
- Label esquerda: estado atual (Idle / Gravando / Transcrevendo / Pronto / Reproduzindo)
- Label centro: modelo ativo
- Label direita: profile ativo

**Tray integration:**
- Double-click no icone do tray chama `gui.toggle()`
- Requer alteracao em `tray.py` para capturar evento de double-click no pystray

**Nota sobre pystray:** O pystray no Windows suporta `on_activate` que e chamado no double-click. Ja existe suporte nativo.

**Alteracoes em `src/tray.py`:**
- Adicionar callback `on_activate` (double-click) ao `pystray.Icon()`
- Passar callback para o GUI toggle

**Alteracoes em `src/main.py`:**
- Conectar `tray.on_activate` -> `gui.toggle()`

**Criterio de aceite:**
- [ ] Status bar mostra estado/modelo/profile corretos
- [ ] Status atualiza em tempo real quando estado muda
- [ ] Double-click no tray abre a janela
- [ ] Double-click novamente fecha a janela
- [ ] Janela inicia escondida (so aparece com double-click)

### GUI-05 — Dark Theme + Polimento

**Objetivo:** Visual escuro e limpo.

**Cores:**
```python
DARK_BG = "#1e1e1e"      # fundo principal (VS Code style)
DARK_SURFACE = "#252526"  # fundo de widgets
DARK_BORDER = "#3c3c3c"   # bordas
TEXT_PRIMARY = "#cccccc"   # texto principal
TEXT_SECONDARY = "#808080" # texto secundario
ACCENT = "#007acc"         # azul de destaque
RECORD_RED = "#f44336"     # vermelho do botao gravar
```

**Detalhes:**
- `ScrolledText` com fundo escuro, texto claro, fonte monospacada (Consolas/Cascadia Code)
- Botao gravar com borda arredondada (se tkinter permitir, senao retangular com padding)
- Dropdowns com estilo dark (ttk theme customizado)
- Status bar com fundo mais escuro que o body
- Titulo e bordas da janela seguem tema do Windows (nao controlavel por tkinter)

**Criterio de aceite:**
- [ ] Janela tem visual dark consistente
- [ ] Texto legivel em todos os widgets
- [ ] Contraste suficiente para acessibilidade
- [ ] Fonte monospacada no log panel
- [ ] Visual nao conflita com temas de alto contraste do Windows

---

## Grafo de Dependencias

```
PRF-01 (profiles module)
   |
   v
PRF-02 (built-in profiles)
   |
   v
PRF-03 (transcriber integration)              ICO-01 (microphone icon)
   |                                              |
   v                                              |
PRF-04 (tray profile selector)                    |
   |                                              |
   v                                              |
PRF-05 (code mode as profile)                     |
   |                                              |
   v                                              |
GUI-01 (janela basica tkinter)                    |
   |                                              |
   v                                              |
GUI-02 (log panel + QueueHandler)                 |
   |                                              |
   v                                              |
GUI-03 (controles: gravar, dropdowns)             |
   |                                              |
   +------------------+---------------------------+
                      |
                      v
               GUI-04 (status bar + tray double-click)
                      |
                      v
               GUI-05 (dark theme)
```

ICO-01 e independente de PRF-* e pode ser feito em paralelo.
GUI-04 depende de ICO-01 apenas para garantir que o icone final esta pronto antes do polish.

---

## Estimativa de Esforco

| Sprint | Tasks | Complexidade total | Sessoes estimadas |
|---|---|---|---|
| Sprint 11 | PRF-01 a PRF-05, ICO-01 | Media | 2-3 sessoes |
| Sprint 12 | GUI-01 a GUI-05 | Alta | 3-4 sessoes |
| **Total** | **11 tasks** | — | **5-7 sessoes** |

---

## Riscos e Mitigacoes

| Risco | Impacto | Mitigacao |
|---|---|---|
| tkinter nao e thread-safe — crash se chamar de outra thread | Alto | Disciplina rigorosa: toda interacao via `root.after()`. Documentar no codigo. |
| tkinter dark theme fica feio / inconsistente | Medio | ttk com tema custom. Se inaceitavel, considerar CustomTkinter (1 dependencia extra). |
| pystray double-click nao funciona em todas as versoes do Windows | Baixo | Testar em Win 10 e 11. Fallback: item "Abrir janela" no menu. |
| Profile .txt com encoding errado (usuario salva em ANSI) | Medio | Ler com `encoding="utf-8"`, fallback para `latin-1`. Documentar que deve ser UTF-8. |
| Muitos profiles no menu tornam navegacao lenta | Baixo | Limitar exibicao a 20 profiles. Ordenar: built-in primeiro, depois custom por nome. |
| QueueHandler perde mensagens se queue cheia | Baixo | Aceitavel — log de arquivo continua completo. GUI e apenas visualizacao. |
| Botao gravar no GUI vs hotkey geram race condition | Medio | Usar lock no recorder.start()/stop(). Ou: botao apenas simula a hotkey. |
| Remocao de Ctrl+Alt+C quebra muscle memory de usuarios | Baixo | Reaproveitar Ctrl+Alt+C para ciclar profiles, ou manter como atalho para profile "Code Mode". |

---

## Impacto em Arquivos Existentes

| Arquivo | Tipo de alteracao | Sprint |
|---|---|---|
| `src/profiles.py` | NOVO | 11 |
| `src/gui.py` | NOVO | 12 |
| `src/config.py` | Modificar: remover code_mode bool, adicionar active_profile_name | 11 |
| `src/transcriber.py` | Modificar: prompt dinamico via profile | 11 |
| `src/tray.py` | Modificar: profile selector, icone microfone, double-click | 11-12 |
| `src/main.py` | Modificar: profile management, GUI integration, QueueHandler | 11-12 |

---

## Ordem de Implementacao Recomendada

1. **ICO-01** — Independente, pode comecar imediatamente. Quick win visual.
2. **PRF-01** — Fundacao do sistema de profiles.
3. **PRF-02** — Bootstrap dos built-in (testavel com unit tests).
4. **PRF-03** — Integrar no transcriber (primeiro teste funcional).
5. **PRF-04** — UI no tray (primeiro teste de UX).
6. **PRF-05** — Migracao final do code_mode.
7. **GUI-01** — Janela basica (testavel isoladamente).
8. **GUI-02** — Log panel (primeira utilidade real da janela).
9. **GUI-03** — Controles (janela funcional completa).
10. **GUI-04** — Integracao com tray.
11. **GUI-05** — Polish final.

Cada task e testavel isoladamente. PRF-01 a PRF-05 nao quebram funcionalidade existente ate PRF-04 (que troca o menu). GUI-01 a GUI-05 sao 100% aditivos — nada quebra se a janela nao for aberta.

---

*Plano criado por: Planner Agent | 2026-03-26*
