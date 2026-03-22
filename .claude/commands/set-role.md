# /set-role — Ativar um role para a instância

Uso: `/set-role <role-name>`

Exemplo: `/set-role qa-engineer`

## Roles disponíveis

- `eddie-morra` — Orquestrador (NTZ-48). Acesso total + git push/pull.
- `senior-dev` — Backend. Workspace: src/, scripts/, tests/. Sem git push/pull.
- `ui-engineer` — Frontend. Workspace: frontend/, tests/. Sem git push/pull.
- `fullstack` — Front + Back. Workspace: src/, scripts/, tests/, frontend/. Sem git push/pull.
- `qa-engineer` — Tester. Workspace: tests/, docs/session/. Sem git push/pull.
- `tech-writer` — Pesquisa & Docs. Workspace: docs/, research/ (exceto ROADMAP/HANDOFF). Sem git push/pull.
- `data-analyst` — Cientista de dados. Workspace: docs/research/, reports/, data/analysis/. Sem git push/pull.
- `observer` — Monitor (somente leitura). Workspace: docs/LIVE_STATUS.md apenas.

## O que `/set-role` faz

1. Lê `.claude/roles/<role-name>.json`
2. Cria `.claude/instance-role.local.json` (gitignored, local)
3. Registra a mudança em `docs/LIVE_STATUS.md`
4. Exibe permissões e restrições do role
5. Adiciona `prompt_addition` ao contexto da sessão

## Guardião de Workspace

Após ativar um role, o hook `PreToolUse` intercepta tentativas de Edit/Write/Bash fora do workspace permitido e bloqueia com erro.

## Exemplo

```bash
/set-role qa-engineer
```

Resultado:
```
[OK] Role ativado: QA ENGINEER — Tester

Workspace Write:  tests/, docs/session/
Workspace Read:   * (tudo)
Git Commit:       [OK] Permitido
Git Push/Pull:    [NO] Bloqueado
Agentes:          tester, reviewer

Aviso: Você não pode editar arquivos fora de tests/ e docs/session/
```

## Como usar em paralelo

- **Terminal 1 (Felipe + Cláudio):** `/set-role eddie-morra` (ou sem role)
- **Terminal 2 (QA):** `/set-role qa-engineer`
- **Terminal 3 (Docs):** `/set-role tech-writer`

Cada terminal tem isolamento. O stop hook só dispara em eddie-morra.

## Limpando o role (resetar para sem restrição)

Delete o arquivo `.claude/instance-role.local.json`:
```bash
rm .claude/instance-role.local.json
```
