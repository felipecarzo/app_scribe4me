# MOT-03 — Cache semântico (similaridade coseno, lookup/store)

**Status**: APROVADO COM RESSALVAS — revisão concluída
**Data**: 2026-03-14

---

## Resultado dos Testes

### Testes unitários (`cargo test --lib`)

| Teste | Status |
|---|---|
| `cache::tests::cache_miss_vazio` | ok |
| `cache::tests::cache_hit_exato` | ok |
| `cache::tests::cache_hit_similar` | ok |
| `cache::tests::cache_miss_dissimilar` | ok |
| `cache::tests::cache_miss_threshold_boundary` | ok |
| `cache::tests::cache_hit_acima_threshold` | ok |
| `cache::tests::eviction_fifo` | ok |
| `cache::tests::isolamento_por_par` | ok |
| `cache::tests::best_match_retornado` | ok |
| `cache::tests::stats_correto` | ok |
| `cache::tests::clear_esvazia_cache` | ok |
| `decoder::tests::to_nllb_code_all_mapped` | ok |
| `decoder::tests::to_nllb_code_known_langs` | ok |
| `decoder::tests::to_nllb_code_unknown_returns_none` | ok |
| `encoder::tests::cosine_identical_vectors` | ok |
| `encoder::tests::cosine_orthogonal_vectors` | ok |
| `encoder::tests::cosine_zero_vector` | ok |

**Total: 17 passed, 0 failed**

Clippy: sem warnings.

---

## Avaliação de Cobertura

### Testes unitários — casos críticos do cache

Os 11 testes de `cache/mod.rs` cobrem:

| Caso | Coberto? |
|---|---|
| Lookup em cache vazio | Sim — `cache_miss_vazio` |
| Hit com vetor idêntico (sim = 1.0) | Sim — `cache_hit_exato` |
| Hit com vetor próximo (sim ~0.995) | Sim — `cache_hit_similar` |
| Miss com vetor ortogonal (sim = 0.0) | Sim — `cache_miss_dissimilar` |
| Miss na fronteira do threshold (sim < 0.90) | Sim — `cache_miss_threshold_boundary` |
| Hit acima do threshold (sim ~0.951) | Sim — `cache_hit_acima_threshold` |
| Eviction FIFO ao exceder max_size | Sim — `eviction_fifo` |
| Isolamento por par de idiomas | Sim — `isolamento_por_par` |
| Retorno do melhor match entre múltiplos candidatos | Sim — `best_match_retornado` |
| Contagem de stats (total, pairs, per_pair) | Sim — `stats_correto` |
| Clear + is_empty + len | Sim — `clear_esvazia_cache` |

**Cobertura unitária: adequada.** Todos os caminhos críticos do `SemanticCache` estão cobertos.

### Testes de integração (`tests/cache_integration.rs`)

Os 4 testes usam `EmbeddingEngine` real com frases PT-BR:

| Teste | O que verifica | Correto? |
|---|---|---|
| `cache_hit_mesma_frase` | Store + lookup com mesmo embedding (sim = 1.0) | Sim |
| `cache_hit_paraphrase` | Hit com paráfrase real ("Bom dia..." / "Olá, tudo bem...") — condicional se sim >= threshold | Sim — design defensivo correto |
| `cache_miss_frase_diferente` | Miss com frase semanticamente distante | Sim |
| `cache_isolamento_idioma` | Mesmo embedding, três pares (pt→es: miss, en→pt: miss, pt→en: hit) | Sim — mais completo que o equivalente unitário |

Os 4 testes estão corretos. O `cache_hit_paraphrase` com lógica condicional é a abordagem adequada: a similaridade real depende do modelo, não é um valor fixo. O `println!` do valor de similaridade facilita diagnóstico caso o modelo mude.

---

## Gaps identificados

| # | Descrição | Pode ser testado offline? | Prioridade |
|---|---|---|---|
| G1 | `translate_cached` (api.rs) sem cobertura de teste — fluxo completo embed→lookup→translate→store | Não sem mock de EmbeddingEngine + Translator | Baixa (requer modelo ~1.5 GB) |
| G2 | `cache_stats()` na API serializa JSON manualmente — sem teste de formato do output | Sim (unit, mas exige singleton CACHE) | Baixa |
| G3 | `store` com `max_size = 1` não tem teste explícito — comportamento do drain com `drain_count = len` | Sim | Baixa |
| G4 | `.expect()` em `translate_cached` herda risco de panic da FFI (identificado em MOT-02/G2) | Não sem refactor | Média — pré-existente |

G1 é o gap mais relevante, mas é estruturalmente inevitável sem injeção de dependência ou mock do motor. O design atual (singletons `OnceLock`) torna `translate_cached` não testável offline.

G4 é herança de MOT-02 e não é exclusivo de MOT-03.

---

## Observações sobre `api.rs` (adições de MOT-03)

- Singleton `CACHE: OnceLock<Mutex<SemanticCache>>` — correto, thread-safe, padrão consistente com os demais singletons.
- `translate_cached` — fluxo correto: embed → lookup → (hit: retorna) → translate → store. `cache_hit: bool` é informação útil para a UI Flutter.
- `cache_stats()` retorna JSON serializado manualmente. Funciona para debug, mas é frágil para extensão. Não bloqueia Sprint 0.
- `TranslateResult` é uma struct pública simples — adequada para a FFI bridge.

---

## Conclusão do Tester

Os 11 testes unitários cobrem **todos os casos críticos** do `SemanticCache`: lookup (hit/miss/threshold/best-match), store, eviction FIFO, isolamento por par e stats. Os 4 testes de integração são corretos e exercitam o cache com embeddings reais.

Os gaps identificados (G1-G4) são de baixa prioridade para Sprint 0. G4 (`.expect()` vs `Result` na FFI) é pré-existente e já documentado para resolução antes da integração Flutter.

**Aprovado para Revisor.**

---

## Revisão de Código (Revisor)

**Data**: 2026-03-14

---

### 1. Correctness

**cache/mod.rs**

- `lookup`: lógica correta — filtra por threshold, retorna o `max_by` sim. `partial_cmp` com fallback `Equal` é seguro para f32 sem NaN (vetores normalizados não produzem NaN em cosine_similarity).
- `store` / eviction: `drain_count = bucket.len() - max_size + 1` é correto — remove exatamente o necessário para abrir uma vaga. Com `max_size = 1`, drain_count = 1 (remove o único elemento antes de inserir o novo). Comportamento correto, gap G3 do Tester é sem fundamento.
- `stats`: clona todas as keys do HashMap para construir `entries_per_pair`. Correto funcionalmente; custo O(n_pairs), aceitável.
- `is_empty` chama `len()` que itera todos os buckets — O(n_pairs). Para o volume atual (500 entradas/par, poucos pares), irrelevante.

**api.rs — partes de MOT-03**

- `translate_cached`: fluxo correto. Nenhum valor stale pode ser retornado — o lookup acontece antes de qualquer escrita.
- `cache_stats`: JSON serializado manualmente. Correto para os dois campos presentes (`total_entries`, `pairs_tracked`). `entries_per_pair` não está incluído no JSON — divergência entre doc do código (comentário "para debug") e o que `CacheStats` contém. Não é bug, mas é uma omissão silenciosa.

---

### 2. Thread-safety e race conditions

O ponto mais crítico da task. Sequência em `translate_cached`:

```
EMBED_ENGINE.lock() → (libera) →
CACHE.lock()        → (libera) →
TRANSLATOR.lock()   → (libera) →
CACHE.lock()        → (libera)
```

**Nenhum lock é mantido enquanto outro é adquirido.** Não há risco de deadlock nem de lock ordering. Cada lock é adquirido, usado e liberado antes de adquirir o próximo.

Race condition lógica possível (TOCTOU no cache): entre o `lookup` (passo 2) e o segundo `CACHE.lock()` para `store` (passo 4), outra thread pode ter inserido a mesma tradução. Resultado: entrada duplicada no bucket. Consequência: bucket pode brevemente ter uma entrada a mais antes do próximo `store` disparar eviction. **Não é corrupção de dados; é duplicata inócua.** Aceitável para Sprint 0; pode ser mitigado com lock único cobrindo lookup+store se necessário no futuro.

Mutex envenenamento: todos os `.expect("Mutex envenenado")` fazem panic, propagando o envenenamento. Comportamento padrão do ecossistema Rust; documentado como gap G4 (herdado de MOT-02).

**Veredicto de thread-safety: seguro para o uso atual.**

---

### 3. Design

**Pontos positivos**
- Separação limpa: `SemanticCache` é puro (sem dependências de singletons). Testável isoladamente.
- Padrão singleton com `OnceLock<Mutex<T>>` é consistente com MOT-01/MOT-02.
- `TranslateResult { translation, cache_hit }` é a interface correta para a UI Flutter.
- `with_config` permite instanciar cache com parâmetros customizados — bom para testes.

**Pontos de atenção**

R1 — **`cache_stats` retorna JSON sem `entries_per_pair`**: o campo existe em `CacheStats` mas não é serializado. Quem consume o JSON não sabe quais pares existem. Para debug rudimentar é suficiente; para a UI Flutter futura pode ser insuficiente. Não bloqueia Sprint 0.

R2 — **Sem deduplicação no `store`**: se a mesma frase for traduzida duas vezes (miss → store, miss → store), cria duas entradas com embeddings idênticos. O lookup retornará a mais similar (qualquer uma das duas, pois sim = 1.0). Não há impacto funcional, mas ocupa espaço do bucket. Pré-condição para que isso não aconteça na prática: `translate_cached` sempre consulta antes de armazenar, então duplicata só ocorre via race (TOCTOU acima) ou chamadas diretas a `store` sem lookup prévio.

R3 — **Singletons tornam `translate_cached` não testável sem modelo**: design consequência de MOT-01/MOT-02. Gap G1 é estrutural. Solução de longo prazo: injeção de dependência ou trait objects. Fora de escopo de Sprint 0.

---

### 4. Tratamento de erros

Sem novidades em relação a MOT-02. Todos os `.expect()` em `translate_cached` e `cache_stats` são herdados do padrão estabelecido. Gap G4 persiste. Nenhum novo vetor de panic introduzido por MOT-03.

---

### 5. Impacto de `rlib` no `crate-type`

`["cdylib", "staticlib", "rlib"]`

- `cdylib`: biblioteca dinâmica para FFI (Flutter via JNI/dylib). Produção.
- `staticlib`: biblioteca estática para linkagem estática (iOS). Produção.
- `rlib`: formato nativo Rust, necessário para que `cargo test --test cache_integration` possa importar `motor::cache` e `motor::encoder` como crate externa.

**Impacto na build final**:
- Cargo compila três artefatos distintos a partir do mesmo código. Custo: tempo de link levemente maior, três arquivos de saída em `target/`.
- Não há conflito entre os três formatos. É padrão em crates de bibliotecas híbridas (FFI + testes de integração).
- `rlib` não é empacotado no APK/IPA — apenas `cdylib`/`staticlib` são copiados pelo flutter_rust_bridge build step.
- **Nenhum risco para a build final.** A adição é correta e necessária.

---

### 6. Checklist final

| Item | Status |
|---|---|
| Correctness — SemanticCache | OK |
| Correctness — translate_cached | OK |
| Thread-safety — sem deadlock | OK |
| Race condition TOCTOU no cache | Inócua, documentada |
| `rlib` no crate-type | OK, sem impacto em produção |
| Cobertura de testes (unitários) | Adequada |
| Cobertura de testes (integração) | Adequada |
| G1 translate_cached sem mock | Baixa prioridade, estrutural |
| G2 cache_stats JSON incompleto | Baixa prioridade (R1 acima) |
| G4 .expect() na FFI | Média, pré-existente, documentado |

---

### Veredicto

**APROVADO COM RESSALVAS**

A implementação está correta, thread-safe e consistente com o design estabelecido. As ressalvas não bloqueiam Sprint 0:

- **R1** (cache_stats sem entries_per_pair no JSON): registrar como débito técnico para quando a UI Flutter consumir cache_stats.
- **R2** (deduplicação no store): irrelevante na prática dado o fluxo de translate_cached; registrar para Sprint 1.
- **G4** (.expect() na FFI): já documentado em MOT-02, resolver antes da integração Flutter.

Nenhum item exige retrabalho imediato.
