# Session — MOT-05: Benchmark Motor Rust vs NLLB-200 Python

> Criado em: 2026-03-14
> Status: em andamento (aguardando python_results.json)

---

## Objetivo

Medir e comparar latência e qualidade semântica do motor Rust (NLLB-200 ONNX via ort, greedy decoding) contra a implementação Python legacy (NLLB-200 CT2, beam_size=4, CPU float32).

**Corpus:** 60 frases, 5 domínios (conversacao, saude, viagem, tecnico, negocios), 3 idiomas (PT/EN/ZH) — 6 direções × 60 = 360 traduções por engine.

---

## Bug crítico encontrado e corrigido

Durante a execução do benchmark, o decoder Rust gerava lixo ("is is is", "was") para todas as traduções. Bug identificado em `motor/src/decoder/mod.rs`:

### Causa 1 — Token de idioma fonte ausente no encoder
NLLB-200 exige formato `<src_lang> tokens </s>` no encoder. O `tokenizer.encode(text, true)` gerava `[default_lang, ...tokens, EOS]` com idioma errado.

**Fix:** Após o encode, o primeiro token é substituído pelo ID correto do idioma fonte:
```rust
let mut input_ids: Vec<i64> = encoding.get_ids()...
if !input_ids.is_empty() {
    input_ids[0] = src_token_id;  // substitui token de idioma padrão
}
```

### Causa 2 — Decoder start token errado
NLLB-200 exige `[</s>, <tgt_lang>]` como início do decoder (EOS como start token). O código usava apenas `[tgt_token_id]`.

**Fix:**
```rust
let mut dec_ids: Vec<i64> = vec![EOS_TOKEN_ID, tgt_token_id];
```

### Safety net adicionada
Proteção contra loops de repetição degenerada (MAX_REPEATS = 8 tokens idênticos consecutivos):
```rust
if next_id == last_token {
    repeat_count += 1;
    if repeat_count >= MAX_REPEATS { break; }
}
```

---

## Resultados Rust (concluído)

**Executado em:** 2026-03-14
**Duração:** 167s para 360 traduções
**JSON:** `docs/benchmark/results/rust_results.json`

| Métrica | Valor |
|---|---|
| Traduções totais | 360 |
| Latência média | 413ms |
| P50 global | ~400ms |
| Quality score médio | 0.9151 |
| Pass rate (≥0.75) | 94.2% |
| Critically low (<0.60) | 2.2% |

### Por direção

| Direção | P50 | P90 | Quality | Pass |
|---|---|---|---|---|
| pt→en | 410ms | 538ms | 0.929 | 96.7% |
| pt→zh | 426ms | 519ms | 0.912 | 95.0% |
| en→pt | 429ms | 587ms | 0.940 | 98.3% |
| en→zh | 405ms | 503ms | 0.905 | 93.3% |
| zh→pt | 426ms | 570ms | 0.884 | 88.3% |
| zh→en | 365ms | 528ms | 0.920 | 93.3% |

**Observações:**
- Direções com ZH como destino têm qualidade ligeiramente menor (esperado — greedy decoding)
- zh→pt tem pass rate menor (88.3%) — domínio técnico sofre mais
- assert ≥70% pass rate: PASSOU com 94.2%

---

## Resultados Python (pendente)

**Status:** benchmark rodando em terminal separado
**JSON esperado:** `docs/benchmark/results/python_results.json`

---

## Próximo passo

Quando `python_results.json` estiver disponível:
```bash
PYTHONIOENCODING=utf-8 python docs/benchmark/generate_report.py
```
Isso gera `docs/benchmark/results/MOT-05-report.md` com comparativo completo.

---

## Arquivos modificados nesta task

- `motor/src/decoder/mod.rs` — fix token idioma fonte + fix decoder start + proteção repetição
- `motor/Cargo.toml` — `ort` mudou de `load-dynamic` para `download-binaries`; `serde_json` adicionado em dev-dependencies
- `motor/Cargo.lock` — atualizado
- `motor/tests/benchmark_mot05.rs` — benchmark Rust (novo)
- `docs/benchmark/corpus.json` — corpus 60 frases (novo)
- `docs/benchmark/benchmark_python.py` — benchmark Python (novo, corrigido API legacy)
- `docs/benchmark/generate_report.py` — gerador de relatório comparativo (novo)
- `docs/benchmark/requirements_benchmark.txt` — deps Python (novo)
