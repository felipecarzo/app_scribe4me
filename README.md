# projeto-template — Sistema de Agentes IA para Desenvolvimento

Template completo para projetos com Claude Code (Claudio) + agente secundário (ex: Antigravity/Gemini).
Inclui pipeline de qualidade multi-agente, protocolo de handoff e documentação de integração.

---

## Como usar este template

### 1. Copie o template para o seu projeto

```bash
cp -r projeto-template/. meu-projeto/
cd meu-projeto
git init
```

### 2. Substitua os placeholders

Busque e substitua em todos os arquivos:

| Placeholder | Substituir por | Exemplo |
|---|---|---|
| `Speedosper` | Nome do projeto | `Ahtleta` |
| `D:DocumentosTiprojetospp_speedosper` | Caminho absoluto da raiz | `/home/felipe/Projetos/meu-projeto` |
| `speedosper` | Slug minúsculo sem espaços | `meu_projeto` |
| `D--Documentos-Ti-projetos-app_speedosper` | Slug do path p/ memória | `-home-felipe-Projetos-meu-projeto` |
| `Python 3.12` | Stack do backend | `Node.js 20, TypeScript, Express 4` |
| `TBD` | Stack do frontend | `Flutter 3.11+, Riverpod 2` |
| `D:DocumentosTiprojetospp_speedosper` | Path relativo do backend | `apps/backend` |
| `D:DocumentosTiprojetospp_speedosper` | Path relativo do frontend | `apps/frontend` |
| `pytest` | Comando de testes | `cd apps/backend && npm test` |
| `Claudio` | Nome do agente primário | `Claudio` |
| `Claude Sonnet 4.6` | Modelo do agente primário | `Claude Sonnet 4.6` |
| `Claude Opus 4.6 <noreply@anthropic.com>` | Co-author do agente A | `Claude Sonnet 4.6 <noreply@anthropic.com>` |
| `Antigravity` | Nome do agente secundário | `Antigravity` |
| `Gemini Advanced` | Modelo do agente secundário | `Gemini Advanced` |
| `Google DeepMind` | Empresa do agente B | `Google DeepMind` |
| `Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>` | Co-author do agente B | `Antigravity (Gemini Advanced) <noreply@google.com>` |

Comando para substituir em massa (adapte conforme necessário):
```bash
find . -type f -name "*.md" -o -name "*.json" -o -name "*.sh" | \
  xargs sed -i 's/Speedosper/MeuProjeto/g'
```

### 3. Adapte o CLAUDE.md

O `CLAUDE.md` é o arquivo mais importante — define stack, estrutura, convenções. Preencha com os detalhes reais do seu projeto.

### 4. Adapte o tester.md

O `tester.md` é o agente mais stack-específico. Adapte:
- Framework de testes (Vitest → Jest, pytest, etc.)
- Comandos de teste
- Estrutura de diretórios de teste
- Checklist do frontend (Flutter → React, etc.)

### 5. Configure o hook do Scrum Manager

Em `.claude/settings.json`, atualize o comando do hook com o caminho correto do seu projeto.

Em `.claude/scripts/run-scrum-manager.sh`, atualize as variáveis de configuração no topo do arquivo.

### 6. Crie o MEMORY.md

O sistema de memória fica em `~/.claude/projects/D--Documentos-Ti-projetos-app_speedosper/memory/`. Não está no template — é criado pelo Claude Code automaticamente.

---

## Estrutura do template

```
projeto-template/
├── CLAUDE.md                          # Instruções mestras do projeto
├── .claude/                           # Sistema de agentes do Claudio (Claude Code)
│   ├── settings.json                  # Permissões + hooks
│   ├── agents/
│   │   ├── planner.md                 # Agente: planejamento pre-código
│   │   ├── reviewer.md                # Agente: revisão de código
│   │   ├── tester.md                  # Agente: execução de testes
│   │   └── scrum-manager.md           # Agente: atualização de ROADMAP
│   ├── commands/
│   │   ├── end-session.md             # Skill: encerramento completo
│   │   ├── end-session-quick.md       # Skill: encerramento rápido
│   │   ├── archive-sprint.md          # Skill: poda de sprint
│   │   ├── commit-now.md              # Skill: commit rápido
│   │   └── pull-now.md                # Skill: pull com aprovação
│   └── scripts/
│       └── run-scrum-manager.sh       # Hook automático do Scrum Manager
├── .agents/                           # Sistema de workflows do Antigravity (Gemini)
│   └── workflows/
│       ├── end-session.md             # Workflow: encerramento completo
│       ├── end-session-quick.md       # Workflow: encerramento rápido
│       ├── commit-now.md              # Workflow: commit rápido
│       └── pull-now.md                # Workflow: pull com verificação
├── docs/
│   ├── HANDOFF.md                     # Estado vivo (sobrescrito a cada sessão)
│   ├── ROADMAP.md                     # Tracker de sprints
│   ├── essential/
│   │   ├── agents-guide.md            # Guia teórico de agentes
│   │   └── multi-integration.md       # Protocolo Claudio ↔ Antigravity
│   ├── chitchat/
│   │   ├── claudio-implementations.md     # Rotina do Claudio
│   │   ├── antigravity-implementations.md # Rotina do Antigravity
│   │   └── integration_plan.md            # Plano de integração
│   ├── reference/
│   │   └── README.md                  # Índice de referências
│   ├── session/                       # Arquivos por task (efêmeros)
│   ├── daily/                         # Diários (append-only)
│   └── archive/                       # Sessions arquivadas por sprint
└── README.md                          # Este arquivo
```

---

## O fluxo de trabalho

```
[Planner]  →  plano em docs/session/{TASK-ID}.md
    ↓
[Claudio]  →  implementa o código
    ↓
[Tester]   →  roda testes, atualiza session file
    ↓
[Revisor]  →  revisa código + session + testes
    ↓
[Felipe]   →  aprovação final
    ↓
[Scrum Manager]  →  atualiza ROADMAP + commit
    ↓
[/end-session]   →  HANDOFF + daily + push
```

Leia `docs/essential/agents-guide.md` para a teoria completa.
Leia `docs/essential/multi-integration.md` para o protocolo de handoff.
