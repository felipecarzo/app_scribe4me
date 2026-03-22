# MOT-02 — Decoder: vetor de intenção → texto (PT-BR ↔ EN)

**Status**: Implementado — aguardando revisão (Revisor)
**Data**: 2026-03-14

---

## Resultado dos Testes

### Testes executados (`cargo test`)

| Teste | Status |
|---|---|
| `decoder::tests::to_nllb_code_all_mapped` | ok |
| `decoder::tests::to_nllb_code_known_langs` | ok |
| `decoder::tests::to_nllb_code_unknown_returns_none` | ok |

Build: sem erros de compilação.

---

## Avaliação de Cobertura

### O que pode ser testado sem rede

A única função isolável sem dependência de rede ou modelo ONNX é `to_nllb_code`. Os 3 testes existentes cobrem:

- mapeamentos conhecidos (pt, en, ja) — ok
- idioma desconhecido retorna `None` — ok
- todos os 8 idiomas mapeados retornam `Some` — ok

**Cobertura de `to_nllb_code`: adequada.** Não há caso de borda relevante faltando nessa função.

### O que NÃO pode ser testado sem rede

`Translator::new()` faz download via `hf_hub` (~1.5 GB). Tudo que depende da struct `Translator` fica fora do escopo de testes unitários offline:

- `Translator::new()` — inicialização com download
- `Translator::translate()` — pipeline encoder → greedy decode → tokenizer decode

### Casos de teste faltando (offline-viáveis)

Há 2 casos que podem ser adicionados sem rede:

**1. `translate` com `src_lang == tgt_lang` é um early-return puro** (linha 78-80 do decoder). Esse caminho poderia ser testado sem modelo se `Translator` fosse construível sem download (ex: via trait/mock). Com a estrutura atual (sem injeção de dependência), não é possível — a construção exige os arquivos ONNX.

**2. `to_nllb_code` com códigos de case errado** (ex: `"PT"`, `"EN"`) — o matcher é case-sensitive e retornaria `None`. Esse comportamento não está documentado nem testado, e pode ser uma fonte de bug se o chamador passar maiúsculas.

---

## Observações sobre `api.rs`

- `translate()` na API pública usa `expect()` — erros de tradução (idioma não mapeado, token ausente) causam panic. Sem retorno de `Result<>` para a camada Flutter.
- O singleton `TRANSLATOR` inicializa lazily na primeira chamada — correto para evitar download no startup, mas sem mecanismo de fallback ou timeout.

---

## Gaps identificados

| # | Descrição | Pode ser testado offline? | Prioridade |
|---|---|---|---|
| G1 | `to_nllb_code` case-sensitive — comportamento não documentado | Sim | Baixa |
| G2 | `translate()` na API usa `expect()` em vez de `Result` | Não (requer modelo) | Média |
| G3 | Sem teste de integração offline para o early-return `src == tgt` | Não sem refactor | Baixa |

---

## Conclusão do Tester

Os 3 testes existentes cobrem **tudo que é testável offline** de forma adequada. Não há teste unitário faltando que seja trivial de adicionar com a estrutura atual.

O gap mais relevante (G2 — panic em vez de Result na API pública) é uma decisão de design, não um bug de lógica. Recomenda-se que o Revisor avalie se `translate()` deveria retornar `Result<String, String>` em vez de `String` com `expect`.

**Aprovado para Revisor.**

---

## Revisão de Código (Revisor)

**Data**: 2026-03-14

---

### decoder/mod.rs

**Correctness**

- Pipeline encoder → greedy decode → decoder está correto estruturalmente. Inputs nomeados batem com o modelo NLLB-200 Xenova: `input_ids`, `attention_mask` no encoder; `input_ids`, `encoder_hidden_states`, `encoder_attention_mask` no decoder.
- O argmax usa `partial_cmp` com fallback `Equal` — correto para NaN safety em f32.
- `dec_ids[1..]` na decodificação final descarta corretamente o token de idioma inicial (forced BOS).
- Early-return `src_lang == tgt_lang` (linha 78) está correto.

**Bug potencial — offset do argmax (linha 132)**

```rust
let offset = (dec_len - 1) * vocab_size;
```

`dec_len` é o tamanho atual de `dec_ids` antes de adicionar o token novo. O logit do último token gerado está em `offset = (dec_len - 1) * vocab_size`. Isso está correto: na iteração 1, `dec_len = 1`, `offset = 0`, pega o logit da posição 0, que é o único token presente. Sem bug.

**Problema real — `unwrap_or(tgt_lang)` em src_lang (linha 82)**

```rust
let tgt_nllb = to_nllb_code(tgt_lang).unwrap_or(tgt_lang);
```

Se `tgt_lang` for um código desconhecido (ex: `"xx"`), `to_nllb_code` retorna `None` e o fallback passa `"xx"` direto para o vocab lookup — que vai falhar com `ok_or_else(|| format!("Token não encontrado: xx"))` e retornar um `Err`. O erro é propagado corretamente via `?`. Não é um bug, mas o comportamento de `src_lang` é assimétrico: `src_lang` é passado ao tokenizador via encoding mas não tem validação equivalente. Risco baixo (o tokenizador aceita texto sem saber o idioma), mas a inconsistência na validação pode confundir.

**Performance — clone desnecessário no loop (linhas 118-120)**

`hidden_flat.clone()` e `attn_mask.clone()` a cada iteração do greedy loop. Para sequências longas (até 512 tokens), isso é memória e CPU desperdiçados. Não é um bug funcional, mas é uma ineficiência clara. O hidden state do encoder não muda — deveria ser reutilizado sem clone se a API do `ort` permitir.

**Thread-safety**

`Translator` usa `&mut self` em `translate()` — correto, protegido pelo `Mutex<Translator>` no singleton. Sem problema.

---

### api.rs

**A questão do `.expect()` vs `Result` na FFI**

O Tester levantou corretamente: `translate()` retorna `String` e usa `.expect()` internamente. A pergunta é: isso é aceitável para flutter_rust_bridge?

**Resposta direta: não é ideal, mas é aceitável no estado atual — com ressalva.**

flutter_rust_bridge 2.x suporta `Result<T, E>` nativamente: uma função que retorna `Result<String, String>` é mapeada para um `Future<String>` no Dart que pode lançar exceção capturável. Com `.expect()`, um panic no lado Rust causa abort no processo Dart — não há como capturar do lado Flutter.

Os cenários que geram panic hoje:
1. `Translator::new()` falha (download interrompido, arquivo corrompido) → panic no `get_or_init`
2. `translate()` retorna `Err` (token não encontrado para idioma) → panic no `.expect()`
3. Mutex envenenado → panic (esse caso é genuinamente irrecuperável, então `.expect()` é aceitável aqui)

O cenário 1 é o mais grave: acontece na primeira chamada de `translate()` e é irrecuperável. O cenário 2 é evitável com input sanitizado no lado Flutter, mas não deveria depender disso.

**Veredicto sobre o `.expect()`**: Para Sprint 0/prototipagem, aceitável. Para produção, `translate()` deve retornar `Result<String, String>` para permitir tratamento de erro no Flutter sem abort.

**Consistência com `embed_text`**

`embed_text` também usa `.expect()` — o padrão é consistente. Ambos devem ser corrigidos juntos quando a FFI for estabilizada.

---

### Gaps confirmados / novos

| # | Descrição | Severidade | Ação recomendada |
|---|---|---|---|
| G1 (confirmado) | `to_nllb_code` case-sensitive — não documentado | Baixa | Adicionar docstring |
| G2 (confirmado) | `translate()` usa `.expect()` em vez de `Result` — panic em erro de tradução | Média | Mudar para `Result<String, String>` antes da integração Flutter |
| G3 (confirmado) | Sem teste offline para `src == tgt` | Baixa | Aceitar: requer refactor de DI |
| G4 (novo) | `hidden_flat.clone()` + `attn_mask.clone()` a cada iteração do greedy loop | Baixa | Otimizar quando performance for prioridade |
| G5 (novo) | `src_lang` não é validado contra `to_nllb_code` — assimétrico com `tgt_lang` | Baixa | Adicionar validação ou documentar comportamento |

---

### Veredicto

**APROVADO COM RESSALVAS**

O código está correto funcionalmente, compila limpo, e o design do singleton thread-safe é adequado. Os testes cobrem o que é possível offline.

As ressalvas não bloqueiam Sprint 0, mas devem ser resolvidas antes da integração com Flutter:

- **G2 é obrigatório antes da integração FFI**: `translate()` (e `embed_text()`) devem retornar `Result` para evitar abort no processo Dart em runtime.
- **G4 é recomendado** quando houver benchmark de performance real.
- **G1 e G5** podem ser resolvidos com documentação ou validação simples.
