# Scribe4me — Visao Geral do Projeto

> Documento de referencia para divulgacao, LinkedIn, apresentacoes e contexto geral do projeto.

---

## O que e o Scribe4me?

Scribe4me e um aplicativo **gratuito e open source** de speech-to-text que roda **100% local** no seu computador. Ele usa o modelo Whisper (OpenAI) para transcrever voz em texto com alta precisao, direto onde voce esta digitando — sem enviar nenhum dado para a nuvem.

A motivacao nasceu da frustracao com o ditado nativo do Windows (Win+H): impreciso, dependente de internet, sem pontuacao real, e travando no meio de frases. O Scribe4me resolve todos esses problemas.

---

## Como funciona

1. Voce pressiona **Ctrl+Alt+H** (segura e fala)
2. Solta a tecla quando terminar
3. O texto transcrito aparece onde seu cursor estiver

Simples assim. Sem login, sem conta, sem internet, sem assinatura.

O app fica na bandeja do sistema (tray icon) com feedback visual por cores:
- **Verde** = pronto para gravar
- **Vermelho** = gravando
- **Vermelho piscando** = transcrevendo
- **Azul** = texto pronto
- **Amarelo piscando** = carregando modelo

---

## Stack tecnica

| Camada | Tecnologia | Por que |
|--------|-----------|---------|
| **Transcricao** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) | 3-4x mais rapido que Whisper original, 40% menos VRAM, mesma qualidade |
| **Linguagem** | Python 3.12 | Ecossistema ML maduro, integracao nativa com Whisper |
| **Aceleracao GPU** | CUDA (NVIDIA) | Transcricao em tempo real com GPU; fallback automatico pra CPU |
| **Captura de audio** | [sounddevice](https://python-sounddevice.readthedocs.io/) | Gravacao do microfone em tempo real, cross-platform |
| **Hotkeys globais** | [pynput](https://github.com/moses-palmer/pynput) | Captura de teclado em background sem conflito com outros apps |
| **Tray icon** | [pystray](https://github.com/moses-palmer/pystray) | Icone na bandeja do sistema com menu de contexto |
| **Build** | PyInstaller + Inno Setup | Executavel standalone (.exe) + instalador profissional para Windows |

### Dependencias (requirements.txt)

```
faster-whisper>=1.0.0
sounddevice>=0.5.1
numpy>=1.26.0
pyperclip>=1.9.0
pynput>=1.7.7
pystray>=0.19.5
Pillow>=10.0.0
```

Nenhuma dependencia de PyTorch. O faster-whisper usa CTranslate2 internamente, que e um runtime de inferencia otimizado em C++ — isso reduz o tamanho do instalador de **1.8 GB** (com PyTorch) para **~64 MB**.

---

## Processo de criacao e evolucao

### Fase 0 — Conceito e setup

O projeto comecou como uma substituicao direta do Win+H do Windows. A ideia era simples: um botao no teclado que grava, transcreve com Whisper e cola o texto onde voce esta digitando.

Estrutura criada do zero: `src/` com modulos separados para gravacao, transcricao, saida de texto, configuracao e orquestracao.

### Fase 1 — MVP funcional (Sprints 0-2)

| Sprint | O que foi feito |
|--------|----------------|
| **Sprint 0** | Estrutura de pastas, ambiente Python, configuracoes (modelo, idioma, hotkeys) |
| **Sprint 1** | Core completo: `recorder.py` (captura audio), `transcriber.py` (Whisper), `clipboard.py` (saida de texto), `main.py` (orquestrador) |
| **Sprint 2** | Hotkeys globais (push-to-talk e toggle), seletor de modo (cursor vs clipboard), testes end-to-end |

Ao final da Fase 1, o app ja funcionava: Ctrl+Alt+H -> grava -> transcreve -> texto aparece.

### Fase 2 — Polimento (Sprint 3)

| Task | O que foi feito |
|------|----------------|
| **Otimizacao de latencia** | Warm-up do modelo no startup (primeira transcricao sem delay), CUDA tuning, beam_size=1 para velocidade |
| **Tray icon** | Icone na bandeja com 5 estados visuais (cores + piscar), menu de contexto com troca de modelo, notificacoes nativas do Windows |
| **Pos-processamento** | Capitalizacao automatica, correcao de espacos antes de pontuacao, remocao de pontuacao duplicada |

### Fase 3 — Migracao e otimizacao

A maior decisao tecnica do projeto: migrar de **openai-whisper** (PyTorch) para **faster-whisper** (CTranslate2).

Resultados:
- **Velocidade**: 3-4x mais rapido na transcricao
- **VRAM**: 40% menos consumo de memoria de GPU
- **Instalador**: de 1.8 GB para 64 MB (sem PyTorch)
- **Qualidade**: identica (mesmo modelo Whisper, formato diferente)

Tambem implementamos deteccao automatica de hardware: o app detecta se a maquina tem GPU NVIDIA com CUDA disponivel. Se tiver, usa GPU com float16. Se nao, faz fallback automatico pra CPU com int8 — sem nenhuma configuracao manual.

### Tentativas que nao deram certo (e o que aprendemos)

- **Transcricao em chunks durante a gravacao**: Tentamos processar audio em pedacos de 3s enquanto o usuario fala, pra ter texto em tempo real. Na pratica, causou contencao de GPU (o modelo nao consegue transcrever e receber audio ao mesmo tempo de forma eficiente) e o app ficou mais lento. Revertido.

- **Texto aparecendo em tempo real no cursor**: Tentamos digitar texto parcial onde o cursor esta e apagar/reescrever conforme novos chunks chegam. Corrompeu a digitacao do usuario. Revertido.

A licao: simplicidade vence. Gravar tudo, transcrever uma vez, colar. Rapido e confiavel.

---

## Modelos Whisper disponiveis

O app detecta o hardware e recomenda o melhor modelo automaticamente. O usuario pode trocar pelo menu do tray (clique direito no icone).

| Modelo | Tamanho | VRAM minima | Qualidade | Caso de uso |
|--------|---------|-------------|-----------|-------------|
| **tiny** | ~39 MB | — | Basica | Maquinas sem GPU, testes rapidos |
| **base** | ~74 MB | — | Razoavel | CPU com pouca RAM |
| **small** | ~244 MB | 2 GB | Boa | GPU entry-level (GTX 1650, etc.) |
| **medium** | ~769 MB | 4 GB | Muito boa | GPU mid-range (RTX 3060, etc.) |
| **large** | ~1.5 GB | 6 GB | Excelente | GPU potente (RTX 3070+, RTX 4060+) |

O modelo e baixado automaticamente no primeiro uso (unico momento em que o app acessa a internet).

---

## Como e gratuito? Como funciona sem internet?

O Scribe4me e **100% gratuito** e **open source** (licenca MIT). Nao tem versao paga, nao tem plano premium, nao tem coleta de dados.

**Como isso e possivel:**

O Whisper e um modelo de IA criado pela OpenAI e liberado como open source. O faster-whisper e uma reimplementacao otimizada por terceiros, tambem open source. Todo o processamento acontece **localmente na sua maquina** — o audio nunca sai do seu computador.

O unico acesso a internet e no primeiro uso, para baixar o modelo (~39 MB a ~1.5 GB dependendo da escolha). Depois disso, o app funciona 100% offline.

**Privacidade total**: nenhum audio, nenhum texto, nenhuma metrica e enviada para nenhum servidor.

---

## Funcionalidades atuais (v1.1.0)

- Transcricao local com Whisper via faster-whisper (CTranslate2)
- Push-to-talk (Ctrl+Alt+H) — segura e fala, solta e aparece
- Toggle (Ctrl+Alt+T) — aperta pra iniciar, aperta de novo pra parar
- Modo cursor (cola direto onde voce digita) ou modo clipboard
- Tray icon com 5 estados visuais + notificacoes nativas
- Deteccao automatica de hardware (GPU/CPU)
- Fallback automatico CUDA -> CPU
- Troca de modelo pelo menu (tiny a large)
- Pontuacao automatica (virgulas, pontos, maiusculas)
- Instancia unica (nao abre duas vezes)
- Roda silenciosamente na bandeja — sem terminal, sem janela
- Instalador profissional para Windows (Inno Setup)

---

## Proximas implementacoes planejadas

### Curto prazo
- **Multi-idioma**: suporte a ingles, espanhol e outros idiomas alem de portugues
- **Historico de transcricoes**: log acessivel pelo menu do tray com as ultimas transcricoes
- **Comandos por voz**: acoes como "apagar ultima frase", "nova linha", "copiar tudo"

### Medio prazo
- **Suporte Linux**: o core do app (faster-whisper, sounddevice, pynput) ja e cross-platform. As adaptacoes necessarias sao:
  - Substituir `pystray` por solucao compativel com Wayland/X11
  - Adaptar deteccao de hardware (nvidia-smi funciona igual)
  - Adaptar o envio de texto para cursor (xdotool ou wtype no Wayland)
  - Remover dependencias Windows-only (ctypes.windll, win32)
  - Build com AppImage ou Flatpak ao inves de PyInstaller + Inno Setup

### Longo prazo
- **Versao mobile (Android/iOS)**: a arquitetura do Whisper permite rodar em dispositivos moveis via [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (implementacao em C/C++ otimizada para ARM). Desafios:
  - Modelos menores (tiny/base) para caber na RAM do celular
  - Otimizacao para processadores ARM (Qualcomm, Apple Silicon)
  - Interface nativa (Kotlin/Swift) ou cross-platform (Flutter/React Native)
  - Integracao com teclado do sistema (como um teclado alternativo)
  - Possivel uso de Core ML (iOS) ou NNAPI (Android) para aceleracao

---

## Numeros do projeto

| Metrica | Valor |
|---------|-------|
| Tamanho do instalador | ~64 MB |
| Tempo de startup (com GPU) | ~3-5 segundos |
| Latencia de transcricao (30s de audio, GPU, large) | ~2-4 segundos |
| Latencia de transcricao (30s de audio, CPU, small) | ~8-15 segundos |
| Modelos disponiveis | 5 (tiny, base, small, medium, large) |
| Idioma principal | Portugues (pt-BR) |
| Licenca | MIT (uso livre, inclusive comercial) |
| Preco | Gratuito, para sempre |

---

## Estrutura do codigo

```
src/
  main.py          — orquestrador (hotkey -> grava -> transcreve -> cola)
  config.py        — configuracoes (modelo, idioma, hotkeys, modos)
  recorder.py      — captura de audio do microfone (sounddevice)
  transcriber.py   — interface com faster-whisper (load, warm-up, transcribe)
  clipboard.py     — envio do texto (simula digitacao ou copia pro clipboard)
  hardware.py      — deteccao de GPU/VRAM/RAM e recomendacao de modelo
  tray.py          — icone na bandeja com estados visuais e menu
  postprocess.py   — pos-processamento de pontuacao e capitalizacao

tests/             — testes unitarios e de integracao
scripts/           — utilitarios (geracao de icone)
assets/            — icone, banner e EULA
```

---

## Links

- **GitHub**: [github.com/felipecarzo/app_scribe4me](https://github.com/felipecarzo/app_scribe4me)
- **Download**: [Releases](https://github.com/felipecarzo/app_scribe4me/releases)
- **Licenca**: [MIT](https://github.com/felipecarzo/app_scribe4me/blob/main/LICENSE)

---

*Documento gerado em marco de 2026. Scribe4me v1.1.0.*
