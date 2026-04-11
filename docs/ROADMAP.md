# ROADMAP — Scribe4me

> Atualizado em: 2026-04-11

---

## Sprint atual — v1.5.x: Polimento e distribuicao

| ID | Task | Status | Notas |
|----|------|--------|-------|
| S5-01 | API backends (OpenAI, Groq, Gemini, Deepgram batch) | CONCLUIDO | v1.5.0 |
| S5-02 | Realtime WebSocket Deepgram + overlay | CONCLUIDO | v1.5.0 |
| S5-03 | Janela de configuracoes unificada (settings_window) | CONCLUIDO | 2026-04-11 |
| S5-04 | Suporte macOS (platform backend + tray main thread + spec + CI) | CONCLUIDO | 2026-04-11 |
| S5-05 | README atualizado (macOS, configuracoes unificadas) | CONCLUIDO | 2026-04-11 |
| S5-06 | Portfolio content (docs/portfolio.md) | CONCLUIDO | 2026-04-11 |
| S5-07 | Build AppImage Linux | PENDENTE | Precisa de maquina Linux |
| S5-08 | Testar build macOS em hardware real | PENDENTE | CI vai gerar; testar quando tiver Mac disponivel |
| S5-09 | Atualizar portfolio carzo.com.br | PENDENTE | Aguarda builds Windows + macOS publicados |
| S5-10 | Publicar v1.5.0 AppImage no GitHub Release | BLOQUEADO | Aguarda S5-07 |

---

## Backlog — v2.0: Motor Ayvu (SpeedOsper)

> Projeto experimental separado. Nao publicar. Apenas local.

| ID | Task | Status |
|----|------|--------|
| V2-01 | Arquitetura Motor Ayvu | PLANEJADO |
| V2-02 | Substituir faster-whisper por motor proprio | PLANEJADO |

---

## Concluido (historico)

| Versao | O que foi entregue |
|--------|--------------------|
| v1.0.0 | MVP: gravacao + Whisper local + tray icon + hotkeys |
| v1.1.0 | Push-to-talk, toggle, modo cursor/clipboard, pos-processamento |
| v1.2.0 | Deteccao automatica de hardware, fallback CPU, troca de modelo |
| v1.3.0 | Suporte Linux (cross-platform), platform backends |
| v1.4.0 | Atalhos personalizaveis, editor de prompt, logs diarios |
| v1.5.0 | API backends (OpenAI/Groq/Gemini/Deepgram), realtime WebSocket, overlay, configuracoes unificadas, suporte macOS |

---

_Ultima atualizacao: 2026-04-11 — configuracoes unificadas + suporte macOS_
