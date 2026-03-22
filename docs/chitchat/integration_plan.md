# Plano de Implementação da Integração Claudio ↔ Antigravity

> Documento que registra o plano de ativação e configuração do sistema multi-agente para o projeto app_ayvu.
> Dividido entre o que cada agente implementa, explorando seus pontos fortes.

---

## FASE 1: O que o Antigravity implementa

Estas são as rotinas que não dependem do hook automático do Claude e podem ser estabelecidas no ecossistema de infraestrutura:

1. **Criar o Workflow Rápido (`end-session-quick.md`)**:
   - Focado em sessões exploratórias curtas
   - Apenas: `git status` → `HANDOFF` → `git push`

2. **Implantar o Sistema Imunológico (Fallback no `tester.md`)**:
   - Se a infra falhar (banco offline, erro de dependência), o Tester reporta **`SKIP`** em vez de **`FAIL`**
   - Não bloqueia o pipeline de revisão por falha de infra

3. **Gatilhos de Ciclo de Vida (Garbage Collection)**:
   - Definir que o Fechamento de Sprint é o evento gatilho para empacotar `docs/session/` antigos para `docs/archive/SPRINT_XX/`
   - Estabelecer critérios de poda do `MEMORY.md`

4. **Reforçar o Protocolo "Git First"**:
   - Garantir que o Step 0 de qualquer inicialização é puxar `git status` de forma autônoma
   - Documentado em `CLAUDE.md` e nos agents

---

## FASE 2: Iteração e Review

Após a Fase 1:
- Antigravity valida as alterações usando `git status` e lendo os artefatos modificados
- Prepara o HANDOFF para comunicar as alterações ao Claudio

---

## FASE 3: O que o Claudio implementa

O Claudio, sendo mestre de hooks do Claude Code, assume:

1. **Script/Skill Automatizada de Poda de Sprint**:
   - Criar e testar `.claude/commands/archive-sprint.md`
   - Automatizar a migração das sessions para pastas de arquivo

2. **Testes Mínimos de Frontend**:
   - Definir os testes estruturais obrigatórios para o framework frontend do projeto
   - Adicionar à esteira do `tester.md`

3. **Hook do Scrum Manager**:
   - Configurar `.claude/scripts/run-scrum-manager.sh`
   - Testar proteção anti-recursão e anti-concorrência

---

## Status da Implementação

| Item | Responsável | Status |
|---|---|---|
| `end-session-quick.md` | Antigravity | ⏳ |
| Fallback Tester | Antigravity | ⏳ |
| Garbage Collection docs | Antigravity | ⏳ |
| `archive-sprint.md` | Claudio | ⏳ |
| Testes mínimos frontend | Claudio | ⏳ |
| Hook Scrum Manager | Claudio | ⏳ |

---

*Atualizar status à medida que cada item for implementado.*
