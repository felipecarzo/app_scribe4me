# app_ayvu — ROADMAP

> Documento de referência central para acompanhamento de progresso entre sessões e dispositivos.
> Atualizado manualmente após conclusão de cada task.
> **Branch de referência deste arquivo:** `{branch}` (ver seção Branches abaixo)

---

## Branches

| Branch | Tipo | Último commit | Estado |
|---|---|---|---|
| `main` | release estável | `{hash}` | {ex: MVP v0.1.0 — congelada até próximo release} |
| `develop` | desenvolvimento ativo | `{hash}` | {ex: Pós-MVP — sprint N em andamento} |

**Regra:** todo código novo vai para `develop`. Merge em `main` apenas em releases formais (tag vX.Y.Z).
**ROADMAP:** mantido em `develop`; `main` recebe cópia atualizada no momento do merge.

> **Como usar:** ao criar branch `develop`, preencher os `{hash}` e estados acima.
> Atualizar a cada encerramento de sessão (`/end-session`) ou release.

---

## Legenda de status

| Simbolo | Significado |
|---|---|
| ✅ | Concluido e commitado |
| 🟡 | Parcialmente feito |
| 🔒 | Bloqueado por dependência |
| ⏳ | Pendente (desbloqueado) |
| 🏗️ | Em progresso |

> IDs sem sufixo = motor/infra. IDs com `-FL` = Flutter. IDs com `-BK` = backend.

---

## Checkpoints de Qualidade

| ID | Checkpoint | Status | Critério de entrada | Responsável |
|---|---|---|---|---|
| VIS-01 | Revisão Visual — Antigravity | 🔒 | Tema global ✅ **E** >= 6 telas implementadas | Antigravity |

---

## Sprint 0 — Setup e Scaffolding ✅ CONCLUÍDA

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| INF-01 | Instalar Flutter + Rust + ferramentas | ✅ | — | INF-02, INF-03 |
| INF-02 | Scaffold Flutter app (estrutura base) | ✅ | INF-01 | TRANS-01-FL |
| INF-03 | Scaffold Rust motor (crate + lib.rs) | ✅ | INF-01 | MOT-01 |
| INF-04 | Configurar flutter_rust_bridge (FFI) | ✅ | INF-02, INF-03 | MOT-01, TRANS-01-FL |
| INF-05 | Copiar legacy e documentar referências | ✅ | — | — |
| INF-06 | Preencher CLAUDE.md + docs do projeto | ✅ | — | — |
| INF-07 | Configurar Antigravity para o projeto | ✅ | INF-06 | VIS-01 |

---

## Sprint 1 — Motor Core (Encoder/Decoder Semântico) — PROXIMA

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| MOT-01 | Encoder semântico: texto -> vetor de intenção | ✅ | INF-03, INF-04 | MOT-02 |
| MOT-02 | Decoder: vetor de intenção -> texto (PT-BR <-> EN) | ✅ | MOT-01 | MOT-03 |
| MOT-03 | Cache semântico (similaridade coseno, lookup/store) | ✅ | MOT-02 | MOT-04 |
| MOT-04 | Validação de qualidade (embedding source vs target) | ✅ | MOT-03 | TRANS-01-FL |
| MOT-05 | Benchmark: motor Rust vs NLLB-200 Python (legacy) | ⏳ | MOT-02 | — | <!-- Rust concluído (94.2% pass rate, 413ms média, quality 0.915); aguardando python_results.json para relatório comparativo final --> |

---

## Sprint 2 — App Core (Flutter + Tradução Texto)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| TRANS-01-FL | Tela de tradução texto (input -> motor -> output) | ✅ | INF-04, MOT-04 | TRANS-02-FL |
| TRANS-02-FL | Seletor de idiomas (PT-BR, EN, ES + expansão) | ⏳ | TRANS-01-FL | P2P-01 | <!-- PT/EN/ZH já implementados em TRANS-01-FL. Escopo redefinido: adicionar ES e/ou expandir idiomas — confirmar com Felipe quais idiomas priorizar --> |
| TRANS-03-FL | Histórico de traduções (SQLite local) | 🔒 | TRANS-01-FL | — |
| SET-01-FL | Tela de configurações | 🔒 | TRANS-01-FL | — |

---

## Sprint 3 — Comunicação P2P (Bluetooth + WiFi Direct)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| P2P-01 | Protocolo de transmissão: vetor semântico compacto | 🔒 | MOT-04 | P2P-02, P2P-03 |
| P2P-02 | Bluetooth: discovery + pairing + transmissão | 🔒 | P2P-01 | P2P-04 |
| P2P-03 | WiFi Direct: discovery + conexão + transmissão | 🔒 | P2P-01 | P2P-04 |
| P2P-04 | Teste real: 2 devices traduzindo texto P2P | 🔒 | P2P-02, P2P-03 | VOZ-01 |
| PAIR-01-FL | Tela de pareamento (scan + connect) | 🔒 | P2P-02 | P2P-04 |

---

## Sprint 4 — Voz (STT + TTS On-Device)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| VOZ-01 | STT on-device (Whisper.cpp ou Vosk via Rust) | 🔒 | P2P-04 | VOZ-02 |
| VOZ-02 | TTS on-device (Piper TTS via Rust) | 🔒 | VOZ-01 | VOZ-03 |
| VOZ-03 | Pipeline completo: fala -> intenção -> P2P -> fala | 🔒 | VOZ-02 | PROS-01 |
| VOZ-04-FL | UI de conversa por voz (chat bubbles, controles) | 🔒 | VOZ-01 | VOZ-03 |

---

## Sprint 5 — Prosódia (Diferencial Patenteável)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| PROS-01 | Extração prosódica: pitch, energia, ritmo, duração | 🔒 | VOZ-03 | PROS-02 |
| PROS-02 | Incluir prosódia no vetor semântico transmitido | 🔒 | PROS-01 | PROS-03 |
| PROS-03 | TTS expressivo: aplicar prosódia na síntese | 🔒 | PROS-02 | LIC-01 |
| PROS-04 | Predição de intenção (contexto + prosódia) | 🔒 | PROS-01 | PROS-03 |

---

## Sprint 6 — Licenciamento e Negócio

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| LIC-01-BK | API de validação de licença (check periódico) | 🔒 | PROS-03 | LIC-02-FL |
| LIC-02-FL | Integração de licença no app (freemium) | 🔒 | LIC-01-BK | BETA-01 |
| LIC-03 | Hardware binding (device ID) | 🔒 | LIC-01-BK | — |

---

## Sprint 7 — Beta e Polimento

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| BETA-01 | Testes com usuários reais | 🔒 | LIC-02-FL | BETA-02 |
| BETA-02 | Performance tuning (latência, bateria, memória) | 🔒 | BETA-01 | BETA-03 |
| BETA-03 | Preparar para loja (Play Store / App Store) | 🔒 | BETA-02 | — |

---

## Fases do Produto (visão macro)

| Fase | Escopo | Sprints |
|---|---|---|
| **Fase 1** — Motor + App texto | Tradução texto P2P offline, 3 idiomas | 0-3 |
| **Fase 2** — Voz + Prosódia | Pipeline voz completo com preservação emocional | 4-5 |
| **Fase 3** — Produto comercial | Licenciamento, beta, lojas | 6-7 |
| **Fase 4** — SDK B2B | Motor como SDK licenciável para terceiros | pós-MVP |

---

*Última atualização: 2026-03-14 — Sprint 1/2 em progresso: MOT-01 ✅ MOT-02 ✅ MOT-03 ✅ MOT-04 ✅ MOT-05 ⏳ (Rust concluído, Python pendente). TRANS-01-FL ✅. Próxima: TRANS-02-FL (escopo a confirmar com Felipe) ou TRANS-03-FL.*
