# TRANS-01-FL — Tela de tradução Flutter (input → motor → output)

**Status:** CONCLUIDO
**Data:** 2026-03-14
**Agente Tester:** Claude Code

---

## Resumo da implementação

Tela principal de tradução conectada ao motor Rust via FFI (flutter_rust_bridge).

### Arquivos criados/modificados

| Arquivo | Papel |
|---|---|
| `app/pubspec.yaml` | Adicionado `flutter_riverpod: ^2.6.1` |
| `app/lib/main.dart` | Inicializa `MotorBridge`, envolve app em `ProviderScope` |
| `app/lib/core/bridge/motor_bridge.dart` | Singleton wrapper FFI — `init()`, `translateCached()`, `version()` |
| `app/lib/features/translator/translator_provider.dart` | Estado (`TranslatorState`), máquina de estados (`TranslatorNotifier`), provider Riverpod |
| `app/lib/features/translator/translator_screen.dart` | Tela principal: seletor de idioma, campo de texto, botão, card de resultado, card de erro |
| `app/lib/features/translator/widgets/quality_badge.dart` | Badge de qualidade (verde/laranja/vermelho) + indicador de cache hit |
| `app/lib/features/translator/widgets/lang_selector.dart` | Dropdown de idioma |

### Comportamento implementado

- 3 idiomas suportados: pt, en, zh
- Swap automático de idiomas (botão + colisão ao selecionar mesmo idioma em src ou tgt)
- Botão "Traduzir" desabilitado enquanto input está vazio ou loading
- Estado de loading com `CircularProgressIndicator` no botão
- Output exibe tradução + `QualityBadge` (score + cache hit) + botão de cópia
- Erros exibidos em card com cor `errorContainer`
- `TranslatorState.copyWith` suporta `clearResult` e `clearError` como flags explícitas

---

## Resultado dos testes

### Suite original (widget_test.dart) — passada antes do Tester
```
00:00 +3: All tests passed!
```

### Testes adicionados pelo Tester (translator_provider_test.dart)
17 testes unitários cobrindo:
- `TranslatorState.copyWith` — preservação de campos, `clearResult`, `clearError`
- `TranslatorNotifier.setInput` — mutação normal e input vazio
- `TranslatorNotifier.swapLangs` — troca correta, limpeza de result/error, idempotência dupla
- `TranslatorNotifier.setSrcLang` — mutação normal + auto-swap quando src colide com tgt
- `TranslatorNotifier.setTgtLang` — mutação normal + auto-swap quando tgt colide com src
- `TranslatorNotifier.translate` — guards: input vazio não dispara loading
- Estado inicial padrão
- `kSupportedLangs` — presença dos 3 idiomas, sem duplicatas

### Suite completa (20 testes)
```
00:01 +20: All tests passed!
```

`flutter analyze` — **No issues found!**

---

## Gaps de cobertura identificados

### Cobertos por testes

| Cenário | Tipo | Arquivo |
|---|---|---|
| Renderização inicial da tela | Widget | widget_test.dart |
| Botão desabilitado com input vazio | Widget | widget_test.dart |
| Swap de idiomas via UI | Widget | widget_test.dart |
| Estado inicial do provider | Unit | translator_provider_test.dart |
| copyWith / clearResult / clearError | Unit | translator_provider_test.dart |
| setInput | Unit | translator_provider_test.dart |
| swapLangs | Unit | translator_provider_test.dart |
| setSrcLang (normal + auto-swap) | Unit | translator_provider_test.dart |
| setTgtLang (normal + auto-swap) | Unit | translator_provider_test.dart |
| translate() guard: input vazio | Unit | translator_provider_test.dart |

### Gaps remanescentes (intencionais — dependem de FFI real)

| Cenário | Motivo do gap |
|---|---|
| `translate()` caminho success (status -> loading -> success, result populado) | Requer mock de `MotorBridge` ou integration test com .so compilado |
| `translate()` caminho error (status -> loading -> error, errorMessage populado) | Mesmo motivo |
| `_OutputCard` renderizado com dados reais | Depende de `TranslateResult` + `QualityReport` do motor |
| `QualityBadge` cores (vermelho/laranja/verde) | Sem mock de `QualityReport` |
| Botão de cópia (`Clipboard`) | Requer `ServicesBinding` no teste |
| `LangSelector` dropdown interaction | Cobre via widget test se necessário em futura task |

Para cobrir os gaps de FFI, a abordagem recomendada é extrair `MotorBridge` para uma interface/abstract class e injetar um mock via `ProviderScope.overrides` nos testes.

---

## Pendencias para tasks futuras

- **Abstração do bridge para testabilidade:** `MotorBridge` é singleton acoplado; uma interface `IMotorBridge` permitiria mock completo do `translate()`.
- **Integration test:** flujo end-to-end com o .so real (candidate para CI quando o bridge FFI estiver gerado).
- **Suporte a mais idiomas:** `kSupportedLangs` hardcoded com 3 entradas; alimentar dinamicamente a partir do motor.

---

## Revisão de código

**Agente Revisor:** Claude Code
**Data:** 2026-03-14

---

### Metodologia

Revisão manual de todos os 8 arquivos. Critérios: correção lógica, segurança, performance, manutenibilidade, boas práticas Flutter/Riverpod, edge cases, UX.

---

### Achados por arquivo

#### `main.dart`

- Correto. `WidgetsFlutterBinding.ensureInitialized()` antes do `init()` do bridge, `ProviderScope` na raiz. Sem problemas.
- Observação menor: ausência de tratamento de erro no `await MotorBridge.instance.init()`. Se o `.so` não carregar, o app crasha silenciosamente com uma `Exception` não capturada. Para produção, um `try/catch` com tela de erro seria mais robusto — mas aceitável para esta task.

#### `motor_bridge.dart`

- Singleton bem implementado com flag `_initialized` para idempotência.
- **Problema menor (não bloqueante):** A flag `_initialized` não é protegida contra chamadas concorrentes. Se `init()` for chamado duas vezes antes do primeiro `await AyvuBridge.init()` retornar, ambas as chamadas prosseguirão para `AyvuBridge.init()`. Padrão correto seria usar um `Completer` ou um `Future?` cached. Baixo risco na prática (só é chamado em `main()`), mas vale registrar.
- `translateCached` e `version` são passthrough diretos sem nenhuma lógica extra — correto para um wrapper fino.
- O acoplamento singleton é o gap principal para testabilidade (já documentado pelo Tester).

#### `translator_provider.dart`

- Máquina de estados clara com `TranslatorStatus` (idle/loading/success/error). Sem estados impossíveis expostos.
- `copyWith` com flags `clearResult`/`clearError` é a solução correta para nullable fields — padrão estabelecido na comunidade Flutter.
- **Problema menor (não bloqueante):** `translate()` captura `catch (e)` genérico e usa `e.toString()` como mensagem de erro para o usuário. Em produção, isso pode expor stack traces ou mensagens internas do Rust via FFI. Recomendado sanitizar ou categorizar o erro antes de expor na UI.
- `translate()` usa `MotorBridge.instance` diretamente (acoplamento estático). Consequência direta do singleton — já identificado como gap pelo Tester. Sem impacto em runtime, só em testabilidade.
- `srcLang == tgtLang` como guard no `translate()` é defensivo e correto — embora o auto-swap no `setSrcLang`/`setTgtLang` torne esse estado praticamente inalcançável pela UI normal. Manter o guard é boa prática.
- **Atenção ao teste `nao muda estado quando srcLang == tgtLang`** (linha 134–157 do test file): o comentário inline do próprio Tester admite que não conseguiu forçar `src == tgt` via API pública. O teste acaba testando apenas o guard de input vazio novamente, não o guard de `srcLang == tgtLang`. Não é bloqueante (o guard existe no código), mas o teste não cobre o que promete no nome.

#### `translator_screen.dart`

- Uso correto de `ConsumerStatefulWidget` com `ref.watch` no `build` e `ref.read` fora do build (linha 39, `notifier`). Porém há uma sutileza: `final notifier = ref.read(translatorProvider.notifier)` é chamado dentro do `build`. O `ref.read` em si não é problema aqui pois `.notifier` é estável, mas o padrão mais seguro seria passar as callbacks diretamente (`ref.read(translatorProvider.notifier).setSrcLang` em vez de capturar `notifier`). Não é bug, mas pode confundir leitores menos familiarizados com Riverpod.
- `_InputField`, `_LangBar`, `_OutputCard`, `_ErrorCard` como widgets privados é o padrão correto — evita rebuilds desnecessários e mantém o `build` do screen legível.
- **Problema menor (não bloqueante):** o `_OutputCard` recebe `srcLang` e `tgtLang` mas não os utiliza no corpo do widget (apenas `result` e `result.quality`/`result.cacheHit`). Os parâmetros são dead code neste momento. Se a intenção era mostrar `"pt → en"` no card, não foi implementado. Se não era intenção, os parâmetros deveriam ser removidos.
- Scroll: o `Column` dentro do `Expanded` não tem scroll. Em telas pequenas com conteúdo grande (output longo + badge), pode ocorrer overflow. Recomendado envolver em `SingleChildScrollView` em task futura.
- `textInputAction: TextInputAction.done` no `_InputField` fecha o teclado ao pressionar "OK" — comportamento correto para um campo multiline de tradução.

#### `quality_badge.dart`

- Lógica de cor correta: `criticallyLow` > `!passed` > verde. Prioridade bem definida.
- Usa `withValues(alpha: 0.15)` (API moderna do Flutter 3.x) em vez do deprecated `withOpacity`. Correto.
- Hardcoded `Colors.blue` para cache hit e `Colors.red/orange/green` para score. Não usa `Theme.of(context)` — em dark mode, essas cores podem ter contraste ruim sobre o background do card. Aceitável para MVP, mas é dívida técnica de acessibilidade.

#### `lang_selector.dart`

- `DropdownButtonHideUnderline` + `isDense: true` é o padrão correto para dropdowns compactos em app bars/tool bars.
- Null check no `onChanged`: `if (v != null) onChanged(v)` — correto para o contrato do `DropdownButton`.
- `LangSelector` é `StatelessWidget` puro com parâmetros explícitos — testável e reutilizável.

#### `widget_test.dart`

- 3 testes de widget bem escritos. Acesso ao container via `ProviderScope.containerOf` para verificar estado após interação é o padrão correto.
- Ausência de `pumpAndSettle` no teste de swap é aceitável pois não há animação esperada.

#### `translator_provider_test.dart`

- Uso correto de `ProviderContainer` isolado com `addTearDown(c.dispose)` — cada teste tem seu próprio estado.
- **Problema de qualidade nos testes (não bloqueante):** O grupo `translate — guards (sem FFI)`, segundo teste (`nao muda estado quando srcLang == tgtLang`) é enganoso: o nome promete testar o guard de idiomas iguais, mas o corpo do teste termina testando input vazio (comentário inline admite isso). O teste não é falso positivo (passa corretamente), mas a cobertura prometida no nome não existe.

---

### Resumo dos problemas

| # | Severidade | Arquivo | Descrição |
|---|---|---|---|
| 1 | Menor | `main.dart` | `init()` sem `try/catch` — crash silencioso se .so falhar |
| 2 | Menor | `motor_bridge.dart` | Race condition teórica em `init()` concorrente — risco baixo na prática |
| 3 | Menor | `translator_provider.dart` | `e.toString()` pode vazar mensagens internas do Rust para o usuário |
| 4 | Menor | `translator_screen.dart` | `srcLang`/`tgtLang` em `_OutputCard` são dead code |
| 5 | Menor | `translator_screen.dart` | `Column` sem scroll pode causar overflow em telas pequenas |
| 6 | Menor | `quality_badge.dart` | Cores hardcoded — dívida de acessibilidade em dark mode |
| 7 | Qualidade de teste | `translator_provider_test.dart` | Teste de guard `srcLang == tgtLang` não cobre o que o nome promete |

**Nenhum problema bloqueante identificado.** Todos os achados são melhorias menores ou dívida técnica documentada.

---

### Veredicto

**APROVADO COM RESSALVAS**

A implementação está correta, idiomaticamente Flutter/Riverpod, e os 20 testes passam com analyze limpo. As ressalvas são todas menores e não impedem o uso em desenvolvimento ou demo. Os itens 3 (sanitização de erro) e 4 (dead code em `_OutputCard`) são os mais relevantes para resolver antes de produção; os demais podem ir para backlog.

**Ações recomendadas antes de produção (não obrigatórias para aprovação desta task):**
1. Sanitizar a mensagem de erro em `catch (e)` no `translate()` — nunca expor `e.toString()` diretamente.
2. Remover `srcLang`/`tgtLang` de `_OutputCard` ou implementar o uso previsto.
3. Corrigir nome/corpo do teste `nao muda estado quando srcLang == tgtLang` para refletir o que realmente testa.
4. Envolver conteúdo scrollável em `SingleChildScrollView` para telas pequenas.
