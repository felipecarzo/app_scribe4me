# Referências do Projeto app_ayvu

> Índice de documentação de referência. Documentos nesta pasta são para leitura humana — não são lidos automaticamente por agentes.

---

## Documentos disponíveis

| Arquivo | Conteúdo | Audiência |
|---|---|---|
| `backlog.md` | Backlog Scrum completo — épicos, user stories, critérios de aceitação | Felipe / PO |
| `implementation_plan.md` | Plano de implementação por sprint — detalhes técnicos de cada task | Desenvolvedores |
| `technology_guide.md` | Guia do desenvolvedor — setup, arquitetura, padrões, decisões técnicas | Desenvolvedores |
| `scrum_geral.md` | Processo Scrum — papéis, cerimônias, DoD, branching | Time |

---

## O que NÃO fica aqui

- **`docs/ROADMAP.md`** — fica na raiz de `docs/` porque é lido por agentes automaticamente
- **`docs/HANDOFF.md`** — fica na raiz de `docs/` porque é o arquivo vivo da sessão
- **`docs/essential/`** — documentação lida por agentes (agents-guide, multi-integration)
- **`docs/chitchat/`** — comunicação inter-agentes
- **`docs/session/`** — arquivos efêmeros por task (Planner → Tester → Revisor)
- **`docs/daily/`** — diários criados automaticamente pelo Scrum Manager

---

## Como criar um novo documento de referência

1. Crie o arquivo em `docs/reference/`
2. Adicione uma entrada na tabela acima
3. Indique claramente a audiência (Felipe / Desenvolvedores / Time)
4. Não inclua informação que deva ser lida por agentes — isso vai em `docs/essential/`
