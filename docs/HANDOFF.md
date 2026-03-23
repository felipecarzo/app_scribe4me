# HANDOFF — Estado atual do projeto app_speedosper

> Arquivo vivo. Sobrescrito ao final de cada sessao, por qualquer agente.
> **Nao e um diario** — nao acumula historico. Para historico, ver `docs/daily/`.
> Qualquer agente (Claudio ou Antigravity) le este arquivo antes de qualquer acao.
> **Sempre validar contra `git status` + `git log` antes de confiar nas pendencias listadas aqui.**

---

## Meta
- **Ultima atualizacao:** 2026-03-22 — Inicio do projeto, reescrita de docs de governanca
- **Agente que escreveu:** Claudio
- **Maquina:** ALIENWARE-LIPE
- **Branch atual:** `master`
- **Ultimo commit:** `14d1727` — chore(infra): setup inicial a partir do projeto-template

---

## Task em andamento
- **ID:** SET-01
- **Descricao:** Criar estrutura de pastas (src/, scripts/) e requirements.txt
- **Status:** pendente — nenhum codigo-fonte existe ainda

---

## Proximo passo exato
1. Rodar `git status` e `git log --oneline -3` (protocolo anti-alucinacao)
2. Implementar SET-01: criar `src/` com arquivos vazios (recorder.py, transcriber.py, clipboard.py, main.py, config.py) + `scripts/speedosper.ahk` + `requirements.txt`
3. Apos SET-01, seguir para SET-02 (venv + instalar dependencias) e SET-03 (config.py)

---

## Arquivos a ler no inicio da sessao
```text
CLAUDE.md
docs/ROADMAP.md
docs/HANDOFF.md
```

---

## Contexto critico
- Projeto recem-criado. Apenas governanca (template) existe no repo.
- Stack: Python 3.12 + Whisper (openai-whisper) + AutoHotKey + CUDA
- Objetivo: substituir Win+H nativo por transcricao precisa com Whisper local
- Alienware com GPU dedicada — Whisper roda local com CUDA
- Session files em `docs/session/` sao do projeto anterior (app_ayvu) — podem ser removidos

---

## Branches ativas

| Branch | Tipo | Ultimo commit | Estado |
|---|---|---|---|
| `master` | desenvolvimento ativo | `14d1727` | Sprint 0 — setup |

---

## Estado do ROADMAP (Sprint 0 — em progresso)

| ID | Task | Status |
|---|---|---|
| SET-01 | Criar estrutura de pastas e requirements.txt | ⏳ |
| SET-02 | Configurar ambiente Python | 🔒 |
| SET-03 | Criar config.py | 🔒 |
