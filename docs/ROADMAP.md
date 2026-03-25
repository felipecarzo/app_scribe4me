# app_speedosper — ROADMAP

> Documento de referencia central para acompanhamento de progresso entre sessoes e dispositivos.
> Atualizado manualmente apos conclusao de cada task.

---

## Branches

| Branch | Tipo | Ultimo commit | Estado |
|---|---|---|---|
| `master` | desenvolvimento ativo | `fa999c1` | Fase 1+2 completas — MVP funcional + polimento |

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
| E2E-01 | Teste end-to-end: hotkey -> gravacao -> Whisper -> texto aparece | ✅ | AHK-01, AHK-02 | POL-01 |

---

## Sprint 3 — Polimento e Otimizacao

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| POL-01 | Otimizacao de latencia (warm-up do modelo, CUDA tuning) | ✅ | E2E-01 | POL-02 |
| POL-02 | Feedback visual (tray icon ou indicador: gravando/transcrevendo/pronto) | ✅ | POL-01 | — |
| POL-03 | Pos-processamento de pontuacao (se Whisper large nao for suficiente) | ✅ | E2E-01 | — |

---

---

# SCRIBE4ME v2 — Motor Ayvu

> Plano completo em `docs/SCRIBE4ME_V2_PLAN.md`

---

## Sprint 4 — Fase 0: C-ABI do Motor Ayvu

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| FFI-01 | Criar `ffi.rs` no motor ayvu — funcoes `extern "C"` wrapping `api.rs` | ✅ | — | FFI-02 |
| FFI-02 | Cargo config cdylib (ja feito) + build release gerando `motor_ayvu.dll` | ✅ | FFI-01 | FFI-03 |
| FFI-03 | Testes de integracao Python ↔ Rust via ctypes | ✅ | FFI-02 | INT-01 |

**Local:** `D:\Documentos\Ti\projetos\app_ayvu\motor\`
**Criterio de aceite:** Python carrega a DLL e chama `scribe_motor_version()` com sucesso.

---

## Sprint 5 — Fase 1: Integracao basica (modo Scribe via motor)

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| INT-01 | Criar `src/motor_bridge.py` — wrapper ctypes para motor_ayvu.dll | ✅ | FFI-03 | INT-02 |
| INT-02 | Refatorar `transcriber.py` — chamar motor_bridge ao inves de faster-whisper | ✅ | INT-01 | INT-03 |
| INT-03 | Remover faster-whisper do requirements.txt e imports | ✅ | INT-02 | INT-04 |
| INT-04 | Config: path da DLL + warm-up via motor | ✅ | INT-02 | INT-05 |
| INT-05 | Testes de regressao — todos os test modules passam com novo backend | ✅ | INT-03 | TRN-01 |

**Criterio de aceite:** Push-to-talk funciona identico ao v1, usando Whisper do motor ayvu.

---

## Sprint 6 — Fase 2: Modo Translate

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| TRN-01 | Config: `target_language` e `mode` enum (scribe/translate/voice) | ✅ | INT-05 | TRN-02 |
| TRN-02 | Orquestrador de modo em `main.py` — despacha pipeline por modo | ✅ | TRN-01 | TRN-03 |
| TRN-03 | Tray: seletor de modo + seletor de idioma alvo no menu | ✅ | TRN-02 | TRN-04 |
| TRN-04 | Output traduzido no cursor/clipboard | ✅ | TRN-03 | TRN-05 |
| TRN-05 | Testes end-to-end modo translate | ✅ | TRN-04 | VOZ-01 |

**Criterio de aceite:** Fala em PT, texto traduzido em EN aparece no cursor.

---

## Sprint 7 — Fase 3: Modo Voice + Polimento final

| ID | Task | Status | Depende de | Desbloqueia |
|---|---|---|---|---|
| VOZ-01 | `src/player.py` — playback de PCM f32 via sounddevice | ⏳ | TRN-05 | VOZ-02 |
| VOZ-02 | Pipeline voice completo: voz -> texto -> traducao -> TTS -> play | 🔒 | VOZ-01 | VOZ-03 |
| VOZ-03 | Tray: estado PLAYING + config auto-play | 🔒 | VOZ-02 | BLD-01 |
| BLD-01 | PyInstaller spec com motor_ayvu.dll bundled | 🔒 | VOZ-03 | BLD-02 |
| BLD-02 | First-run: download de modelos ONNX com progress bar | 🔒 | BLD-01 | BLD-03 |
| BLD-03 | Installer atualizado + testes em maquina limpa | 🔒 | BLD-02 | — |

**Criterio de aceite:** Fala em PT, ouve traducao em EN. Installer funcional.

---

## Fases do Produto (visao macro)

| Fase | Escopo | Sprints | Estado |
|---|---|---|---|
| **v1 Fase 1** — MVP funcional | Ctrl+Alt+H -> grava -> Whisper -> texto | 0-2 | ✅ |
| **v1 Fase 2** — Polimento | Latencia, tray icon, pontuacao | 3 | ✅ |
| **v1 Fase 3** — Migracao faster-whisper | CTranslate2, CUDA fallback, open source | pos-3 | ✅ |
| **v2 Fase 0** — C-ABI motor ayvu | ffi.rs, DLL, testes Python↔Rust | 4 | ✅ |
| **v2 Fase 1** — Integracao motor | Substituir faster-whisper pelo motor | 5 | ✅ |
| **v2 Fase 2** — Modo Translate | Transcricao + traducao NLLB-200 | 6 | ✅ |
| **v2 Fase 3** — Modo Voice + Build | TTS + prosodia + installer final | 7 | ⏳ |

---

*Ultima atualizacao: 2026-03-25 — Sprint 6 concluido (Fase 2 — modo translate ✅). Proximo: Sprint 7 (Fase 3 — modo voice + build).*
