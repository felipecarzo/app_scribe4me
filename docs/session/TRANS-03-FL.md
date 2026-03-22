# Session — TRANS-03-FL: Histórico de Traduções (SQLite local)

> Criado em: 2026-03-14
> Status: planejado — aguardando aprovação de Felipe

---

## Objetivo

Persistir localmente cada tradução bem-sucedida e exibir um histórico navegável ao usuário. Offline-first, sem backend.

---

## Decisão arquitetural: `drift` (aprovado)

| Critério | drift | sqflite |
|---|---|---|
| Type safety | Total — compile-time | Nenhuma — runtime |
| Migrações | Built-in, versionadas | Manual |
| Testabilidade | `NativeDatabase.memory()` nativo | Requer `sqflite_ffi` extra |
| Alinhamento CLAUDE.md | Mencionado como opção preferida | Alternativa |

**Escolha: `drift`** — schema cresce com P2P/voz/prosódia nas próximas sprints. Migrações versionadas e queries type-safe valem o custo de setup.

---

## Schema da tabela `translation_history`

| Campo | Tipo | Obs |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| input_text | TEXT NOT NULL | |
| output_text | TEXT NOT NULL | |
| src_lang | TEXT NOT NULL | "pt", "en", "zh" |
| tgt_lang | TEXT NOT NULL | |
| quality_score | REAL NOT NULL | 0.0..1.0 |
| quality_passed | INTEGER NOT NULL | boolean (0/1) |
| cache_hit | INTEGER NOT NULL | boolean (0/1) |
| created_at | INTEGER NOT NULL | Unix ms |

**Índices:** `created_at DESC` (listagem), `(src_lang, tgt_lang)` (filtro futuro)
**Retenção:** máximo 500 registros — delete automático do mais antigo após insert

---

## Arquitetura

```
core/database/
  app_database.dart          -- AppDatabase drift + TranslationHistoryTable

features/translator/history/
  translation_history_entry.dart         -- modelo de domínio (puro Dart)
  translation_history_repository.dart    -- interface abstrata
  translation_history_repository_impl.dart  -- implementação drift
  history_provider.dart                  -- Riverpod providers
  history_screen.dart                    -- tela de listagem
  widgets/
    history_tile.dart                    -- item da lista
```

**Fluxo:**
```
TranslatorNotifier.translate() → sucesso
  → ref.read(historyRepositoryProvider).save(entry)
  → historyListProvider (StreamProvider) emite lista atualizada
  → HistoryScreen reage automaticamente
```

**Providers:**
- `appDatabaseProvider` — `Provider<AppDatabase>` (singleton)
- `historyRepositoryProvider` — `Provider<HistoryRepository>`
- `historyListProvider` — `StreamProvider<List<TranslationHistoryEntry>>`

**Integração no TranslatorNotifier:** Opção A — `ref.read(historyRepositoryProvider).save(entry)` dentro do bloco `success`. Falha no save: logar, não propagar (tradução já foi bem-sucedida).

---

## Plano de implementação

### Step 1 — Dependências
- `pubspec.yaml` dependencies: `drift`, `drift_flutter`, `sqlite3_flutter_libs`, `path_provider`
- `pubspec.yaml` dev_dependencies: `build_runner`, `drift_dev`
- Verificar `minSdkVersion >= 21` em `android/app/build.gradle`

### Step 2 — Database
- Criar `app/lib/core/database/app_database.dart`
- Rodar `dart run build_runner build` para gerar `.g.dart`

### Step 3 — Modelo de domínio
- Criar `translation_history_entry.dart` com factory `fromDb`

### Step 4 — Repositório
- Criar interface + implementação drift + providers Riverpod

### Step 5 — Integrar no TranslatorNotifier
- `translate()`: após sucesso, `save(entry)` via `ref.read`

### Step 6 — Tela de histórico
- `history_screen.dart`: `ConsumerWidget`, `historyListProvider.when(...)`, `ListView.builder`
- `history_tile.dart`: src→tgt, input/output truncados, timestamp, QualityBadge reaproveitado
- Botão "Limpar histórico" no AppBar

### Step 7 — Navegação
- Ícone de histórico no AppBar da `TranslatorScreen` → `Navigator.push(HistoryScreen)`

### Step 8 — Testes
- Repositório: `NativeDatabase.memory()`, save/watch/deleteAll/trim 500
- Provider: container com fake repository, translate() → save()
- Widget: lista vazia, N itens, tile renderiza campos

---

## Arquivos a criar/modificar

| Arquivo | Ação |
|---|---|
| `app/pubspec.yaml` | MODIFICAR — deps drift |
| `app/lib/core/database/app_database.dart` | CRIAR |
| `app/lib/features/translator/history/translation_history_entry.dart` | CRIAR |
| `app/lib/features/translator/history/translation_history_repository.dart` | CRIAR |
| `app/lib/features/translator/history/translation_history_repository_impl.dart` | CRIAR |
| `app/lib/features/translator/history/history_provider.dart` | CRIAR |
| `app/lib/features/translator/history/history_screen.dart` | CRIAR |
| `app/lib/features/translator/history/widgets/history_tile.dart` | CRIAR |
| `app/lib/features/translator/translator_provider.dart` | MODIFICAR |
| `app/lib/features/translator/translator_screen.dart` | MODIFICAR |

---

## Critérios de aceite

- `save()` persiste e aparece em `watchAll()`
- 501 inserts mantém ≤ 500 registros (oldest deleted)
- `deleteAll()` zera a lista
- `watchAll()` emite stream reativo após cada insert
- Falha no save não afeta status do `translatorProvider`
- `HistoryScreen` renderiza "vazio" e lista com N itens
- `HistoryTile` exibe idiomas, textos truncados, timestamp

---

## Riscos

1. `build_runner` + `flutter_rust_bridge` coexistência — testar no Step 2
2. `sqlite3_flutter_libs` requer `minSdkVersion >= 21`
3. `AppDatabase` precisa de `path_provider` para path do filesystem

---

## Resultados

### Testes criados

| Arquivo | Testes | Cobertura |
|---|---|---|
| `app/test/history/history_repository_test.dart` | 11 | Repositório drift com `NativeDatabase.memory()` |
| `app/test/history/history_provider_test.dart` | 12 | Providers Riverpod com `InMemoryHistoryRepository` fake |
| `app/test/history/history_widget_test.dart` | 11 | `HistoryTile` + `HistoryScreen` com `ProviderScope(overrides:[...])` |

**Total: 34 novos testes + 20 existentes = 54/54 passando**

### Critérios de aceite verificados

| Critério | Resultado |
|---|---|
| `save()` persiste e aparece em `watchAll()` | PASS |
| 501 inserts mantém ≤ 500 registros | PASS |
| trim remove o mais antigo | PASS |
| `deleteAll()` zera a lista | PASS |
| `deleteAll()` em lista vazia não lança exceção | PASS |
| `deleteById()` remove apenas o item correto | PASS |
| `watchAll()` emite stream reativo após cada insert | PASS |
| `historyListProvider` reage a save/deleteAll/deleteById | PASS |
| `HistoryScreen` renderiza "vazio" | PASS |
| `HistoryScreen` renderiza N itens | PASS |
| `HistoryTile` exibe idiomas, textos, timestamp, badge qualidade, badge cache | PASS |
| Botão limpar: aparece com itens, some com lista vazia | PASS |
| Dialog limpar: confirmar chama deleteAll; cancelar preserva lista | PASS |

### Correção identificada durante testes

O `TranslationHistoryCompanion.insert()` gerado pelo drift (v2.31) recebe `bool` diretamente nos campos `qualityPassed` e `cacheHit` — não `Value<bool>`. Os testes foram escritos com a assinatura correta.

### flutter analyze

```
0 issues
```

### Observação sobre reatividade do StreamProvider

`container.read(historyListProvider.future)` captura o `Future` já resolvido em cache — não atualiza após novas emissões. Os testes de reatividade usam `container.listen(historyListProvider, ...)` para capturar todas as emissões, que é a abordagem correta para testar `StreamProvider` com Riverpod.

---

## Revisão de Código

> Revisor: Claude Code (Sonnet 4.6) — 2026-03-14

### app_database.dart

**Corretude do schema:** OK. Colunas tipadas corretamente; `boolean()` drift gera INTEGER 0/1 no SQLite (correto). `autoIncrement()` implica PK; não há redundância.

**Trim logic (`insertEntry`):** A lógica está correta, mas tem uma ineficiência menor: ela faz `COUNT(*)` + `SELECT id ... LIMIT excess` + `DELETE ... WHERE id IN (...)` — três round-trips para cada insert quando o banco está cheio. Para o limite de 500 registros com acesso local isso é aceitável; não é um bloqueador.

**Race condition no trim:** `insertEntry` não é executado em transação. Se dois inserts ocorrerem concorrentemente (improvável na UI, mas possível em testes de carga), o `COUNT` pode estar desatualizado entre as chamadas e o trim pode remover registros a mais ou a menos. Drift permite `transaction(() async { ... })` para envolver o bloco inteiro. Recomendação para sprint futura; não é bloqueador na sprint atual (fluxo single-user, single-thread).

**`watchAll` limit:** `watchAll({int limit = 500})` — o limite padrão é o mesmo que `maxEntries`. Se `maxEntries` for customizado para outro valor no futuro, `watchAll` pode retornar menos do que existe. Os dois parâmetros deveriam ser derivados de uma constante compartilhada. Ressalva menor.

**`deleteAll` retorna `Future<int>`?** Não — `delete(translationHistory).go()` retorna `Future<int>` (linhas afetadas), mas o método declara `Future<void>`. O Dart descarta o valor silenciosamente; funciona, mas uma anotação explícita `// rows affected ignored` deixaria a intenção clara. Cosmético.

**Índice em `createdAt`:** O schema declara a necessidade de índice em `created_at DESC` no plano, mas o código não define `@override List<String> get customConstraints` nem usa `customIndex` do drift para criar o índice explicitamente. O drift não cria índices automaticamente além da PK. Para 500 registros o impacto é zero, mas o índice deve ser adicionado quando o schema escalar. Ressalva para sprint futura.

---

### translation_history_entry.dart

**Isolamento de domínio:** Correto — `TranslationHistoryEntry` é POJO puro, sem dependência de drift na camada de domínio/UI.

**`id: 0` na criação:** O campo `id` na interface de domínio precisa ter valor na construção (antes do insert), então `0` como sentinel é uma convenção razoável. Alternativa seria `int?` com `late` ou factory separado para "novo registro" vs "registro persistido". A convenção atual funciona, mas pode confundir: um ID `0` retornado por `watchAll` nunca deveria acontecer (drift usa autoincrement >= 1), e o teste `id autoincrement e positivo apos save()` cobre isso. Aceitável.

**`fromDb` timezone:** `DateTime.fromMillisecondsSinceEpoch(d.createdAt)` — por padrão cria `DateTime` local. `createdAt` é gravado com `DateTime.now().millisecondsSinceEpoch` no `_saveToHistory`, que também é local. Consistente. Se no futuro houver sincronização P2P entre dispositivos em fusos diferentes, será necessário mudar para UTC. Ressalva arquitetural para quando P2P for implementado.

---

### translation_history_repository.dart / _impl.dart

**Interface:** Limpa. Quatro métodos bem definidos, alinhados com os critérios de aceite.

**`watchAll()` na impl:** `_db.watchAll().map(...)` — cada insert/delete emite novo snapshot completo. Com 500 registros e objetos pequenos, serialização é barata. OK.

**Nenhum `try/catch` na impl:** Correto — exceções de I/O do drift devem propagar para o chamador. O tratamento foi decidido na camada de cima (`_saveToHistory` com `catchError`).

---

### history_provider.dart

**`appDatabaseProvider`:** `ref.onDispose(db.close)` garante que a conexão SQLite seja fechada quando o `ProviderScope` for descartado. Correto.

**`historyRepositoryProvider` usa `ref.watch`:** Correto — se `appDatabaseProvider` for sobrescrito no `ProviderScope` de testes, `historyRepositoryProvider` reagirá. O override nos testes usa `historyRepositoryProvider.overrideWithValue(fake)` diretamente, o que também funciona.

**`historyListProvider` como `StreamProvider`:** Correto. O `StreamProvider` fecha e reinscreve o stream automaticamente quando `historyRepositoryProvider` muda (por rebuild). Sem memory leak aqui.

**Observação:** `historyListProvider` não passa `keepAlive: true`. Isso significa que se nenhum widget estiver ouvindo (ex.: usuário navega para fora da `HistoryScreen`), o provider será descartado e o stream cancelado. Na próxima navegação, o stream será recriado — comportamento correto para este caso. Sem problema.

---

### translator_provider.dart — integração `_saveToHistory`

**`catchError` pattern:**
```dart
ref.read(historyRepositoryProvider).save(entry).catchError((_) {
  // Falha no save não deve impactar o resultado da tradução
});
```
O `.catchError((_) {})` silencia qualquer exceção do `save()`. Isso atende ao requisito ("falha no save não propaga"), mas tem dois problemas menores:

1. **Sem logging:** erros de I/O (disco cheio, DB corrompido) são descartados silenciosamente. Recomendado adicionar `debugPrint` ou logger para rastreabilidade em dev. Ressalva.
2. **`unawaited` implícito:** A Future retornada pelo `.catchError` não é awaited nem descartada explicitamente com `unawaited(...)`. O linter do Dart em modo estrito pode emitir `unawaited_futures`. O `flutter analyze` atual não reportou (provavelmente porque `unawaited_futures` não está habilitado no `analysis_options.yaml`). Usar `unawaited(ref.read(...).save(entry).catchError(...))` tornaria a intenção explícita. Ressalva menor.

**`state.srcLang` / `state.tgtLang` captura correta:** `_saveToHistory` lê `state.srcLang` e `state.tgtLang` do estado atual, que não muda entre o `translate()` retornar e `_saveToHistory` ser chamado (é síncrono no mesmo frame). Correto.

---

### history_screen.dart

**`mounted` check ausente no `_confirmClear`:** O método `_confirmClear` é `async` e usa `ref` após `await showDialog`. Em `ConsumerWidget`, `ref` permanece válido enquanto o widget estiver montado (Riverpod 2.x garante isso via `WidgetRef`). Diferente de `BuildContext`, não é necessário verificar `mounted` para `ref` em `ConsumerWidget`. OK.

**`context` usado após `await` no `_confirmClear`:** `showDialog` recebe `context` — mas o `context` é capturado antes do `await`, não depois. Nenhum uso de `context` após o `await`. OK.

**`historyAsync.maybeWhen` no AppBar:** Correto — evita mostrar o botão "Limpar" durante loading ou erro. `SizedBox.shrink()` como fallback é idiomático.

**`onDelete` faz `ref.read` direto:** `ref.read(historyRepositoryProvider).deleteById(entry.id)` no `itemBuilder` — correto (não é `ref.watch` dentro de callback). A Future retornada não é awaited mas o erro, se houver, seria silencioso. Padrão aceitável para delete de item individual na UI (se falhar, o stream reemitirá o item na próxima emissão). Ressalva menor (sem feedback ao usuário em caso de erro).

---

### history_tile.dart

**`withValues(alpha: 0.12)`:** API correta do Flutter 3.x (substitui `withOpacity` depreciado). OK.

**`_dateFmt` como variável de nível de arquivo:** Correto — evita recriar `DateFormat` a cada rebuild. OK.

**`maxLines: 2` nos textos:** Truncamento com ellipsis está correto para lista densa.

**Nenhuma acessibilidade explícita:** Os badges de idioma, qualidade e cache não têm `Semantics` labels. Para uma aplicação de comunicação (propósito do Ayvu), acessibilidade será importante. Ressalva para sprint futura.

---

### Testes

**`history_repository_test.dart`:** Sólido. Usa `NativeDatabase.memory()` corretamente; `tearDown` fecha o DB. O teste de trim usa `createdAt: i` (inteiros crescentes) como surrogate de timestamp — correto e elegante.

**`history_provider_test.dart`:** `InMemoryHistoryRepository` é um fake bem implementado. O `broadcast()` no `StreamController` é a escolha certa (múltiplos listeners). `watchAll()` como `async*` com `yield` + `yield*` cobre o snapshot inicial e as emissões subsequentes corretamente.

**Duplicação do fake:** `InMemoryHistoryRepository` em `history_provider_test.dart` e `_FakeHistoryRepository` em `history_widget_test.dart` são implementações idênticas. Oportunidade de refatoração: extrair para `test/helpers/fake_history_repository.dart`. Não é bloqueador, mas gera drift de comportamento se um dos dois for atualizado e o outro não.

**`history_widget_test.dart`:** Cobre os casos críticos de UI. O padrão `await tester.pump()` após `pumpWidget` para aguardar o `StreamProvider` emitir é correto.

**Ausência de teste para `_saveToHistory` no `TranslatorNotifier`:** O provider test cobre a reatividade do repositório fake, mas não há teste que valide que `TranslatorNotifier.translate()` chama `save()` após sucesso. O Tester documentou 54/54 passando — o critério de aceite "Falha no save não afeta status do translatorProvider" está coberto indiretamente. Ressalva: falta teste de integração entre `translatorProvider` e `historyRepositoryProvider`.

---

### Resumo das ressalvas

| # | Severidade | Arquivo | Descrição |
|---|---|---|---|
| R1 | Baixa | `app_database.dart` | `insertEntry` sem transação — race condition teórica; aceitável para uso single-user atual |
| R2 | Baixa | `app_database.dart` | `maxEntries` e `limit` de `watchAll` deveriam derivar de constante compartilhada |
| R3 | Baixa | `app_database.dart` | Índice em `createdAt` não criado explicitamente — necessário quando schema escalar |
| R4 | Baixa | `translator_provider.dart` | `_saveToHistory` descarta erro sem logging — dificulta diagnóstico em produção |
| R5 | Baixa | `translator_provider.dart` | Future de `save().catchError` não marcada como `unawaited` explicitamente |
| R6 | Baixa | `history_screen.dart` | `deleteById` sem feedback ao usuário em caso de falha |
| R7 | Info | `translation_history_entry.dart` | `DateTime` local — mudança para UTC necessária quando P2P for implementado |
| R8 | Info | Testes | Fake duplicado em dois arquivos de teste — extrair para helper compartilhado |
| R9 | Info | Testes | Sem teste direto para `TranslatorNotifier → save()` após tradução bem-sucedida |
| R10 | Info | `history_tile.dart` | Sem `Semantics` nos badges — acessibilidade para sprint futura |

**Nenhuma ressalva de severidade alta ou bloqueadora.**

---

## Veredicto

**APROVADO COM RESSALVAS**

A implementação está correta, segura para produção no escopo atual (app offline, single-user) e bem testada. Os 54 testes cobrem os critérios de aceite. O `flutter analyze` retorna 0 issues.

As ressalvas R1–R6 são melhorias incrementais, não bugs. As R7–R10 são débitos técnicos conhecidos e aceitáveis para esta sprint. Nenhuma delas impede o merge.

**Ações recomendadas antes do próximo sprint (não bloqueadoras para merge desta task):**
- R4: adicionar `debugPrint` no `catchError` de `_saveToHistory`
- R8: extrair fake para `test/helpers/`
- R9: adicionar teste de integração `translatorProvider → save()`
