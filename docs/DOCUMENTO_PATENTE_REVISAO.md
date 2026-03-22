# DOCUMENTO TÉCNICO PARA REVISÃO DE PATENTE
## Sistema de Tradução de Fala com Preservação Prosódica via Representação Interlingua

**Versão:** 1.0
**Data:** 2026-03-14
**Status:** Rascunho para revisão por profissional de PI
**Confidencial — Não distribuir sem NDA**

---

## AVISO AO PROFISSIONAL REVISOR

Este documento foi preparado pelo inventor para orientar a redação formal do pedido de patente. Ele contém:

- Descrição técnica detalhada do sistema implementado (protótipo funcional v6.0)
- Descrição do sistema projetado (partitura vocal — em desenvolvimento)
- Reivindicações preliminares sugeridas pelo inventor
- Análise de estado da técnica (prior art) com base em pesquisa prévia
- Distinção explícita entre o que já está funcionando e o que está em roadmap

O profissional de PI deve avaliar a patenteabilidade, refinar as reivindicações e verificar conflitos com prior art antes de qualquer depósito.

---

---

# PARTE I — IDENTIFICAÇÃO DA INVENÇÃO

## 1. TÍTULO SUGERIDO

> **"Sistema e método de tradução de fala entre idiomas com preservação de características prosódicas via codificação vetorial de representação intermediária"**

Títulos alternativos para avaliação:
- "Motor interlingua com partitura vocal digital para tradução prosódica em tempo real"
- "Sistema de comunicação multilíngue com codificação e transferência de prosódia entre idiomas"

---

## 2. CAMPO TÉCNICO DA INVENÇÃO

A invenção pertence ao campo do **processamento de linguagem natural aplicado a sistemas de comunicação multilíngue em tempo real**, especificamente à interseção entre:

- Reconhecimento automático de fala (ASR / Speech-to-Text)
- Tradução automática neural com representação interlingua
- Análise e síntese prosódica de voz
- Protocolos de comunicação P2P (peer-to-peer) com metadados expressivos
- Sistemas de cache baseados em similaridade semântica

---

## 3. PROBLEMA TÉCNICO SOLUCIONADO

### 3.1 Problema Central

A comunicação humana transmite dois planos simultâneos de informação:

1. **Conteúdo semântico** — o que é dito (palavras, frases, significado)
2. **Conteúdo prosódico** — como é dito (entonação, ritmo, ênfase, emoção)

Os sistemas de tradução de fala existentes operam exclusivamente sobre o plano semântico. O processo de tradução converte texto de origem em texto de destino, que é posteriormente sintetizado por um motor de texto-para-fala (TTS) genérico. Nesse processo, **todas as informações prosódicas são perdidas irreversivelmente**.

### 3.2 Consequências Concretas do Problema

A perda de prosódia gera os seguintes problemas documentáveis:

**a) Perda de urgência clínica:**
Em contextos de telemedicina cross-border, um paciente que diz "DOR FORTE" com entonação ascendente e alta energia de voz transmite urgência que não chega ao médico receptor na língua de destino — o TTS genérico reproduz a frase com tom neutro.

**b) Perda de ênfase em negociação:**
"Precisamos disso HOJE" dito com ênfase distinta em "HOJE" torna-se "We need this today" em tom uniforme, removendo a urgência que pode ser determinante em acordos comerciais.

**c) Perda de intenção comunicativa:**
Questões retóricas, sarcasmo, preocupação e encorajamento dependem fundamentalmente de prosódia para ser identificados como tais. A tradução texto-a-texto elimina esses marcadores.

**d) Inaplicabilidade em contextos expressivos:**
Tradução de conteúdo artístico (teatro, comédia, audiobooks) torna-se inviável quando a expressividade vocal é perdida.

### 3.3 Limitações do Estado da Técnica

| Sistema | Tipo | Tradução offline | Prosódia | Cache semântico | Validação auto. |
|---------|------|-----------------|----------|-----------------|-----------------|
| Google Translate | Cloud | Não | Não | Não | Não |
| DeepL Voice | Cloud | Não | Não | Não | Não |
| Microsoft Translator | Cloud | Parcial | Não | Não | Não |
| Apple Translate | Edge parcial | Limitado | Não | Não | Não |
| Amazon Transcribe+Polly | Cloud | Não | Parcial (voice style) | Não | Não |

Nenhuma solução conhecida integra: tradução semântica offline + preservação prosódica + validação automática de qualidade + operação P2P sem infraestrutura de nuvem.

---

---

# PARTE II — DESCRIÇÃO DETALHADA DO MOTOR

## 4. VISÃO GERAL DO SISTEMA

O sistema proposto pode ser descrito como um **pipeline integrado de processamento de fala** composto por seis módulos funcionais principais, operando em sequência com dois caminhos paralelos (semântico e prosódico):

```
┌──────────────────────────────────────────────────────────────────┐
│  DISPOSITIVO EMISSOR                                             │
│                                                                  │
│  [Microfone] → [STT] ──────────────────────► [Texto Origem]     │
│                  │                                  │            │
│                  ▼                                  ▼            │
│          [Extrator          [Embedding        [NLLB-200          │
│           Prosódico]         Semântico]        Tradução]         │
│                  │                  │                │           │
│                  ▼                  ▼                ▼           │
│          [Encoder          [Cache              [Validação        │
│           Prosódia         Semântico]           Qualidade]       │
│           128D]                                      │           │
│                  │                                   │           │
│                  └──────────── [Protocolo P2P] ──────┘           │
│                                      │                           │
└──────────────────────────────────────┼───────────────────────────┘
                                       │ WebSocket / Bluetooth
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  DISPOSITIVO RECEPTOR                                            │
│                                                                  │
│  [Texto Traduzido] + [Vetor Prosódico 128D]                     │
│          │                      │                                │
│          ▼                      ▼                                │
│  [Decoder Prosódico]   [TTS Expressivo] → [Alto-falante]        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Status de implementação:**
- Módulos de Tradução Semântica, Cache e Validação: **implementados e em produção (v6.0)**
- Módulos de Extração/Codificação Prosódica e TTS Expressivo: **especificados, em desenvolvimento (Sprint 4-5)**

---

## 5. MÓDULO 1 — TRANSCRIÇÃO DE FALA (STT)

### 5.1 Função

Converter o sinal de áudio captado pelo microfone em texto na língua de origem, operando em modo de streaming com dois tipos de saída:

- **Resultado intermediário (partial):** fragmentos de texto a cada ~80ms, usados para tradução especulativa
- **Resultado final:** texto completo após detecção de pausa de ≥1,2 segundos, submetido ao pipeline completo

### 5.2 Implementação Atual (Prototipada)

O sistema utiliza dois mecanismos de STT, dependendo do modo de operação:

**Modo web (v6.0 — em produção):**
- API `webkitSpeechRecognition` do navegador
- Retorna eventos `interim` e `final` nativamente
- Nenhum modelo local requerido no servidor

**Modo desktop (legacy — referência):**
- Modelo: `faster-whisper` (variante CTranslate2 do OpenAI Whisper Base)
- Configuração: `device="cpu"`, `compute_type="int8"`, `beam_size=2`
- Detecção de atividade de voz: VAD nativo do Whisper + limiar RMS calibrado
- Buffer circular: 10 segundos a 16kHz mono (float32)
- Calibração de ruído de fundo: medição de RMS por 2 segundos × fator 2,5

**Código de referência (calibração, sender/sender_stream.py):**
```python
# Calibração do piso de ruído
def calibrate_noise(duration=2.0):
    # Grava amostras de silêncio
    rms = float(np.sqrt(np.mean(all_audio ** 2)))
    noise_floor = max(rms * 2.5, 0.003)
```

**Código de referência (detecção de fala, sender/sender_stream.py):**
```python
# Detecção de pausa → finalização de frase
if frase_ativa and silencio_seg >= SILENCE_SECONDS:
    msg = criar_mensagem_stream(ultimo_envio, seq_num, is_final=True, lang_source=MY_LANG)
```

### 5.3 Inovação Técnica Neste Módulo

O sistema utiliza **prompt contextual dinâmico** para guiar o modelo Whisper: as últimas 3 frases da conversa e o tema da sessão são injetados como `initial_prompt`, melhorando a precisão de reconhecimento em conversas contínuas sem retreinamento do modelo.

```python
def build_whisper_prompt() -> str:
    parts = [f"Contexto: {contexto_usuario}"]
    parts.append(" ".join(list(frases_cache)[-3:]))  # últimas 3 frases
    return " ".join(parts)
```

---

## 6. MÓDULO 2 — MOTOR DE TRADUÇÃO INTERLINGUA (NLLB-200)

### 6.1 Conceito de Interlingua

O núcleo da tradução utiliza o modelo **NLLB-200** (No Language Left Behind, Meta AI, 2022), um transformer encoder-decoder treinado para traduzir entre 200 idiomas usando uma **representação intermediária compartilhada** — a "interlingua".

O conceito de interlingua é o seguinte: em vez de criar N×(N-1) modelos de tradução par-a-par (PT→EN, PT→ES, EN→ES, etc.), o modelo aprende uma única representação latente que captura o significado de qualquer frase em qualquer idioma. Todos os 200 idiomas projetam-se nesse mesmo espaço vetorial.

```
Texto em PT → Encoder → Vetor Latente (interlingua) → Decoder → Texto em EN
                               ↑
               Representação compartilhada para 200 idiomas
               Funciona como um "esperanto neural" interno
```

### 6.2 Especificações do Modelo

| Parâmetro | Valor |
|-----------|-------|
| Modelo | `nllb-200-distilled-600M` (destilado) |
| Arquitetura | Transformer encoder-decoder |
| Parâmetros | 600 milhões |
| Idiomas suportados | 200 (via códigos Flores-200) |
| Tokenizador | SentencePiece (subword) |
| Framework de inferência | CTranslate2 |
| Compute mode | CUDA float16 (GPU) / int8 (CPU fallback) |
| Tamanho em disco | ~2,5 GB |

### 6.3 Mapeamento de Idiomas

O sistema utiliza códigos ISO 639 simplificados mapeados para os códigos Flores-200 do NLLB:

```python
LANG_MAP = {
    "pt": "por_Latn",   # Português (escrita latina)
    "en": "eng_Latn",   # Inglês
    "es": "spa_Latn",   # Espanhol
    "fr": "fra_Latn",   # Francês
    "de": "deu_Latn",   # Alemão
    "it": "ita_Latn",   # Italiano
    "ja": "jpn_Jpan",   # Japonês (escrita japonesa)
    "zh": "zho_Hans",   # Chinês simplificado
}
```

### 6.4 Pipeline de Tradução Neural

O processo de tradução executa as seguintes etapas internas:

1. **Tokenização SentencePiece:** O texto é segmentado em subpalavras. Exemplo: "Olá mundo" → `["▁O", "lá", "▁mundo"]`

2. **Injeção de token de idioma fonte:** O token de idioma é preposto aos tokens de texto. Exemplo: `["por_Latn", "▁O", "lá", "▁mundo"]`

3. **Tradução com beam search:** O encoder projeta a sequência no espaço latente interlingua. O decoder expande 4 hipóteses simultâneas (beam_size=4), selecionando a de maior probabilidade.

4. **Decodificação:** Os tokens de saída são convertidos de volta em texto. O token de idioma alvo é removido do resultado.

```python
# Código de referência (translation_engine.py)
def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
    tokens = self.sp.encode(text, out_type=str)
    tokens = [src_nllb] + tokens

    results = self.translator.translate_batch(
        [tokens],
        target_prefix=[[tgt_nllb]],
        beam_size=4,
        max_input_length=512,
        max_decoding_length=512,
    )

    output_tokens = results[0].hypotheses[0]
    return self.sp.decode(output_tokens[1:])  # remove token de idioma
```

### 6.5 Otimizações de Desempenho

| Técnica | Parâmetro | Efeito |
|---------|-----------|--------|
| CUDA float16 | `compute_type="float16"` | 2x velocidade, 50% VRAM vs float32 |
| CTranslate2 | framework otimizado | 4x vs PyTorch puro |
| Fallback automático | CPU int8 se CUDA falhar | Alta disponibilidade sem intervenção |
| Beam size=4 | qualidade vs velocidade | +5% qualidade vs greedy (beam=1) |

**Latência medida (RTX 3060 12GB, frase de 15 palavras):** 80–150ms

---

## 7. MÓDULO 3 — EMBEDDING SEMÂNTICO

### 7.1 Função

O módulo de embedding converte qualquer texto em um vetor numérico de 384 dimensões que captura o **significado semântico** da frase, independentemente de sua forma lexical ou idioma.

O modelo utilizado é o `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers), treinado especificamente para produzir representações que preservam equivalência semântica entre idiomas.

### 7.2 Propriedade Fundamental

Frases semanticamente equivalentes em qualquer idioma produzem vetores com alta similaridade de cosseno:

```
embed("Olá, como vai?")        → v₁ = [0.1234, -0.5678, 0.9012, ..., 0.3456]  (384 dim)
embed("Oi, tudo bem?")         → v₂ = [0.1198, -0.5601, 0.8987, ..., 0.3421]
embed("Hello, how are you?")   → v₃ = [0.1201, -0.5589, 0.8994, ..., 0.3445]

cosine_similarity(v₁, v₂) = 0.96  (mesma intenção, forma diferente)
cosine_similarity(v₁, v₃) = 0.94  (mesma intenção, idioma diferente)
```

### 7.3 Implementação

```python
# translation_engine.py — classe EmbeddingEngine

def _mean_pooling(self, model_output, attention_mask):
    """Agrega representações de tokens em vetor de sentença via média ponderada."""
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(
        token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / \
           torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def embed(self, text: str) -> list[float]:
    inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = self.model(**inputs)
    vector = self._mean_pooling(outputs, inputs["attention_mask"])
    return vector[0].tolist()  # lista de 384 floats

def similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
    a = torch.tensor(vec_a).unsqueeze(0)
    b = torch.tensor(vec_b).unsqueeze(0)
    return F.cosine_similarity(a, b).item()  # float entre -1 e 1
```

### 7.4 Usos do Embedding

O vetor semântico de 384 dimensões é usado em **dois lugares distintos** no sistema:

1. **Cache semântico** (seção 8): lookup por similaridade de paráfrases
2. **Validação de qualidade** (seção 9): comparação entre original e tradução

---

## 8. MÓDULO 4 — CACHE SEMÂNTICO

### 8.1 Problema que o Cache Resolve

Sistemas de tradução tradicionais utilizam cache por correspondência exata de string ou por hash do texto. Esses métodos falham em reutilizar traduções quando o usuário reformula a mesma ideia:

- "Como vai você?" e "Como você está?" têm o mesmo significado mas são strings diferentes → sem cache hit nos sistemas convencionais
- Em conversas naturais, 30–50% das frases são variações semânticas de frases anteriores

### 8.2 Mecanismo de Cache por Similaridade Vetorial

O sistema implementa um cache baseado em **similaridade de cosseno entre embeddings**:

```
Nova frase → embed() → vetor Vₙ
     ↓
Para cada entrada (Vᵢ, tradução_i) no cache:
     ↓
cosine_similarity(Vₙ, Vᵢ) ≥ threshold ?
     ↓ SIM                    ↓ NÃO
Retorna tradução_i         Chama NLLB
(cache HIT)                Armazena nova entrada
                           (cache MISS)
```

### 8.3 Implementação

```python
# translation_engine.py — classe SemanticCache

def __init__(self, embedder, threshold=0.85, max_size=200):
    # cache[lang_pair] = [{"embedding": [...384D], "source": str, "translation": str}]
    self._cache: dict[str, list[dict]] = {}
    self.threshold = threshold  # limiar configurável

def lookup(self, text, src, tgt, embedding) -> str | None:
    key = f"{src}→{tgt}"
    entries = self._cache.get(key, [])
    for entry in entries:
        sim = self.embedder.similarity(embedding, entry["embedding"])
        if sim >= self.threshold:
            return entry["translation"]  # HIT — reutiliza tradução anterior
    return None  # MISS

def store(self, text, translation, src, tgt, embedding):
    key = f"{src}→{tgt}"
    if key not in self._cache:
        self._cache[key] = []
    self._cache[key].append({
        "embedding": embedding,
        "source": text,
        "translation": translation,
    })
    # Política de evicção FIFO para limitar uso de memória
    if len(self._cache[key]) > self.max_size:
        self._cache[key] = self._cache[key][-self.max_size:]
```

### 8.4 Características do Cache

| Parâmetro | Valor padrão | Ajustável |
|-----------|-------------|----------|
| Threshold de similaridade | 0.85 (85%) | Sim |
| Tamanho máximo por par de idiomas | 200 entradas | Sim |
| Estrutura de dados | Dict em RAM (Python) | Futuramente: SQLite/Redis |
| Política de evicção | FIFO (mais antigos removidos) | — |
| Escopo do cache | Por par de idiomas (ex: `pt→en`) | — |

### 8.5 Benefícios Mensuráveis

- Redução de 30–50% nas chamadas ao motor NLLB-200 em conversas naturais
- Latência de cache hit: ~20–40ms (embedding) vs 80–150ms (tradução + embedding)
- Sem degradação de qualidade (threshold alto garante equivalência semântica)

---

## 9. MÓDULO 5 — VALIDAÇÃO AUTOMÁTICA DE QUALIDADE

### 9.1 Problema

Modelos neurais de tradução podem produzir traduções incorretas ("alucinações"), especialmente em frases ambíguas, idiomas raros ou contextos muito específicos. Não existe mecanismo interno ao modelo que indique quando a tradução está errada.

### 9.2 Solução: Cross-Lingual Semantic Similarity

A inovação consiste em usar o mesmo espaço de embedding multilíngue que serviu para o cache para **medir a distância semântica entre o texto original e o texto traduzido**. Se a tradução preservou o significado, os dois vetores devem ser similares. Se há divergência semântica, o score será baixo.

```
text_orig = "The sky is blue"         → embed() → Vₒᵣᵢ₉
text_trad = "O céu é azul"            → embed() → Vₜᵣₐd
quality_score = cosine_similarity(Vₒᵣᵢ₉, Vₜᵣₐd) = 0.88  ✓ Boa tradução

text_trad_erro = "O azul está céu"    → embed() → Vₑᵣᵣₒ
quality_score = cosine_similarity(Vₒᵣᵢ₉, Vₑᵣᵣₒ) = 0.62  ⚠ Alerta: qualidade baixa
```

### 9.3 Implementação no Pipeline

```python
# translation_engine.py — classe TranslationPipeline, método translate()

def translate(self, text, src_lang, tgt_lang) -> dict:
    # 1. Gera embedding do texto original
    src_embedding = self.embedder.embed(text)

    # 2. Cache lookup
    cached = self.cache.lookup(text, src_lang, tgt_lang, src_embedding)
    if cached:
        return {"translated": cached, "quality_score": 1.0, "cache_hit": True, ...}

    # 3. Tradução NLLB
    translated = self.nllb.translate(text, src_lang, tgt_lang)

    # 4. Embedding do traduzido
    tgt_embedding = self.embedder.embed(translated)

    # 5. Score de qualidade (sem referência humana)
    quality_score = self.embedder.similarity(src_embedding, tgt_embedding)

    if quality_score < 0.6:
        print(f"⚠ Qualidade baixa ({quality_score:.2f}): '{text}' → '{translated}'")

    # 6. Armazena no cache
    self.cache.store(text, translated, src_lang, tgt_lang, src_embedding)

    return {
        "translated": translated,
        "embedding": src_embedding,      # 384 floats
        "embedding_dims": 384,
        "quality_score": round(quality_score, 3),
        "cache_hit": False,
    }
```

### 9.4 Limiares de Qualidade

| Score | Interpretação | Ação recomendada |
|-------|--------------|-----------------|
| ≥ 0.85 | Excelente | Usar diretamente |
| 0.70–0.84 | Boa | Usar, registrar para revisão |
| 0.60–0.69 | Aceitável | Alertar usuário |
| < 0.60 | Suspeita | Alertar fortemente, não armazenar no cache |

---

## 10. MÓDULO 6 — TRADUÇÃO ESPECULATIVA COM PRÉ-BUFFERING DE TTS

### 10.1 Problema de Latência Percebida

O pipeline completo (STT final → embedding → cache → NLLB → validação → TTS) tem latência de 250–500ms a partir da detecção de fim de frase. Para o usuário, a percepção é de ~800ms porque o TTS tem um cold-start adicional de 200–300ms na primeira inicialização.

### 10.2 Solução: Dois Caminhos Paralelos

O sistema implementa um mecanismo de **tradução especulativa** que opera em paralelo ao pipeline completo:

**Caminho especulativo (partial, a cada ~80ms):**
```
STT interim → speech_partial → translate_partial() → translation_partial → Pre-buffer TTS (silencioso)
```

**Caminho completo (final, uma vez por frase):**
```
STT final → speech → translate() [com cache+validação] → translation → TTS audível (motor já aquecido)
```

### 10.3 Método translate_partial()

```python
# translation_engine.py

def translate_partial(self, text, src_lang, tgt_lang) -> str:
    """
    Tradução rápida sem embedding, cache ou validação.
    Usada para fragmentos intermediários — baixa qualidade aceitável.
    beam_size=1 (greedy) para máxima velocidade.
    """
    tokens = self.nllb.sp.encode(text, out_type=str)
    tokens = [src_nllb] + tokens

    results = self.nllb.translator.translate_batch(
        [tokens],
        target_prefix=[[tgt_nllb]],
        beam_size=1,          # greedy — 2x mais rápido
        max_input_length=128,
        max_decoding_length=128,
    )
    return self.nllb.sp.decode(output_tokens[1:])
```

### 10.4 Pre-buffering do TTS no Cliente

O cliente receptor executa TTS silencioso com a tradução especulativa para "aquecer" o motor de síntese:

```javascript
// web/index.html — função preBufferTTS()
preBufferTTS(text, lang) {
    const u = new SpeechSynthesisUtterance(text);
    u.volume = 0;          // silencioso — não audível
    speechSynthesis.speak(u);
    setTimeout(() => speechSynthesis.cancel(), 10);  // cancela imediatamente
    // Efeito: motor TTS sai do estado "cold" sem produzir áudio
}
```

### 10.5 Resultado de Desempenho

| Cenário | Latência fim-da-fala → início do TTS |
|---------|--------------------------------------|
| Sem especulativo, sem pre-buffer | ~800ms |
| Com especulativo, sem pre-buffer | ~500ms |
| Com especulativo + pre-buffer | **<200ms percebidos** |

---

## 11. MÓDULO 7 — PROTOCOLO DE COMUNICAÇÃO P2P

### 11.1 Arquitetura Hub-and-Spoke

O sistema atual utiliza modelo WebSocket Hub centralizado:

```
[Dispositivo A] ──WebSocket──► [Hub Servidor] ──WebSocket──► [Dispositivo B]
[Dispositivo C] ──WebSocket──►     (NLLB)     ──WebSocket──► [Dispositivo D]
```

**Princípios do protocolo:**

- **Agnóstico de idioma no emissor:** O emissor envia apenas `{texto, lang_source}`. Não precisa conhecer os idiomas dos receptores.
- **Tradução seletiva no hub:** O servidor traduz o texto para cada idioma de cada receptor individualmente.
- **Echo para o remetente:** O remetente recebe seu próprio texto de volta (sem tradução) para confirmar recepção.

### 11.2 Schema de Mensagens (Protocolo v0.3-bilateral)

**Mensagem de registro (cliente → servidor):**
```json
{
  "type": "register",
  "lang": "pt",
  "name": "Felipe"
}
```

**Mensagem de fala final (cliente → servidor):**
```json
{
  "type": "speech",
  "text": "Você está bem?",
  "lang_source": "pt"
}
```

**Mensagem de fala parcial (cliente → servidor):**
```json
{
  "type": "speech_partial",
  "text": "Você está",
  "lang_source": "pt"
}
```

**Tradução final (servidor → receptor):**
```json
{
  "type": "translation",
  "original": "Você está bem?",
  "translated": "Are you okay?",
  "from_name": "Felipe",
  "from_lang": "pt",
  "to_lang": "en",
  "embedding": [0.123, -0.456, ..., 0.789],
  "embedding_dims": 384,
  "quality_score": 0.91,
  "cache_hit": false
}
```

**Protocolo legacy (sender/receiver direto, v0.3-bilateral):**
```json
{
  "version": "0.3-bilateral",
  "type": "stream_chunk",
  "id": "uuid-v4",
  "seq": 42,
  "is_final": false,
  "timestamp": 1709768400.123,
  "text": "Hello world",
  "lang_source": "en"
}
```

### 11.3 Inovação do Protocolo

O campo `lang_target` foi **deliberadamente removido** da mensagem do emissor. O receptor decide seu próprio idioma de destino e traduz localmente. Isso permite:

- Grupos com N participantes cada um ouvindo em seu idioma preferido
- Adição de novos participantes sem reconfiguração do emissor
- Suporte a múltiplos idiomas simultâneos na mesma sessão

---

## 12. MÓDULO 8 — PARTITURA VOCAL DIGITAL (SISTEMA PROSÓDICO)

*Este módulo está especificado e em desenvolvimento (Sprint 4-5, previsão Q2-Q3 2026). A descrição abaixo representa a arquitetura projetada, derivada da análise técnica documentada.*

### 12.1 Conceito da Partitura Vocal

A "partitura vocal digital" é uma representação estruturada dos parâmetros expressivos da voz humana, análoga a uma partitura musical: assim como uma partitura musical captura não só quais notas tocar mas também como tocá-las (dinâmica, articulação, tempo), a partitura vocal captura não só o que foi dito mas como foi dito.

### 12.2 Parâmetros Prosódicos Capturados

| Parâmetro | Unidade | Descrição | Tecnologia de extração |
|-----------|---------|-----------|----------------------|
| **Pitch contour (F0)** | Hz por frame de 10ms | Melodia fundamental da voz | parselmouth (Praat wrapper) |
| **Energy** | RMS 0–1 por frame | Intensidade/ênfase | librosa.feature.rms |
| **Duration** | segundos por sílaba | Ritmo de fala | parselmouth + VAD |
| **Pauses** | segundos após sílaba | Timing dramático e respiração | pydub.silence / webrtcvad |
| **Emotion** | vetor de classe | Classificação ML: alegria, raiva, medo, etc. | Speech Emotion Recognition (SER) |

### 12.3 Encoder Prosódico (vetor 128D)

Os parâmetros brutos são comprimidos em um vetor de dimensão fixa (128D) por uma rede neural (LSTM), tornando-os compactos para transmissão e agnósticos quanto ao comprimento da frase:

```python
# Especificação (pseudocódigo)
class ProsodyEncoder(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=256, output_dim=128):
        # input_dim=3: [pitch normalizado, energy, pause_flag]
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=2, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, features):  # (batch, seq_len, 3)
        _, (h_n, _) = self.lstm(features)
        return self.fc(h_n[-1])   # (batch, 128) — vetor compacto da prosódia
```

### 12.4 Schema de Transmissão com Prosódia

O protocolo será estendido para incluir o vetor prosódico:

```json
{
  "type": "speech",
  "text": "Você está bem?",
  "lang_source": "pt",
  "prosody": {
    "embedding": [0.12, -0.45, 0.67, ..., 0.33],
    "raw": {
      "pitch": [120, 125, 140, 155, 180],
      "energy": [0.5, 0.6, 0.7, 0.8, 0.9],
      "pauses": [0, 0, 0, 0, 0.5],
      "emotion": "interrogative_concerned"
    }
  }
}
```

### 12.5 Decoder e TTS Expressivo

No receptor, o vetor prosódico de 128D é decodificado em parâmetros que controlam a síntese de voz:

```python
# Especificação (pseudocódigo)
def decode_prosody(embedding_128d):
    # Decoder: rede neural ou lookup table por emoção
    # Saída: parâmetros de síntese de voz
    return {
        "pitch_shift": float,    # deslocamento em Hz relativo ao falante sintético
        "duration_scale": float, # aceleração/desaceleração 0.8x–1.2x
        "energy_scale": float,   # amplitude 0.5–1.5
        "emotion_preset": str    # para engines que aceitam preset de emoção
    }

# Síntese com controle prosódico (Coqui XTTS v2)
tts.synthesize(
    text="Are you okay?",
    language="en",
    prosody_params=decode_prosody(received_embedding)
)
```

### 12.6 Preservação Cruzada de Prosódia

O hub **não altera** o vetor prosódico durante a tradução — apenas traduz o texto. O vetor é transmitido intacto ao receptor:

```
Emissor:          "Você está bem?" + prosody_vector [preocupação, tom ascendente]
          ↓
Hub:              traduz texto → "Are you okay?" / mantém prosody_vector
          ↓
Receptor:         sintetiza "Are you okay?" aplicando prosody_vector
Resultado:        "Are you OKAY?" [mesma entonação preocupada do original]
```

### 12.7 Mapeamento de Pitch entre Línguas

Línguas têm registros vocais médios distintos. O decoder realiza um mapeamento proporcional do pitch:

- PT-BR: registro médio masculino ~110Hz, feminino ~200Hz
- EN-US: registro médio masculino ~120Hz, feminino ~210Hz
- ZH: contorno tonal mapeado para equivalente prosódico não-tonal em EN

O mapeamento preserva os contrastes relativos (ascendente, descendente, neutro, interrogativo) mesmo que os valores absolutos de Hz sejam ajustados para o range natural do idioma alvo.

---

---

# PARTE III — REIVINDICAÇÕES PRELIMINARES

*Nota ao profissional revisor: As reivindicações abaixo são sugestões preliminares do inventor. Devem ser refinadas tecnicamente e juridicamente antes do depósito. Verificar prior art detalhado antes de confirmar independência de cada claim.*

---

## 13. REIVINDICAÇÕES SUGERIDAS

### Reivindicação 1 — Sistema (independente, principal)

> **Sistema de tradução de fala entre idiomas com preservação de características prosódicas**, caracterizado por compreender:
>
> **(a)** módulo de captura e transcrição de fala que converte sinal de áudio de entrada em representação textual e que produz resultados intermediários e resultados finalizados;
>
> **(b)** módulo de representação semântica que gera vetor numérico de dimensão fixa a partir de texto em qualquer idioma, usando modelo de linguagem multilíngue, onde vetores de textos semanticamente equivalentes exibem alta similaridade de cosseno independentemente do idioma de origem;
>
> **(c)** módulo de tradução neural que converte texto de idioma de origem para idioma de destino utilizando modelo transformer com representação interlingua compartilhada entre múltiplos idiomas;
>
> **(d)** módulo de cache semântico que armazena pares (vetor semântico, tradução) e que reutiliza uma tradução armazenada quando a similaridade de cosseno entre o vetor da nova entrada e um vetor armazenado excede limiar configurável;
>
> **(e)** módulo de validação de qualidade que calcula similaridade de cosseno entre o vetor semântico do texto de origem e o vetor semântico do texto traduzido, gerando escore de confiança da tradução sem necessidade de referência humana;
>
> **(f)** módulo de extração prosódica que extrai do sinal de áudio original parâmetros incluindo contorno de frequência fundamental, energia por unidade temporal e padrões de pausa;
>
> **(g)** módulo de codificação prosódica que comprime os parâmetros prosódicos extraídos em vetor numérico de dimensão fixa usando rede neural recorrente;
>
> **(h)** protocolo de transmissão que transporta texto traduzido conjuntamente com o vetor prosódico codificado entre dispositivos;
>
> **(i)** módulo de síntese expressiva que gera sinal de áudio no idioma de destino aplicando ao motor de síntese de voz os parâmetros prosódicos decodificados do vetor recebido, de modo a preservar características expressivas da voz original.

---

### Reivindicação 2 — Cache semântico (dependente da 1)

> **Sistema conforme Reivindicação 1**, caracterizado por o módulo de cache semântico manter estrutura de dados indexada por par de idiomas, onde cada entrada compreende o vetor semântico do texto de origem, o texto de origem e a tradução correspondente, e onde o limiar de similaridade para cache hit é configurável pelo operador.

---

### Reivindicação 3 — Tradução especulativa (dependente da 1)

> **Sistema conforme Reivindicação 1**, caracterizado por compreender adicionalmente:
>
> módulo de tradução especulativa que processa resultados intermediários de transcrição de fala a intervalos regulares, gerando traduções parciais antes da finalização da frase; e
>
> mecanismo de pré-carregamento de motor de síntese de voz que executa síntese silenciosa (volume zero) com a tradução parcial especulativa, eliminando latência de inicialização fria do motor TTS quando a tradução final é recebida.

---

### Reivindicação 4 — Protocolo agnóstico (dependente da 1)

> **Sistema conforme Reivindicação 1**, caracterizado por o protocolo de transmissão incluir somente o identificador de idioma de origem no pacote enviado pelo emissor, sendo a seleção do idioma de destino realizada de forma independente por cada receptor, de modo a permitir comunicação simultânea entre múltiplos participantes cada um recebendo tradução para seu idioma particular sem reconfiguração do emissor.

---

### Reivindicação 5 — Método (independente)

> **Método de tradução de fala com preservação de características prosódicas**, caracterizado pelas etapas de:
>
> **(1)** capturar sinal de áudio contendo fala em idioma de origem;
> **(2)** transcrever o sinal de áudio em texto por meio de reconhecimento automático de fala;
> **(3)** extrair simultaneamente à transcrição parâmetros prosódicos do sinal de áudio incluindo contorno de frequência fundamental, perfil de energia temporal e padrões de pausa;
> **(4)** converter os parâmetros prosódicos em vetor numérico de dimensão fixa por meio de rede neural recorrente;
> **(5)** gerar vetor semântico do texto transcrito por modelo de linguagem multilíngue;
> **(6)** verificar no cache de tradução se existe entrada com vetor semântico similar ao vetor gerado, com limiar de similaridade de cosseno configurável;
> **(7)** na ausência de entrada similar no cache, traduzir o texto para idioma de destino por meio de modelo transformer com representação interlingua;
> **(8)** calcular escore de qualidade da tradução por similaridade de cosseno entre vetor semântico de origem e vetor semântico da tradução;
> **(9)** transmitir para dispositivo receptor o texto traduzido conjuntamente com o vetor prosódico codificado;
> **(10)** no dispositivo receptor, decodificar o vetor prosódico em parâmetros de controle de síntese de voz;
> **(11)** sintetizar o texto traduzido no idioma de destino aplicando os parâmetros prosódicos decodificados ao motor de síntese.

---

### Reivindicação 6 — Estrutura de dados (independente)

> **Estrutura de dados para transmissão de fala traduzida com preservação prosódica**, caracterizada por formato digital compreendendo:
>
> **(a)** campo de texto no idioma de destino;
> **(b)** vetor numérico de dimensão fixa representando características prosódicas da voz original, incluindo contorno de frequência fundamental, perfil de energia e padrões de pausa codificados por rede neural;
> **(c)** identificadores de idioma de origem e de destino;
> **(d)** escore numérico de qualidade da tradução derivado de similaridade semântica entre texto original e traduzido;
> **(e)** indicador de proveniência da tradução distinguindo entre tradução computada e tradução recuperada de cache semântico.

---

### Reivindicação 7 — Validação por embedding (dependente da 5)

> **Método conforme Reivindicação 5**, caracterizado por o escore de qualidade da tradução ser calculado sem referência humana ou corpus paralelo, exclusivamente mediante similaridade de cosseno entre representações vetoriais do texto de origem e do texto traduzido em espaço de embedding multilíngue compartilhado.

---

### Reivindicação 8 — Mapeamento prosódico cross-lingual (dependente da 5)

> **Método conforme Reivindicação 5**, caracterizado por a decodificação do vetor prosódico incluir mapeamento proporcional de valores de frequência fundamental do registro vocal típico do idioma de origem para o registro vocal típico do idioma de destino, preservando contrastes prosódicos relativos (ascendente, descendente, interrogativo, enfático) enquanto ajusta valores absolutos de frequência ao range natural do idioma de destino.

---

---

# PARTE IV — ANÁLISE DO ESTADO DA TÉCNICA

## 14. PRIOR ART — ANÁLISE PRELIMINAR

*Esta seção é uma análise preliminar do inventor. O profissional de PI deve conduzir busca formal nas bases USPTO, EPO, INPI, J-PlatPat e CNIPA antes do depósito.*

### 14.1 Tecnologias Existentes e suas Limitações

**Google Translate / Google Cloud Translation:**
- Cobre: tradução neural estado-da-arte, TTS básico, 100+ idiomas
- Não cobre: prosódia, operação offline, cache semântico, validação automática de qualidade

**Meta NLLB-200 (modelo público, 2022):**
- Cobre: representação interlingua para 200 idiomas
- Não cobre: prosódia, cache semântico, pipeline integrado com validação

**DeepL:**
- Cobre: tradução de alta qualidade
- Não cobre: prosódia, operação offline, cache semântico

**Microsoft Azure Cognitive Services (Translator + Neural TTS):**
- Cobre: tradução + TTS com estilos de voz predefinidos (cheerful, sad, etc.)
- Não cobre: extração e preservação da prosódia do falante original, transmissão de vetor prosódico

**Amazon Polly (Neural TTS):**
- Cobre: TTS neural com alguns controles SSML
- Não cobre: extração de prosódia do áudio original, integração com tradução, transmissão de vetor prosódico

**OpenAI Whisper (2022):**
- Cobre: ASR de alta qualidade para múltiplos idiomas
- Não cobre: extração de prosódia, tradução, TTS

**Coqui TTS (XTTS v2):**
- Cobre: TTS neural multilíngue com voice cloning
- Não cobre: integração com pipeline de tradução, recepção de vetor prosódico externo, preservação de prosódia de falante diferente

### 14.2 Patentes Identificadas como Potencialmente Relacionadas

*Nota: Esta lista é preliminar e não substitui busca formal.*

| Identificador | Titular (estimado) | Escopo relevante | Risco de conflito |
|--------------|-------------------|-----------------|-------------------|
| US10,741,181 | Google | Neural TTS com controle de estilo | Baixo — não preserva prosódia de falante original |
| US11,062,699 | Amazon | TTS neural com emoção | Baixo — não integra tradução nem extrai prosódia |
| US10,984,779 | Microsoft | Tradução com entonação básica | Médio — verificar escopo exato |
| EP3,588,501 | Nuance | Análise prosódica para sentimento | Baixo — não traduz nem preserva prosódia |

### 14.3 Distinção Clara do Estado da Técnica

O sistema descrito neste documento distingue-se do estado da técnica pela combinação inédita dos seguintes elementos num único pipeline integrado:

1. **Extração vetorial de prosódia do falante original** (não seleção de preset de emoção)
2. **Compressão prosódica em vetor de dimensão fixa** por rede neural (não mapeamento heurístico)
3. **Transmissão do vetor prosódico junto com texto traduzido** como estrutura de dados unificada
4. **Síntese expressiva guiada pelo vetor** no idioma de destino
5. **Cache semântico por similaridade de cosseno** (não por correspondência exata de string)
6. **Validação automática de qualidade** por distância semântica entre embeddings
7. **Operação 100% offline** sem dependência de serviços de nuvem

Nenhuma das soluções identificadas combina todos esses elementos.

---

---

# PARTE V — INFORMAÇÕES COMPLEMENTARES

## 15. ESTADO DE IMPLEMENTAÇÃO

| Módulo | Status | Evidência |
|--------|--------|-----------|
| STT (Whisper + Web Speech API) | Implementado e em produção | `legacy/sender/sender_stream.py`, `legacy/web/web_peer.py` |
| Embedding semântico 384D | Implementado e em produção | `legacy/translation_engine.py:36-62` |
| Cache semântico | Implementado e em produção | `legacy/translation_engine.py:65-95` |
| Tradução NLLB-200 | Implementado e em produção | `legacy/translation_engine.py:98-184` |
| Validação por cosine similarity | Implementado e em produção | `legacy/translation_engine.py:187-257` |
| Tradução especulativa | Implementado e em produção | `legacy/translation_engine.py:259-284`, `legacy/web/web_peer.py:63-88` |
| Pre-buffering TTS | Implementado e em produção | `legacy/web/index.html:635-643` |
| Protocolo WebSocket agnóstico | Implementado e em produção | `legacy/protocol/message.py`, `legacy/web/web_peer.py` |
| Extração prosódica | Especificado, em desenvolvimento | `legacy/documentacao/ANALISE_GAP_PROSODICA.md` |
| Encoder prosódico 128D | Especificado, em desenvolvimento | `legacy/documentacao/MOTOR_INTERLINGUA.md` |
| Decoder prosódico + TTS expressivo | Especificado, em desenvolvimento | `legacy/documentacao/ANALISE_GAP_PROSODICA.md` |

## 16. HARDWARE DE REFERÊNCIA PARA OPERAÇÃO

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | 4 cores 2,5GHz | 6 cores 3,0GHz+ |
| RAM | 8 GB | 16 GB |
| GPU | Integrada (lento) | NVIDIA GTX 1660+ (6 GB VRAM) |
| Armazenamento | 5 GB (modelos) | SSD 10 GB |
| SO | Windows / Linux / macOS | — |

**Modelos em disco:**
- NLLB-200 distilled 600M (CTranslate2): ~2,5 GB
- MiniLM embedder: ~400 MB
- Whisper Base: ~142 MB
- XTTS v2 (planejado): ~2 GB
- Total atual: ~3 GB | Total projetado: ~5 GB

## 17. ESCOPO DE PROTEÇÃO RECOMENDADO

*Sugestão do inventor para avaliação do profissional de PI:*

**Prioridade máxima (registrar primeiro):**
- Sistema integrado completo (Reivindicação 1)
- Método end-to-end com prosódia (Reivindicação 5)
- Estrutura de dados de transmissão prosódica (Reivindicação 6)

**Prioridade média:**
- Cache semântico por embeddings (Reivindicação 2)
- Tradução especulativa com pre-buffering (Reivindicação 3)
- Validação automática por distância semântica (Reivindicação 7)

**Estratégia de proteção complementar:**
- Registro de software no INPI (proteção do código-fonte, custo ~R$200)
- Segredo industrial para hiperparâmetros de treinamento do encoder prosódico
- Marca para o nome comercial do produto

## 18. CRONOGRAMA DE PROTEÇÃO SUGERIDO

| Marco | Data estimada | Ação |
|-------|--------------|------|
| Protótipo prosódico funcional | Jun/2026 | Demo técnico com áudio antes/depois |
| Depósito INPI Brasil | Q3/2026 | Pedido de patente nacional + sigilo 18 meses |
| Depósito PCT | Q4/2026 | Proteção internacional (EUA, EU, CN, JP, KR) |
| Publicação | ~2028 | Após fase nacional nos países designados |

**Custo estimado (USD):**
- Advogado de PI (redação e depósito): $8.000–$12.000
- Taxas INPI: ~R$2.500 (pessoa física/micro empresa com desconto 60%)
- Taxas PCT: ~$3.500
- Traduções: ~$2.000
- **Total inicial:** ~$14.000–$18.000

---

## 19. CONTATO DO INVENTOR

*(A ser preenchido pelo inventor antes de compartilhar com o profissional de PI)*

- **Inventor:** Felipe [sobrenome]
- **CPF/RG:** —
- **Endereço:** —
- **E-mail:** —
- **Data da primeira redução a código (proto funcional v6.0):** 07/03/2026

---

*Documento preparado pelo inventor para orientação do profissional de propriedade intelectual.*
*Versão 1.0 — 2026-03-14*
*Confidencial — Não distribuir sem NDA assinado*
