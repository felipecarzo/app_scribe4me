# Scribe4me v2 — Plano de Implementacao com Motor Ayvu

> Documento de referencia para implementacao do Scribe4me v2.
> Qualquer agente (humano ou IA) que trabalhar neste projeto DEVE ler este documento antes de agir.

---

## ATENCAO — O que e o Motor Ayvu (leia antes de tudo)

O motor ayvu e uma **biblioteca Rust compilada localmente** que roda modelos de IA **100% on-device via ONNX Runtime**. Ele **NAO usa APIs externas**, **NAO usa Google Cloud**, **NAO usa OpenAI API**, **NAO usa nenhum servico online para inferencia**.

### Modelos que o motor usa (todos locais, ONNX):

| Modelo | Repo HuggingFace | Tamanho | O que faz | Runtime |
|--------|------------------|---------|-----------|---------|
| **Whisper-base** | `Xenova/whisper-base` | ~200MB | STT (speech-to-text) | ONNX Runtime (crate `ort`) |
| **NLLB-200-distilled-600M** | `Xenova/nllb-200-distilled-600M` | ~1.5GB | Traducao (200 idiomas) | ONNX Runtime (crate `ort`) |
| **MMS-TTS-{lang}** | `Xenova/mms-tts-por`, `mms-tts-eng`, etc | ~50MB/lang | TTS (text-to-speech) | ONNX Runtime (crate `ort`) |
| **ParaphraseMLMiniLML12V2** | via `fastembed` | ~100MB | Embeddings semanticos 384D | fastembed (Rust) |

**Os modelos sao baixados do HuggingFace na PRIMEIRA execucao** e ficam em cache local.
Apos o download inicial, tudo roda 100% offline.

### O que o motor NAO e:

- NAO e um wrapper de API (Google Translate, DeepL, OpenAI, etc.)
- NAO usa PyTorch, TensorFlow, ou qualquer framework Python
- NAO depende de internet apos o download inicial dos modelos
- NAO e o faster-whisper (CTranslate2) — usa Whisper via ONNX Runtime em Rust
- NAO usa espeak-ng para TTS — usa tokenizacao character-level propria

---

## Contexto

### Scribe4me v1 (estado atual)

App desktop Windows (Python 3.12) para transcricao de voz local:

- **Engine STT:** faster-whisper (CTranslate2) — Python
- **Audio:** sounddevice (16kHz mono)
- **Hotkeys:** pynput (Ctrl+Alt+H push-to-talk, Ctrl+Alt+T toggle)
- **Output:** cola no cursor (pyperclip + Ctrl+V simulado) ou clipboard
- **UI:** system tray (pystray) com 5 estados visuais (cores)
- **Build:** PyInstaller (~64MB .exe) + Inno Setup installer
- **Funcionalidade:** apenas transcricao PT-BR, sem traducao

### Motor Ayvu (fonte: `D:\Documentos\Ti\projetos\app_ayvu\motor\`)

Crate Rust com pipeline completo de processamento de voz/texto:

- **STT:** Whisper-base via ONNX (auto-deteccao de idioma)
- **Traducao:** NLLB-200 distilado com KV cache + cache semantico
- **TTS:** MMS-TTS multilingue via ONNX
- **Prosodia:** extracao (pitch, energia, ZCR) + aplicacao em audio sintetizado
- **Embeddings:** vetores semanticos 384D (cross-lingual)
- **Qualidade:** validacao semantica (cosine similarity source vs target)
- **Protocolo P2P:** pacotes binarios 410/426 bytes (nao relevante para scribe4me)
- **WebSocket:** servidor hub de broadcast (nao relevante para scribe4me)

### Objetivo do v2

Criar uma **nova versao do Scribe4me** que usa o motor ayvu como core de ML/NLP,
mantendo a identidade do app (desktop, leve, system tray, Windows-first).

**Novos modos de operacao:**
1. **Scribe** — transcricao pura (como hoje, mas usando Whisper do motor)
2. **Translate** — transcreve + traduz para idioma configurado
3. **Voice** — transcreve + traduz + sintetiza audio no idioma alvo

---

## Arquitetura v2

```
┌──────────────────────────────────────────────────────────┐
│                    Scribe4me v2 (Python)                  │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Hotkeys  │  │  Tray UI │  │  Audio   │  │Clipboard│  │
│  │ (pynput) │  │ (pystray)│  │(sounddev)│  │  Paste  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │
│       │              │             │              │       │
│  ┌────┴──────────────┴─────────────┴──────────────┴────┐  │
│  │              Orchestrator (main.py)                  │  │
│  │  - Gerencia modos (Scribe / Translate / Voice)      │  │
│  │  - Despacha audio para o motor via FFI              │  │
│  │  - Recebe texto/audio de volta                      │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │ FFI (ctypes ou cffi)             │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           motor_ayvu.dll / motor_ayvu.so             │  │
│  │                                                     │  │
│  │  transcribe(samples, lang?) -> texto                │  │
│  │  translate_cached(text, src, tgt) -> TranslateResult│  │
│  │  synthesize(text, lang) -> samples PCM              │  │
│  │  voice_translate(samples, src?, tgt) -> VoiceTrRes  │  │
│  │  analyze_prosody(samples) -> ProsodyFeatures        │  │
│  │  motor_version() -> string                          │  │
│  │  cache_stats() -> JSON                              │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Separacao de responsabilidades

| Camada | Linguagem | Responsabilidade |
|--------|-----------|-----------------|
| **UI/Sistema** | Python | Hotkeys, tray icon, audio capture, clipboard, config, logging |
| **ML/NLP** | Rust (DLL) | STT, traducao, TTS, prosodia, cache, embeddings |

**Python nao faz ML.** O faster-whisper e removido. Toda inferencia passa pelo motor Rust.

---

## API FFI — Funcoes expostas pela DLL

O motor ayvu hoje expoe API via `flutter_rust_bridge`. Para o scribe4me,
precisamos de uma **camada C-ABI** (cdecl) que Python possa chamar via `ctypes`.

### Funcoes necessarias (C-ABI wrapper)

```c
// STT
// Recebe: samples (ponteiro f32), num_samples (usize), lang (nullable c_str)
// Retorna: c_str alocado (caller deve liberar com scribe_free_string)
const char* scribe_transcribe(const float* samples, size_t num_samples, const char* lang);

// Traducao com cache
// Recebe: text, src_lang (ISO 639-3: "por","eng"), tgt_lang
// Retorna: JSON { "translation": "...", "cache_hit": bool, "quality_score": f32 }
const char* scribe_translate(const char* text, const char* src_lang, const char* tgt_lang);

// TTS
// Recebe: text, lang (ISO 639-1: "pt","en")
// Retorna: ponteiro para struct { float* samples; size_t num_samples; uint32_t sample_rate; }
ScribeSynthResult* scribe_synthesize(const char* text, const char* lang);

// Pipeline completo: voz -> texto -> traducao -> voz
// Recebe: samples, num_samples, src_lang (nullable), tgt_lang
// Retorna: JSON com todos os campos de VoiceTranslateResult + ponteiro para audio
ScribeVoiceResult* scribe_voice_translate(const float* samples, size_t num_samples,
                                          const char* src_lang, const char* tgt_lang);

// Prosodia
ScribeProsody* scribe_analyze_prosody(const float* samples, size_t num_samples);

// Utilitarios
const char* scribe_motor_version();
const char* scribe_cache_stats();

// Liberacao de memoria
void scribe_free_string(const char* ptr);
void scribe_free_synth_result(ScribeSynthResult* ptr);
void scribe_free_voice_result(ScribeVoiceResult* ptr);
void scribe_free_prosody(ScribeProsody* ptr);
```

### Structs C-ABI

```c
typedef struct {
    float* samples;
    size_t num_samples;
    uint32_t sample_rate;
} ScribeSynthResult;

typedef struct {
    float* samples;
    size_t num_samples;
    uint32_t sample_rate;
    const char* source_text;
    const char* translated_text;
    bool cache_hit;
    float quality_score;
} ScribeVoiceResult;

typedef struct {
    float pitch_hz;
    float energy;
    float zcr;
    float duration_secs;
} ScribeProsody;
```

---

## Fases de implementacao

### Fase 0 — Preparacao (motor ayvu)

**Objetivo:** Adicionar camada C-ABI ao motor ayvu para que possa ser consumido via ctypes.

**Local:** `D:\Documentos\Ti\projetos\app_ayvu\motor\`

**Tasks:**

| ID | Task | Descricao | Estimativa |
|----|------|-----------|-----------|
| FFI-01 | C-ABI wrapper | Criar `src/ffi.rs` com funcoes `extern "C"` que chamam `api.rs` | Media |
| FFI-02 | Cargo config cdylib | Adicionar `[lib] crate-type = ["cdylib", "lib"]` ao `Cargo.toml` | Pequena |
| FFI-03 | Build DLL | `cargo build --release` gerando `motor_ayvu.dll` | Pequena |
| FFI-04 | Testes C-ABI | Testes de integracao chamando a DLL via ctypes (Python) | Media |
| FFI-05 | Header file | Gerar `motor_ayvu.h` (cbindgen ou manual) | Pequena |

**Criterio de aceite:** `python -c "import ctypes; dll = ctypes.CDLL('motor_ayvu.dll'); print(dll.scribe_motor_version())"` funciona.

### Fase 1 — Integracao basica (scribe4me)

**Objetivo:** Substituir faster-whisper pelo motor ayvu para transcricao (modo Scribe).

**Local:** `D:\Documentos\Ti\projetos\app_scribe4me\`

**Tasks:**

| ID | Task | Descricao |
|----|------|-----------|
| INT-01 | Python bridge | Criar `src/motor_bridge.py` — wrapper ctypes para a DLL |
| INT-02 | Substituir transcriber | `src/transcriber.py` passa a chamar `motor_bridge.transcribe()` |
| INT-03 | Remover faster-whisper | Remover do `requirements.txt` e imports |
| INT-04 | Config: caminho DLL | `src/config.py` — path para `motor_ayvu.dll` (bundled ou instalado) |
| INT-05 | Warm-up via motor | Substituir warm-up do faster-whisper pelo motor (primeira chamada lazy) |
| INT-06 | Testes de regressao | Garantir que todos os testes existentes passam com o novo backend |

**Criterio de aceite:** Push-to-talk funciona igual ao v1, mas usando Whisper do motor ayvu.

### Fase 2 — Modo Translate

**Objetivo:** Adicionar modo que transcreve + traduz automaticamente.

**Tasks:**

| ID | Task | Descricao |
|----|------|-----------|
| TRN-01 | Config: idioma alvo | `src/config.py` — `target_language` (default: "eng") |
| TRN-02 | Config: modo operacao | `src/config.py` — `mode` enum: "scribe", "translate", "voice" |
| TRN-03 | Orquestrador de modo | `main.py` — despacha para pipeline correto baseado no modo |
| TRN-04 | Tray: seletor de modo | Menu do tray com opcao de trocar modo (Scribe / Translate / Voice) |
| TRN-05 | Tray: seletor idioma | Submenu com idiomas alvo (EN, ES, PT, ZH) |
| TRN-06 | Output traduzido | Modo translate: cola "texto original\n-> traducao" ou so traducao (config) |
| TRN-07 | Testes modo translate | Testes end-to-end do pipeline transcricao + traducao |

**Criterio de aceite:** Fala em PT, texto traduzido em EN aparece no cursor.

### Fase 3 — Modo Voice

**Objetivo:** Pipeline completo voz-a-voz com prosodia.

**Tasks:**

| ID | Task | Descricao |
|----|------|-----------|
| VOZ-01 | Playback de audio | `src/player.py` — reproduz PCM f32 via sounddevice |
| VOZ-02 | Pipeline voice | `main.py` — chama `scribe_voice_translate`, reproduz audio + cola texto |
| VOZ-03 | Tray: estado PLAYING | Novo estado visual (roxo?) para quando esta reproduzindo audio |
| VOZ-04 | Config: auto-play | Opcao de reproduzir audio automaticamente ou so transcrever+traduzir |
| VOZ-05 | Prosodia display | Tray tooltip ou notificacao com metricas prosodicas (opcional) |
| VOZ-06 | Testes modo voice | Testes end-to-end do pipeline completo |

**Criterio de aceite:** Fala em PT, ouve traducao em EN com prosodia similar.

### Fase 4 — Polimento e build

**Objetivo:** Preparar para distribuicao.

**Tasks:**

| ID | Task | Descricao |
|----|------|-----------|
| BLD-01 | Bundling DLL | PyInstaller spec incluindo `motor_ayvu.dll` + modelos ONNX |
| BLD-02 | Download de modelos | First-run: baixar modelos (~2GB) com progress bar / notificacao |
| BLD-03 | Installer atualizado | Inno Setup com nova versao e dependencias |
| BLD-04 | Hardware detection v2 | `hardware.py` adaptado para detectar compatibilidade com ONNX Runtime |
| BLD-05 | Docs atualizados | README e PROJECT_OVERVIEW com novos features |
| BLD-06 | Testes finais | Suite completa de testes em maquina limpa |

---

## Decisoes tecnicas

### Por que ctypes e nao PyO3/pyo3?

- **ctypes** e stdlib Python — zero dependencia extra
- A DLL ja vai existir (motor ayvu compila como cdylib)
- Evita acoplar o motor ao ecossistema Python (PyO3 gera .pyd)
- Scribe4me pode ser portado para qualquer linguagem no futuro
- Tradeoff: ctypes e mais verboso, mas mais simples e desacoplado

### Por que nao manter faster-whisper + adicionar motor para traducao?

- Dois runtimes de STT (CTranslate2 + ONNX Runtime) = dobro de VRAM
- Motor ayvu ja tem Whisper ONNX funcionando e testado
- Unificar o runtime simplifica build, debug e distribuicao
- Unico tradeoff: faster-whisper suporta mais modelos (large-v3), motor so tem base
  - Mitigacao futura: adicionar modelos maiores ao motor se necessario

### Por que nao reescrever tudo em Rust?

- Python e ideal para UI desktop leve (pystray, pynput, sounddevice)
- Rust desktop (egui, iced) nao tem equivalente maduro para system tray no Windows
- Manter Python para orquestracao preserva o ecossistema existente
- Heavy lifting (ML) ja esta em Rust — melhor dos dois mundos

---

## Mapa de dependencias entre fases

```
Fase 0 (motor: C-ABI)
    │
    ▼
Fase 1 (integracao basica: modo Scribe)
    │
    ├──► Fase 2 (modo Translate) ──► Fase 3 (modo Voice)
    │                                      │
    └──────────────────────────────────────►│
                                           ▼
                                    Fase 4 (build/polish)
```

Fases 2 e 3 sao sequenciais (Voice depende de Translate).
Fase 4 pode comecar em paralelo com Fase 3 (exceto BLD-06).

---

## Riscos e mitigacoes

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| ONNX Runtime DLL conflicts (Python vs Rust) | Build quebra | Motor compila ONNX Runtime estaticamente (ja faz isso) |
| Tamanho do installer explode (~2GB com modelos) | UX ruim | Modelos baixados on-demand no first-run (nao bundled) |
| Whisper-base inferior ao large-v3 do faster-whisper | Qualidade STT menor | Fase futura: adicionar suporte a modelos maiores no motor |
| ctypes memory leaks | Crashes | Disciplina rigorosa: toda alocacao tem free correspondente |
| Motor ayvu evolui e quebra ABI | Integracao quebra | Versionar API C-ABI; motor_version() como health check |

---

## Estrutura de arquivos v2 (projetada)

```
app_scribe4me/
├── src/
│   ├── main.py              # Orquestrador (atualizado: 3 modos)
│   ├── config.py            # Config (atualizado: modo, idioma alvo, path DLL)
│   ├── motor_bridge.py      # NOVO — wrapper ctypes para motor_ayvu.dll
│   ├── recorder.py          # Sem mudanca
│   ├── transcriber.py       # Refatorado: chama motor_bridge ao inves de faster-whisper
│   ├── translator.py        # NOVO — orquestra transcricao + traducao
│   ├── player.py            # NOVO — playback de audio PCM (Fase 3)
│   ├── clipboard.py         # Sem mudanca
│   ├── hardware.py          # Atualizado: detectar compatibilidade ONNX Runtime
│   ├── tray.py              # Atualizado: novos menus (modo, idioma) + estado PLAYING
│   ├── postprocess.py       # Sem mudanca (pos-processamento de texto)
│   └── __init__.py
├── motor/
│   └── motor_ayvu.dll       # DLL compilada do motor (ou baixada no install)
├── tests/
│   ├── ... (existentes, atualizados)
│   ├── test_motor_bridge.py # NOVO — testes do wrapper ctypes
│   ├── test_translator.py   # NOVO — testes do pipeline traducao
│   └── test_player.py       # NOVO — testes do playback (Fase 3)
├── docs/
│   ├── PROJECT_OVERVIEW.md  # Atualizado
│   └── SCRIBE4ME_V2_PLAN.md # Este documento
├── requirements.txt         # Atualizado (sem faster-whisper)
└── ...
```

---

## Referencia rapida — Repositorio do motor

- **Codigo fonte:** `D:\Documentos\Ti\projetos\app_ayvu\motor\src\`
- **API publica:** `motor\src\api.rs` (678 linhas, todas as funcoes documentadas)
- **Modulos:** encoder, decoder, prosody, cache, protocol, stt, tts, quality
- **Build:** `cargo build --release` (gera target/release/motor_ayvu.dll com cdylib)
- **Testes:** `cargo test` (200+ testes passando)
- **Dependencias chave:** `ort` (ONNX Runtime), `fastembed`, `tokenizers`, `hf-hub`, `rustfft`, `crc`

---

## Checklist de validacao por fase

### Fase 0
- [ ] `motor_ayvu.dll` compila com `crate-type = ["cdylib", "lib"]`
- [ ] Funcoes `extern "C"` em `ffi.rs` cobrem: transcribe, translate, synthesize, voice_translate, analyze_prosody, motor_version, cache_stats
- [ ] Todas as funcoes free correspondentes existem
- [ ] Python consegue carregar a DLL e chamar `scribe_motor_version()`
- [ ] Testes de integracao Python ↔ Rust passam

### Fase 1
- [ ] `motor_bridge.py` carrega DLL e expoe API Pythonica
- [ ] `transcriber.py` usa motor_bridge (zero imports de faster-whisper)
- [ ] `requirements.txt` sem faster-whisper
- [ ] Todos os 8 test modules passam
- [ ] Push-to-talk funciona identico ao v1

### Fase 2
- [ ] Modo Translate funciona via tray menu
- [ ] Seletor de idioma alvo no tray
- [ ] Traducao aparece no cursor/clipboard
- [ ] Cache semantico funciona (segunda traducao da mesma frase e instantanea)
- [ ] Quality score acessivel (log ou tooltip)

### Fase 3
- [ ] Audio traduzido reproduz automaticamente
- [ ] Prosodia do falante original e preservada
- [ ] Novo estado visual no tray (PLAYING)
- [ ] Opcao de desabilitar auto-play

### Fase 4
- [ ] Installer funcional com DLL bundled
- [ ] First-run baixa modelos com feedback visual
- [ ] Tamanho do installer sem modelos < 100MB
- [ ] Funciona em maquina limpa (sem Rust, sem Python dev tools)
