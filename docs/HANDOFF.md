# HANDOFF — Estado atual do projeto app_ayvu

> Arquivo vivo. Sobrescrito ao final de cada sessão, por qualquer agente.
> **Não é um diário** — não acumula histórico. Para histórico, ver `docs/daily/`.
> Qualquer agente (Claudio ou Antigravity) lê este arquivo antes de qualquer ação.
> **Sempre validar contra `git status` + `git log` antes de confiar nas pendências listadas aqui.**

---

## Meta
- **Última atualização:** 2026-03-14 — Sprint 1/2, MOT-05 Rust concluído + TRANS-01-FL concluída
- **Agente que escreveu:** Scrum Manager (Claudio)
- **Máquina:** ALIENWARE-LIPE
- **Branch atual:** `main`
- **Commits desta sessão:**
  - `feat(motor): MOT-05 — benchmark Rust + fix decoder NLLB-200`
  - `feat(app): TRANS-01-FL — tela de tradução Flutter com Riverpod`

---

## Task em andamento
- **ID:** TRANS-02-FL (ou TRANS-03-FL — ver decisão abaixo)
- **Descrição:** TRANS-01-FL concluída. Próxima task a confirmar com Felipe: TRANS-02-FL (seletor de idiomas — PT/EN/ZH já existe, escopo é adicionar ES e/ou expandir) **ou** TRANS-03-FL (histórico SQLite, scope claramente novo).
- **Status:** aguardando decisão de Felipe sobre TRANS-02-FL vs TRANS-03-FL

---

## Próximo passo exato
1. Rodar `git status` e `git log --oneline -3` (protocolo anti-alucinação)
2. Felipe decide: **TRANS-02-FL** (expandir seletor de idiomas — qual idioma adicionar além de PT/EN/ZH?) ou **TRANS-03-FL** (histórico de traduções SQLite local)
3. Se TRANS-02-FL: confirmar lista de idiomas alvo antes de codar
4. Se TRANS-03-FL: invocar Planner (depende de SQLite/drift — decisão arquitetural)
5. MOT-05 Python side: rodar `legacy/` para gerar `docs/benchmark/results/python_results.json` e fechar relatório comparativo

---

## Arquivos a ler no início da sessão
```text
CLAUDE.md
docs/ROADMAP.md
docs/HANDOFF.md
motor/src/encoder/mod.rs        — EmbeddingEngine (fastembed, MiniLM 384D)
motor/src/decoder/mod.rs        — Translator (NLLB-200 ONNX via hf-hub + ort 2.0)
motor/src/cache/mod.rs          — SemanticCache com quality_score persistido
motor/src/quality/mod.rs        — QualityReport { score, passed, critically_low }
motor/src/api.rs                — FFI pública com validate_translation() + TranslateResult.quality
app/lib/features/translator/    — tela de tradução Flutter (Riverpod)
app/lib/core/bridge/            — MotorBridge FFI wrapper + FRB bindings
docs/session/MOT-05.md          — plano e resultados do benchmark Rust
docs/session/TRANS-01-FL.md     — plano e notas da tela de tradução
docs/benchmark/results/         — benchmark_results.json (Rust) + python_results.json (pendente)
legacy/                         — app_tradutor Python (referência para MOT-05 Python side)
```

---

## Contexto crítico
- Sprint 0 totalmente concluída — todos os 7 INFs ✅ e commitados
- Flutter 3.41.4 instalado em C:/dev/flutter (PATH do user atualizado)
- Rust 1.94.0 instalado via rustup (PATH do user atualizado)
- Android SDK 36.1.0 + licenças aceitas + Android Studio instalado
- `app/` scaffoldado (Flutter), `motor/` scaffoldado (Rust crate)
- flutter_rust_bridge v2.11.1 configurado + codegen rodado
- Legacy copiado em `legacy/`, todos os placeholders preenchidos
- Antigravity configurado para o projeto
- Nome "ayvu" pode mudar — já pertence a alguém
- Stack: Flutter (app) + Rust (motor/patente) + flutter_rust_bridge (FFI)
- Documento técnico de patente adicionado

### MOT-01 — Encoder semântico (commitado em 2adcab9)
- `motor/src/encoder/mod.rs` — `EmbeddingEngine` com fastembed (MiniLM 384D), `cosine_similarity`, testes passando
- Modelo baixado on-demand via fastembed

### MOT-02 — Decoder NLLB-200 (commitado em cbd660f)
- `motor/src/decoder/mod.rs` — `Translator` com NLLB-200 via hf-hub + ort 2.0
- `motor/src/api.rs` — FFI pública atualizada com `translate()`
- Session file: `docs/session/MOT-02.md`

### MOT-03 — Cache semântico (commitado em fbed236)
- `motor/src/cache/mod.rs` — `SemanticCache` com lookup/store por similaridade coseno, threshold 0.90, eviction FIFO
- 11 testes unitários + 4 testes de integração em `motor/tests/cache_integration.rs`
- Fixes G4/R1: FFI retorna `Result<T, String>`, `cache_stats()` inclui `entries_per_pair`
- Session file: `docs/session/MOT-03.md`

### MOT-04 — Validação de qualidade (commitado em 820a8fb)
- `motor/src/quality/mod.rs` — `QualityReport { score, passed, critically_low }`, `evaluate()`, `from_score()`
- `motor/src/api.rs` — `validate_translation()` exposta na FFI; `TranslateResult` inclui campo `quality`
- 26 testes unitários passando; `cargo clippy` sem warnings
- Fixes G1/G2: `CacheEntry` persiste `quality_score: f32`; cache hits reconstroem `QualityReport::from_score()` — sem score 1.0 artificial
- Bindings FRB regenerados
- Session file: `docs/session/MOT-04.md`

### MOT-05 — Benchmark Rust (commitado nesta sessão)
- `motor/tests/benchmark_mot05.rs` — suite de benchmark Rust
- Resultados: **94.2% pass rate, 413ms média de latência, quality score 0.915**
- `docs/benchmark/results/benchmark_results.json` — resultados Rust salvos
- **Pendente:** rodar lado Python (legacy) para gerar `python_results.json` e fechar relatório comparativo
- Fix decoder NLLB-200 incluído neste commit
- Session file: `docs/session/MOT-05.md`

### TRANS-01-FL — Tela de tradução Flutter (commitado nesta sessão)
- `app/lib/features/translator/` — tela principal com Riverpod
- `app/lib/core/bridge/motor_bridge.dart` — MotorBridge FFI wrapper
- `app/lib/shared/widgets/quality_badge.dart` — QualityBadge widget
- Lang selector implementado: **PT-BR / EN / ZH** (não ES — atenção ao escopo de TRANS-02-FL)
- 20 testes passando; `flutter analyze` limpo; todos os issues do Revisor resolvidos
- Session file: `docs/session/TRANS-01-FL.md`

---

## Branches ativas

| Branch | Tipo | Último commit | Estado |
|---|---|---|---|
| `main` | desenvolvimento ativo | `feat(app): TRANS-01-FL` | Sprint 1/2 em andamento |

**Nota:** projeto ainda em `main` (sem branch `develop` criado). Considerar separar quando aproximar de release.

---

## Estado do ROADMAP (Sprint 1/2 — em progresso)

| ID | Task | Status |
|---|---|---|
| MOT-01 | Encoder semântico: texto -> vetor de intenção | ✅ |
| MOT-02 | Decoder: vetor de intenção -> texto (PT-BR <-> EN) | ✅ |
| MOT-03 | Cache semântico (similaridade coseno, lookup/store) | ✅ |
| MOT-04 | Validação de qualidade (embedding source vs target) | ✅ |
| MOT-05 | Benchmark: motor Rust vs NLLB-200 Python (legacy) | ⏳ Rust concluído; Python pendente |
| TRANS-01-FL | Tela de tradução texto (input -> motor -> output) | ✅ |
| TRANS-02-FL | Seletor de idiomas (PT/EN/ZH já feito; definir expansão) | ⏳ escopo a confirmar |
| TRANS-03-FL | Histórico de traduções (SQLite local) | 🔒 |
| SET-01-FL | Tela de configurações | 🔒 |
