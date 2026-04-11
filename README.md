<p align="center">
  <img src="assets/banner.png?v=3" alt="Scribe4me" width="100%">
</p>

<p align="center">
  <strong>Speech-to-text local com IA</strong> — transcreve sua voz em texto usando Whisper, direto no seu computador.<br>
  Nenhum dado e enviado para a nuvem. 100% privado.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20macOS-0078D6" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.12-3776AB" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
  <a href="../../releases/latest"><img src="https://img.shields.io/github/v/release/felipecarzo/app_scribe4me?label=download&color=brightgreen" alt="Download"></a>
</p>

---

## Como funciona

1. Pressione **Ctrl+Alt+H** (segure e fale)
2. Solte a tecla quando terminar
3. O texto aparece onde seu cursor estiver

Simples assim. Sem login, sem internet, sem assinatura.

---

## Instalacao

### Windows

<p align="center">
  <a href="../../releases/latest">
    <img src="https://img.shields.io/badge/Baixar%20Scribe4me-Windows-brightgreen?style=for-the-badge&logo=windows" alt="Download Windows">
  </a>
</p>

Baixe o instalador `.exe` na [pagina de Releases](../../releases/latest) e execute. A instalacao leva menos de 1 minuto.

### macOS

<p align="center">
  <a href="../../releases/latest">
    <img src="https://img.shields.io/badge/Baixar%20Scribe4me-macOS-lightgrey?style=for-the-badge&logo=apple" alt="Download macOS">
  </a>
</p>

Baixe o arquivo `.dmg` na [pagina de Releases](../../releases/latest), abra e arraste o `Scribe4me.app` para a pasta Aplicativos.

> **Primeira execucao:** o macOS pode exibir um aviso de seguranca. Va em `Preferencias do Sistema > Privacidade e Seguranca` e clique em "Abrir mesmo assim". Alem disso, conceda permissao de microfone quando solicitado.

### Linux

Abra o terminal e rode:

```bash
curl -fsSL https://raw.githubusercontent.com/felipecarzo/app_scribe4me/main/scripts/install_linux.sh | bash
```

O script baixa o AppImage, instala em `~/.local/bin/` e cria um atalho no menu de aplicativos.

**Dependencias (Debian/Ubuntu):**

```bash
sudo apt install xclip libportaudio2 libappindicator3-1
```

**Desinstalar:**

```bash
rm ~/.local/bin/Scribe4me ~/.local/share/applications/Scribe4me.desktop
```

> No primeiro uso, o modelo Whisper e baixado automaticamente (~39 MB a ~1.5 GB dependendo do modelo). Apos isso, tudo funciona offline.

---

## Funcionalidades

<table>
<tr>
<td width="50%">

**Transcricao**
- Whisper local 100% offline via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **API opcional**: OpenAI, Groq, Gemini, Deepgram — mais rapido, sem GPU
- **Realtime (Deepgram)**: texto aparece enquanto voce fala
- Push-to-talk — segura e fala
- Toggle — aperta pra iniciar/parar
- Cancelar gravacao — aborta sem processar
- Pontuacao automatica — virgulas, pontos e maiusculas
- Prompt personalizado — configure o estilo de transcricao

</td>
<td width="50%">

**Interface**
- Tray icon com estados visuais (verde/vermelho/amarelo/azul)
- **Janela de configuracoes unificada** — modelo, atalhos, prompt e API em um so lugar
- Deteccao automatica de hardware (GPU/CPU)
- Modo cursor (cola direto) ou clipboard — alternavel nas configuracoes
- **Atalhos personalizaveis** — reconfigure qualquer tecla pela janela de configuracoes
- Logs diarios permanentes — recupere textos de qualquer dia
- Ajuda integrada com link para documentacao

</td>
</tr>
</table>

---

## Atalhos

Todos os atalhos podem ser personalizados em **Configuracoes** (botao direito no tray > Configuracoes... > aba Atalhos).

| Atalho padrao | Acao |
|---------------|------|
| **Ctrl+Alt+H** | Push-to-talk (segura e fala) |
| **Ctrl+Alt+T** | Toggle gravacao (iniciar/parar) |
| **Ctrl+Alt+C** | Cancelar gravacao |
| **Ctrl+Q** | Sair do aplicativo |

---

## Configuracoes

Clique com o botao direito no **icone do tray** e selecione **Configuracoes...**

A janela e dividida em quatro abas:

| Aba | O que configura |
|-----|-----------------|
| **Geral** | Modelo Whisper e modo de saida (cursor / clipboard) |
| **Atalhos** | Recaptura qualquer atalho — basta clicar e pressionar a combinacao |
| **Prompt** | Texto de instrucao personalizado para o Whisper |
| **API** | Backend de transcricao, API keys e modo realtime (Deepgram) |

---

## Transcricao via API (opcional)

Por padrao o Scribe4me transcreve 100% offline. Se quiser mais velocidade — ou usar sem GPU — pode configurar um backend de API.

### Backends disponíveis

| Backend | Modelo | Gratuito | Realtime | Qualidade PT-BR |
|---------|--------|----------|----------|-----------------|
| **Groq** | whisper-large-v3 | 7.200s/dia | Nao | Excelente |
| **OpenAI** | whisper-1 | $0.006/min | Nao | Excelente |
| **Gemini** | gemini-1.5-flash | Free tier | Nao | Muito boa |
| **Deepgram** | nova-2 | 200h/mes | **Sim** | Muito boa |

### Como configurar

1. Clique com o botao direito no **icone do tray**
2. Clique em **Configuracoes...**
3. Va para a aba **API**
4. Selecione o backend no dropdown
5. Cole a API key no campo correspondente
6. Clique em **Salvar**

O app troca imediatamente para o novo backend — sem reiniciar.

> **Fallback automatico:** se a API retornar erro, o Scribe4me usa o Whisper local automaticamente.

### Onde obter as API keys

| Provider | Link | Observacao |
|----------|------|------------|
| Groq | [console.groq.com](https://console.groq.com) | Crie conta e va em API Keys |
| OpenAI | [platform.openai.com](https://platform.openai.com) | Requer cartao de credito |
| Gemini | [aistudio.google.com](https://aistudio.google.com) | Conta Google, sem cartao |
| Deepgram | [console.deepgram.com](https://console.deepgram.com) | Crie conta e va em API Keys |

### Transcricao em tempo real (Deepgram)

Com o backend **Deepgram** configurado, voce pode ativar o modo **realtime**:

1. Va em **Configuracoes... > aba API**
2. Selecione **Deepgram**
3. Marque **"Ativar transcricao em tempo real"**
4. Salve

No modo realtime, ao pressionar o atalho de gravacao, um overlay aparece na parte inferior da tela exibindo o texto parcial enquanto voce fala. Ao soltar a tecla (ou parar o toggle), o texto final e enviado ao cursor ou clipboard normalmente.

> O modo realtime requer conexao com a internet e consome a cota do Deepgram (200h/mes no free tier).

---

## Modelos Whisper

O app detecta seu hardware e recomenda o melhor modelo. Troque em **Configuracoes... > aba Geral**.

| Modelo | Tamanho | VRAM minima | Qualidade |
|--------|---------|-------------|-----------|
| tiny | ~39 MB | - | Basica |
| base | ~74 MB | - | Razoavel |
| small | ~244 MB | 2 GB | Boa |
| medium | ~769 MB | 4 GB | Muito boa |
| large | ~1.5 GB | 6 GB | Excelente |

---

## Requisitos

**Windows:**
- Windows 10/11 (64-bit)
- Microfone
- GPU NVIDIA com CUDA (opcional — funciona em CPU, mais lento)

**macOS:**
- macOS 12 Monterey ou superior (Apple Silicon e Intel)
- Microfone
- Permissao de acessibilidade (para hotkeys globais) e microfone

**Linux:**
- Distribuicao com X11 ou XWayland (Ubuntu, Fedora, Mint, etc.)
- Microfone
- `xclip`, `libportaudio2`, `libappindicator3-1`
- GPU NVIDIA com CUDA (opcional — funciona em CPU, mais lento)

> **Nota Linux:** Hotkeys globais requerem X11 ou XWayland. Wayland puro sem XWayland nao e suportado no momento.

---

## Rodar pelo codigo fonte

**Windows:**

```bash
git clone https://github.com/felipecarzo/app_scribe4me.git
cd app_scribe4me

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python run_scribe4me.py
```

**macOS / Linux:**

```bash
git clone https://github.com/felipecarzo/app_scribe4me.git
cd app_scribe4me

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python run_scribe4me.py
```

> Para CUDA, instale o [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) separadamente.

---

## Build

**Windows (instalador .exe):**

```bash
pip install pyinstaller
pyinstaller scribe4me.spec --noconfirm
```

Para gerar o instalador, instale o [Inno Setup 6](https://jrsoftware.org/isdl.php) e compile `scribe4me_installer.iss`.

**macOS (.app + .dmg):**

O build macOS roda automaticamente via GitHub Actions ao criar uma tag `v*`. Para buildar manualmente em um Mac:

```bash
pip install pyinstaller
pyinstaller scribe4me_macos.spec --noconfirm
hdiutil create -volname "Scribe4me" -srcfolder dist/Scribe4me.app -ov -format UDZO Scribe4me_macOS.dmg
```

**Linux (AppImage):**

```bash
pip install pyinstaller
chmod +x scripts/build_appimage.sh
./scripts/build_appimage.sh
```

Requer [appimagetool](https://github.com/AppImage/appimagetool/releases) no PATH.

---

## Testes

```bash
pytest tests/ -v
```

---

## Estrutura

```
src/
  main.py               — orquestrador principal
  config.py             — configuracoes e persistencia
  recorder.py           — captura de audio do microfone
  transcriber.py        — interface com faster-whisper (local)
  transcriber_api.py    — backends de API (OpenAI/Groq/Gemini/Deepgram)
  realtime_manager.py   — streaming WebSocket Deepgram (realtime)
  realtime_overlay.py   — overlay flutuante de texto parcial
  settings_window.py    — janela de configuracoes unificada (tkinter)
  clipboard.py          — envio do texto (cursor ou clipboard)
  hardware.py           — deteccao de GPU/RAM
  tray.py               — icone na bandeja do sistema
  postprocess.py        — pos-processamento de pontuacao
  platform/             — abstracao de plataforma (Windows / Linux / macOS)

tests/               — testes unitarios e de integracao
scripts/             — build AppImage + instalador Linux
assets/              — icone, banner e EULA
```

---

## Tecnologias

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper otimizado com CTranslate2
- [pynput](https://github.com/moses-palmer/pynput) — captura global de teclado
- [pystray](https://github.com/moses-palmer/pystray) — icone na bandeja do sistema
- [sounddevice](https://python-sounddevice.readthedocs.io/) — captura de audio
- [httpx](https://www.python-httpx.org/) — cliente HTTP para APIs de transcricao
- [websocket-client](https://github.com/websocket-client/websocket-client) — WebSocket para Deepgram realtime
- [soundfile](https://python-soundfile.readthedocs.io/) — conversao audio numpy → WAV

---

## Privacidade

Por padrao, o Scribe4me processa audio **localmente** no seu computador. Nenhum audio ou texto e enviado para servidores externos.

Se voce configurar um backend de API (OpenAI, Groq, Gemini ou Deepgram), os chunks de audio serao enviados para os servidores do provider escolhido. O uso de API e **opcional** e desativado por padrao.

---

## Licenca

[MIT](LICENSE)
