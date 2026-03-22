# MOT-04 — Validação de qualidade (embedding source vs target)

**Status**: Tester concluído — aprovado com observações menores
**Data**: 2026-03-14
**Avaliado por**: Agente Tester

---

## 1. Resumo

A task implementa avaliação de qualidade semântica cross-lingual por similaridade de cosseno entre embedding do texto fonte e embedding do texto traduzido. A cobertura de testes é sólida para o escopo entregue. Nenhum gap bloqueante identificado.

---

## 2. Testes unitários — `quality/mod.rs` (7 testes)

| Teste | Caso coberto | Resultado | Observação |
|---|---|---|---|
| `evaluate_identical_embeddings` | score = 1.0, passed, not critically_low | ok | |
| `evaluate_high_similarity` | score > threshold | ok | |
| `evaluate_borderline_passed` | score exatamente em 0.75 (passed = true) | ok | Construção geométrica correta |
| `evaluate_borderline_failed` | score em 0.74 (passed = false, not critically_low) | ok | Faixa "falhou mas não crítico" coberta |
| `evaluate_critically_low` | score < 0.60 (critically_low = true) | ok | |
| `evaluate_zero_vector` | vetor zero => score 0.0 | ok | Edge case de degeneração |
| `perfect_report` | `QualityReport::perfect()` | ok | Construtor auxiliar validado |

**Veredicto**: Todos os 7 casos cobrem os branches da função `evaluate` e do construtor `perfect()`. As três regiões do espaço de score (passed / failed-normal / critically_low) estão cobertas, incluindo bordas exatas.

**Gap menor**: Não há teste para `score == QUALITY_WARN_THRESHOLD` (0.60 exato — borderline critically_low). O caso é análogo ao `evaluate_borderline_passed` e o risco é baixo, mas a simetria seria boa para documentação.

---

## 3. Testes de integração — `tests/quality_integration.rs` (6 testes)

| Teste | Cenário | Assert | Observação |
|---|---|---|---|
| `quality_correct_translation_pt_en` | Tradução correta PT→EN | `passed == true` | Frase coloquial real |
| `quality_correct_translation_en_pt` | Tradução correta EN→PT | `passed == true` | Par diferente |
| `quality_identical_text` | src == tgt | `score ≈ 1.0` | Verifica invariante do modelo |
| `quality_bad_translation_critically_low` | Texto completamente fora de contexto | `!passed` + `critically_low OR < threshold` | Assert conservador (correto: modelo pode variar) |
| `quality_semantic_inversion` | Frase com sentido oposto | Nenhum assert — apenas `println!` | **Ver observação abaixo** |
| `quality_calibration_conversational_pt_en` | 8 pares PT↔EN | Todos devem passar no threshold | Benchmark de calibração robusto |

**Veredicto**: A cobertura de integração é adequada. Os testes exercitam o modelo real com inputs linguísticos genuínos e verificam os casos de uso principais da task.

### Observação sobre `quality_semantic_inversion`

O teste não faz nenhum `assert` — apenas printa scores. Isso é aceitável como teste de calibração/observação, mas não detecta regressões. O comentário no arquivo reconhece isso explicitamente ("Registra o score para calibração — sem assert absoluto pois depende do modelo"). **Não é um gap bloqueante**, mas se o modelo for trocado ou os thresholds alterados, esse teste não vai quebrar para sinalizar mudança de comportamento. Recomendação para iteração futura: adicionar um assert suave (ex: `score < 0.90`) para detectar se inversões semânticas passam a gerar scores altos demais.

---

## 4. Cobertura da API (`api.rs`)

As três funções novas/modificadas na API pública não têm testes unitários dedicados — isso é esperado e aceitável, pois dependem de singletons e modelos pesados:

- `translate_cached` — cobre path de cache miss com `quality::evaluate` integrado
- `validate_translation` — expõe `quality::evaluate` direto via FFI
- `TranslateResult.quality` — campo verificado indiretamente pelos testes unitários do `quality` module

Não há testes de integração que exercitem `validate_translation` isoladamente ou o campo `quality` de `translate_cached`. Esses são gaps de cobertura mas **não bloqueantes para MOT-04** — a lógica de negócio está em `quality/mod.rs`, que está bem coberta.

---

## 5. Gaps identificados

| # | Gap | Severidade | Bloqueante? |
|---|---|---|---|
| G1 | `quality_semantic_inversion` sem assert — não detecta regressão | Baixa | Não |
| G2 | Borderline `QUALITY_WARN_THRESHOLD` (0.60 exato) sem teste unitário | Baixa | Não |
| G3 | `validate_translation` da API sem teste de integração próprio | Baixa | Não |

---

## 6. Decisão

**Aprovado para Revisor.**
Os 7 testes unitários cobrem todos os branches de `quality/mod.rs`. Os 6 testes de integração validam o comportamento real do modelo cross-lingual com asserts significativos (exceto `quality_semantic_inversion`). Todos os 24 testes passam, clippy sem warnings.

Os gaps identificados são recomendações para iteração futura, não impedimentos para aprovação da task.

---

## 7. Revisão de Código — Agente Revisor

**Data**: 2026-03-14
**Avaliado por**: Agente Revisor

### 7.1 Verificações diretas

**Lock contention em `validate_translation`**: Não há deadlock. Os dois `.lock()` sobre `EMBED_ENGINE` (api.rs linhas 133 e 139) são sequenciais com drop implícito entre eles — o guard do primeiro é liberado antes do segundo ser adquirido. Correto.

**Derives de `QualityReport` para flutter_rust_bridge**: `#[derive(Debug, Clone)]` presente (quality/mod.rs linha 19). flutter_rust_bridge requer exatamente `Clone` + `Debug` para tipos de retorno FFI. Correto. `TranslateResult` não precisa de derives — o bridge gera o wrapper externo.

### 7.2 Achados de revisão

**[MÉDIO] Bug de design: cache hit retorna `perfect()` independente da qualidade original**

`QualityReport::perfect()` (score 1.0) é retornado em todo cache hit (api.rs linha 98). O cache armazena apenas a string traduzida — o `QualityReport` original não é persistido. Consequência: uma tradução com score original 0.76 (passou por margem mínima) ou mesmo uma tradução `critically_low` (score < 0.60 — armazenada incondicionalmente pela linha 118) retorna score 1.0 na segunda consulta. O Flutter nunca saberá que aquela tradução foi ruim.

O comentário na linha 118 reconhece o armazenamento incondicional: `// Flutter decide como reagir`. Mas o Flutter só pode reagir se receber a informação correta — e em cache hit recebe sempre 1.0.

Dois sub-problemas independentes:
- `QualityReport::perfect()` em hit: o score deveria refletir a qualidade original, não 1.0.
- Armazenamento de traduções `critically_low` no cache: debatível como política, mas se a decisão for armazenar, o score original deve ser preservado.

**[BAIXO] `cosine_similarity` trunca silenciosamente vetores de dimensões diferentes**

`zip` em encoder/mod.rs linha 34 trunca ao menor vetor sem warning ou panic. No uso normal (mesmo engine, sempre 384D), risco zero. Mas `evaluate()` não valida que `src_embedding.len() == tgt_embedding.len()`. Edge case defensivo ausente.

**[BAIXO] `quality_semantic_inversion` sem assert** (já registrado pelo Tester — confirmado)

Sem assert, não detecta regressão se o modelo for trocado ou thresholds alterados. Sugestão para iteração futura: `assert!(report.score < 0.90)` como piso mínimo.

**[BAIXO] Borderline `QUALITY_WARN_THRESHOLD` (0.60 exato) sem teste unitário** (já registrado pelo Tester — confirmado)

### 7.3 Pontos positivos

- Lógica de `evaluate()` é simples e correta. Sem branches ocultos.
- Thresholds documentados com justificativa de modelo (0.75-0.95 para PT-EN correto).
- Testes unitários de borda (0.75 exato, 0.74 exato, vetor zero) são exemplares.
- Comentários em api.rs são claros sobre responsabilidade de cada step do pipeline.
- Nenhuma lógica duplicada — `evaluate()` é o único lugar que computa o score.
- Clippy limpo, 24 testes passando.

### 7.4 Gaps consolidados

| # | Gap | Severidade | Bloqueante? | Origem |
|---|---|---|---|---|
| G1 | Cache hit retorna `perfect()` independente da qualidade original | Média | Não (workaround aceitável por ora) | Revisor |
| G2 | Traduções `critically_low` armazenadas no cache sem preservar score | Média | Não | Revisor |
| G3 | `quality_semantic_inversion` sem assert | Baixa | Não | Tester (confirmado) |
| G4 | Borderline `QUALITY_WARN_THRESHOLD` sem teste unitário | Baixa | Não | Tester (confirmado) |
| G5 | `evaluate()` sem validação de dimensão de vetores | Baixa | Não | Revisor |

G1 e G2 são o mesmo problema raiz: o cache deveria persistir o score original junto com a tradução, ou ao menos marcar que a tradução veio de um cache hit com qualidade degradada. Nenhum é bloqueante para MOT-04 porque a lógica central de `quality::evaluate` está correta — mas devem ser endereçados antes de MOT-04 ser exposta ao Flutter em produção.

### 7.5 Veredicto

**APROVADO COM RESSALVAS**

A implementação central (`quality/mod.rs`, `evaluate()`, thresholds, testes unitários) está correta e bem testada. A integração no pipeline de `translate_cached` funciona. Os derives FFI estão corretos. Não há deadlock.

A ressalva principal (G1/G2) é uma imprecisão semântica na camada de cache: o Flutter receberá `quality.score = 1.0` em cache hits independentemente da qualidade real da tradução armazenada. Isso não compromete o funcionamento da task isolada, mas cria uma mentira observável na API pública antes da integração Flutter. Recomendo registrar no ROADMAP como debt técnico de MOT-04 a ser resolvido na task de integração Flutter ou em uma MOT-04b.
