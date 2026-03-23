# app_speedosper — ROADMAP

> Documento de referencia central para acompanhamento de progresso entre sessoes e dispositivos.
> Atualizado manualmente apos conclusao de cada task.

---

## Branches

| Branch | Tipo | Ultimo commit | Estado |
|---|---|---|---|
| `master` | desenvolvimento ativo | `14d1727` | Setup inicial — Sprint 0 em andamento |

---

## Legenda de status

| Simbolo | Significado |
|---|---|
| ✅ | Concluido e commitado |
| 🟡 | Parcialmente feito |
| 🔒 | Bloqueado por dependencia |
| ⏳ | Pendente (desbloqueado) |
| 🏗️ | Em progresso |

---

## Sprint 0 — Setup e Estrutura

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| SET-01 | Criar estrutura de pastas (src/, scripts/) e requirements.txt | ✅ | — | SET-02, SET-03 |
| SET-02 | Configurar ambiente Python (venv, instalar whisper + dependencias) | ✅ | SET-01 | REC-01 |
| SET-03 | Criar config.py (modelo large, idioma pt, hotkey Ctrl+H, modos de saida) | ✅ | SET-01 | REC-01, TRS-01, AHK-01 |

---

## Sprint 1 — Core (Gravacao + Transcricao + Saida)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| REC-01 | Gravacao de audio do microfone (recorder.py) — start/stop controlado | ✅ | SET-02, SET-03 | TRS-01 |
| TRS-01 | Transcricao com Whisper large, pt-BR, pontuacao real (transcriber.py) | ✅ | REC-01 | OUT-01 |
| OUT-01 | Saida de texto — dois modos: colar no cursor OU copiar pro clipboard (clipboard.py) | ✅ | TRS-01 | ORC-01 |
| ORC-01 | Orquestrador main.py — conecta gravacao -> transcricao -> saida | ✅ | OUT-01 | AHK-01 |

---

## Sprint 2 — Integracao (Hotkey + Modos + E2E)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| AHK-01 | Script AHK: Win+H push-to-talk + Win+Shift+H toggle (substitui Win+H nativo) | ✅ | ORC-01, SET-03 | E2E-01 |
| AHK-02 | Seletor de modo de saida (cursor direto vs clipboard) via config ou hotkey | ✅ | AHK-01 | E2E-01 |
| E2E-01 | Teste end-to-end: hotkey -> gravacao -> Whisper -> texto aparece | ⏳ | AHK-01, AHK-02 | POL-01 |

---

## Sprint 3 — Polimento e Otimizacao

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| POL-01 | Otimizacao de latencia (warm-up do modelo, CUDA tuning) | 🔒 | E2E-01 | POL-02 |
| POL-02 | Feedback visual (tray icon ou indicador: gravando/transcrevendo/pronto) | 🔒 | POL-01 | — |
| POL-03 | Pos-processamento de pontuacao (se Whisper large nao for suficiente) | 🔒 | E2E-01 | — |

---

## Fases do Produto (visao macro)

| Fase | Escopo | Sprints |
|---|---|---|
| **Fase 1** — MVP funcional | Ctrl+H -> grava -> Whisper large -> texto no cursor/clipboard | 0-2 |
| **Fase 2** — Polimento | Latencia otimizada, feedback visual, pontuacao refinada | 3 |
| **Fase 3** — Extras | Multi-idioma, comandos por voz, historico | pos-MVP |

---

*Ultima atualizacao: 2026-03-22 — Sprint 0 ✅, Sprint 1 ✅, Sprint 2 em progresso. AHK-01 ✅, AHK-02 ✅. Proximo: E2E-01.*
