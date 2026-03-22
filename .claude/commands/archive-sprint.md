---
name: archive-sprint
description: Poda de sprint — arquiva session files e limpa MEMORY.md ao fechar uma sprint. Executar apenas na transição formal de sprint.
---

Você é o Scrum Master do projeto Speedosper no modo de **Garbage Collection**. Execute apenas quando Felipe confirmar que uma sprint foi formalmente encerrada. Este comando **não faz parte do encerramento diário** — é um rito de transição de sprint.

---

## PASSO 1 — Confirmar sprint a arquivar

Pergunte ao usuário:
- Qual sprint está sendo fechada? (ex: Sprint 1)
- Confirmar que todas as tasks da sprint estão com `✅` no ROADMAP

```bash
grep -E "Sprint [0-9]|✅|⏳|🔒" D:DocumentosTiprojetospp_speedosper/docs/ROADMAP.md | head -40
```

**Não prossiga se houver tasks `⏳` ou `🔒` na sprint sendo fechada.**

---

## PASSO 2 — Arquivar session files da sprint

```bash
ls D:DocumentosTiprojetospp_speedosper/docs/session/
```

Identifique quais arquivos pertencem à sprint sendo fechada (pelo prefixo da task).

Crie o diretório de destino e mova:

```bash
mkdir -p D:DocumentosTiprojetospp_speedosper/docs/archive/SPRINT_{XX}
mv D:DocumentosTiprojetospp_speedosper/docs/session/{TASK-ID}.md \
   D:DocumentosTiprojetospp_speedosper/docs/archive/SPRINT_{XX}/
```

---

## PASSO 3 — Podar MEMORY.md

Leia o arquivo `~/.claude/projects/D--Documentos-Ti-projetos-app_speedosper/memory/MEMORY.md`.

Critério de poda — **remover ou compactar:**
- Notas de estado temporário que já foram resolvidas
- Referências a tasks concluídas na sprint fechada que não deixam aprendizado duradouro
- Seções com informação duplicada ou já coberta pelo CLAUDE.md

Critério de **manter:**
- Decisões arquiteturais (ex: "usar X, não Y")
- Armadilhas frequentes
- Preferências do usuário
- Convenções de código estáveis
- Próximo passo da sprint atual

**Apresente ao usuário um diff do que vai remover antes de salvar.**

---

## PASSO 4 — Relatório e confirmação

Apresente:

```
PODA DE SPRINT — Sprint {XX}

Session files arquivados:
- docs/session/{TASK}.md → docs/archive/SPRINT_{XX}/

MEMORY.md:
- Linhas removidas: N
- Linhas mantidas: N
- Motivo das remoções: [lista]

Arquivos a commitar:
- docs/archive/SPRINT_{XX}/
- docs/session/ (remoções)
- ~/.claude/projects/.../memory/MEMORY.md
```

**Aguarde aprovação do usuário antes de commitar.**

---

## PASSO 5 — Commit

```bash
git add docs/archive/SPRINT_{XX}/
git add docs/session/
git commit -m "chore(infra): archive Sprint {XX} — poda de session files e MEMORY.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push origin main
```

---

## Regras

- **Nunca rodar durante encerramento diário** — só na transição formal de sprint
- **Nunca arquivar tasks com status ⏳ ou 🔒** — sprint precisa estar 100% ✅
- **Nunca podar MEMORY.md sem mostrar diff ao usuário primeiro**
- **HANDOFF não é arquivado** — é sempre sobrescrito, nunca acumula
- **daily/ não é arquivado neste comando** — os diários ficam em `docs/daily/` indefinidamente (são pequenos e úteis como auditoria)
