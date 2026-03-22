---
name: start-session
description: Inicia sessão de trabalho — Step 0 Anti-Alucinação + leitura do HANDOFF + apresentação do próximo passo
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git branch:*)
---

Você está iniciando uma sessão de trabalho no projeto Speedosper. Execute os passos abaixo em ordem antes de qualquer outra ação.

---

## PASSO 1 — Step 0 Anti-Alucinação

Execute os comandos obrigatórios:

```bash
git status --short
git log --oneline -5
git branch --show-current
```

Registre mentalmente:
- Branch atual
- Hash do último commit
- Arquivos modificados/staged (se houver)

> O código real vence os documentos. O HANDOFF pode estar errado; o git nunca mente.

---

## PASSO 2 — Leitura do HANDOFF

Leia `docs/HANDOFF.md` e extraia:
- `Task em andamento` (o que foi deixado para esta sessão)
- `Próximo passo exato` (instrução deixada pelo agente anterior)
- `Meta` (data, agente, hash — para comparar com o git log)

Se o hash do HANDOFF divergir do `git log`, **priorize o git** e avise o usuário.

---

## PASSO 3 — Relatório de início

Apresente ao usuário um resumo neste formato:

```
INÍCIO DE SESSÃO — <data de hoje>

Branch:       <branch atual>
Último commit: <hash> — <mensagem> (<data relativa>)
Working tree: <limpa | N arquivo(s) modificado(s)>

HANDOFF diz:
  Task:   <task em andamento>
  Passo:  <próximo passo exato>

Pronto para começar.
```

Se houver arquivos modificados não commitados, liste-os e pergunte ao usuário se quer tratá-los antes de continuar.

---

## Regras

- **Nunca pule o Step 0** — é o protocolo Anti-Alucinação
- **Nunca confie só no HANDOFF** — valide sempre contra o git
- Após este comando, aguarde instrução do usuário para começar a trabalhar
