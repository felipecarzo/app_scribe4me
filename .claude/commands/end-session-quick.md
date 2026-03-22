---
name: end-session-quick
description: Encerramento rápido — apenas HANDOFF + daily + commit. Para sessões curtas ou exploratórias sem entrega de código.
---

Você é o Scrum Master do projeto Speedosper no modo rápido. Use este comando em sessões **sem entrega de código** — discussão, análise, reorganização, planejamento. Se houve código entregue, use `/end-session` completo.

---

## PASSO 1 — Estado real do repositório

```bash
git status --short
git log --oneline -3
git branch --show-current
```

---

## PASSO 2 — Atualizar diário (`docs/daily/YYYY-MM-DD.md`)

Adicione uma entrada para esta sessão (append — nunca sobrescreva):

```markdown
### Sessão N — <título resumido>

- <bullet do que foi discutido/decidido>
- Nenhuma implementação — ROADMAP sem alterações
```

---

## PASSO 3 — Atualizar HANDOFF (`docs/HANDOFF.md`)

Sobrescreva completamente com o estado atual. Campos obrigatórios:

- `Meta`: data de hoje, agente, máquina, hash do último commit
- `Task em andamento`: próxima task real (não a que acabou de ser discutida)
- `Próximo passo exato`: instruções claras para o próximo agente
- Se houve decisão estrutural nesta sessão, documente em uma seção extra

---

## PASSO 4 — Relatório e commit

Apresente ao usuário:

```
ENCERRAMENTO RÁPIDO — <data>

Diário:   ✅ atualizado
HANDOFF:  ✅ atualizado

Arquivos a commitar:
- docs/HANDOFF.md
- docs/daily/<data>.md
- <outros modificados na sessão>

Mensagem de commit proposta:
  docs(session): encerramento <YYYY-MM-DD> — <resumo>
```

**Aguarde aprovação do usuário antes de commitar.**

Após aprovação:

```bash
git add docs/HANDOFF.md docs/daily/<data>.md
# adicione outros arquivos modificados
git commit -m "docs(session): encerramento <YYYY-MM-DD> — <resumo>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push origin <branch>
git log --oneline -3
```

---

## Regras

- **Use apenas para sessões sem código entregue** — se houve código, use `/end-session`
- **HANDOFF sempre vai no commit** — é a ponte entre máquinas e agentes
- **Nunca commite sem aprovação explícita do usuário**
- ROADMAP e MEMORY não são verificados neste modo — se perceber que estão desatualizados, alerte o usuário e sugira `/end-session` completo
