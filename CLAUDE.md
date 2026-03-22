# app_speedosper — Claude Code Instructions

## Projeto
Speech-to-text local baseado em Whisper (OpenAI). Substituicao do Win+H nativo por uma solucao com transcricao precisa, pontuacao automatica real, integrada ao workflow do teclado via hotkey.
Raiz: `D:\Documentos\Ti\projetos\app_speedosper`

## Stack
- **Core**: Python 3.12 — Whisper (openai-whisper ou whisper.cpp bindings), gravacao de audio
- **Integracao**: AutoHotKey — hotkey para gravar/transcrever/colar
- **GPU**: CUDA (Alienware com GPU dedicada — Whisper roda local)

## Estrutura
```
src/
  recorder.py          — captura de audio do microfone
  transcriber.py       — interface com Whisper para transcricao
  clipboard.py         — envio do texto transcrito para clipboard/cursor ativo
  main.py              — orquestrador: hotkey -> grava -> transcreve -> cola
  config.py            — configuracoes (modelo, idioma, hotkey, etc.)

scripts/
  speedosper.ahk       — AutoHotKey script para hotkey global

docs/                   — governanca do projeto
```

## Comandos essenciais
```bash
# Testes
pytest

# Rodar
python src/main.py

# Instalar dependencias
pip install -r requirements.txt
```

## Convencoes
- Commits: `type(scope): mensagem` + `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- Testes: pytest (unit)
- Fluxo ideal: botao no teclado -> grava mic -> Whisper transcreve -> texto vai pro clipboard ou direto pro cursor ativo

## Docs de referencia
- `docs/ROADMAP.md` — tracker de sprints (fonte da verdade)
- `docs/essential/agents-guide.md` — guia de agentes e pipeline de qualidade
- `docs/essential/multi-integration.md` — protocolo Claudio <-> Antigravity

## Estado atual
- Sprint atual: Sprint 1
- Proxima task: TK-001 — Setup inicial

---

## Sistema de Agentes

O projeto possui **dois times de agentes** em `.claude/agents/`. Guia completo em `docs/essential/agents-guide.md`.

### Time de Planejamento

| Agente | Arquivo | Quando invocar |
|--------|---------|---------------|
| **Planner** | `planner.md` | Antes de codificar uma task de medio/alto impacto |

O Planner le a task + contexto e escreve `docs/session/{TASK-ID}.md` com o plano.
**Felipe revisa e aprova o plano antes de Claudio comecar a codificar.**

### Time de Qualidade

| Agente | Arquivo | Quando invocar | Ordem |
|--------|---------|---------------|-------|
| **Tester** | `tester.md` | Apos escrever codigo | 1o |
| **Revisor** | `reviewer.md` | Apos o Tester | 2o |
| **Scrum Manager** | `scrum-manager.md` | Quando Felipe aprova a task | 3o (foreground para git; background so para proposicao) |

### Fluxo por task

```
[Opcional] Felipe + Claudio discutem a task
      |
[Planner] le task -> escreve docs/session/{TASK-ID}.md
      |
[Felipe] revisa e aprova o plano
      |
[Claudio] implementa seguindo o plano
      |
[Tester] roda/cria testes -> atualiza docs/session/{TASK-ID}.md
      |
[Revisor] le codigo + session + testes -> relatorio
      |
[Felipe] aprovacao final
      |
[Scrum Manager] atualiza ROADMAP + commit (invocado por Felipe)
```

### Regras obrigatorias

- **Step 0 de Sessao (Protocolo Anti-Alucinacao):** Sempre inicie QUALQUER sessao executando `git status --short` e `git log --oneline -3` de forma autonoma **antes** de agir ou confiar no roteiro. O codigo real vence os documentos.
- **Nunca pule o Tester nem o Revisor** apos modificar arquivos de codigo
- **Tester sempre antes do Revisor** — o Revisor deve ver o resultado dos testes
- **Scrum Manager: apenas quando Felipe aprovar** — background apenas para proposicao (sem Bash/git); quando Felipe aprova e quer execucao, sempre foreground
- **Planner e opcional** para tasks simples (1-2 arquivos, sem decisao arquitetural)
- Se existir `docs/session/{TASK-ID}.md`, **sempre passe o caminho** ao invocar Tester e Revisor
