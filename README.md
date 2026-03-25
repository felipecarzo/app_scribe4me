<p align="center">
  <img src="assets/banner.png?v=2" alt="Scribe4me" width="100%">
</p>

<p align="center">
  <strong>Speech-to-text local com IA</strong> — transcreve sua voz em texto usando Whisper, direto no seu computador.<br>
  Nenhum dado e enviado para a nuvem.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Windows">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
  <img src="https://img.shields.io/github/v/release/felipecarzo/app_scribe4me?label=download&color=brightgreen" alt="Release">
</p>

---

## Como funciona

1. Pressione **Ctrl+Alt+H** (segure e fale)
2. Solte a tecla quando terminar
3. O texto aparece onde seu cursor estiver

Simples assim. Sem login, sem internet, sem assinatura.

---

## Funcionalidades

- **Transcricao local** — Whisper (OpenAI) roda 100% no seu computador via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **Push-to-talk** (Ctrl+Alt+H) — segura e fala, solta e o texto aparece
- **Toggle** (Ctrl+Alt+T) — aperta pra iniciar, aperta de novo pra parar
- **Tray icon** com estados visuais (verde = pronto, vermelho = gravando, azul = texto pronto)
- **Deteccao automatica de hardware** — escolhe o melhor modelo Whisper para sua GPU/CPU
- **Troca de modelo** pelo menu do tray — tiny, base, small, medium, large
- **Modo cursor** — cola o texto direto onde voce esta digitando
- **Modo clipboard** — copia para a area de transferencia
- **Pontuacao automatica** — o texto sai com virgulas, pontos e maiusculas
- **Instancia unica** — nao abre duas vezes por acidente
- **Sem terminal** — roda silenciosamente na bandeja do sistema

---

## Requisitos

- **Windows 10/11** (64-bit)
- **Python 3.12+**
- **Microfone**
- **GPU NVIDIA com CUDA** (opcional — funciona em CPU tambem, mais lento)

---

## Instalacao

### Via instalador (recomendado)

Baixe o instalador na [pagina de Releases](../../releases) e execute.

### Via codigo fonte

```bash
# Clone o repositorio
git clone https://github.com/felipecarzo/app_scribe4me.git
cd app_scribe4me

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instale as dependencias
pip install -r requirements.txt

# Execute
python run_scribe4me.py
```

> **Nota sobre GPU:** Para usar CUDA, instale o [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) separadamente. Sem ele, o app funciona normalmente em CPU.

---

## Atalhos

| Atalho | Acao |
|--------|------|
| **Ctrl+Alt+H** | Push-to-talk (segura e fala) |
| **Ctrl+Alt+T** | Toggle gravacao (aperta pra iniciar/parar) |
| **Ctrl+Q** | Sair do aplicativo |

---

## Modelos Whisper

O app detecta seu hardware e recomenda o melhor modelo automaticamente. Voce pode trocar pelo menu do tray (botao direito no icone).

| Modelo | Tamanho | VRAM minima | Qualidade |
|--------|---------|-------------|-----------|
| tiny | ~39 MB | - | Basica |
| base | ~74 MB | - | Razoavel |
| small | ~244 MB | 2 GB | Boa |
| medium | ~769 MB | 4 GB | Muito boa |
| large | ~1.5 GB | 6 GB | Excelente |

O modelo e baixado automaticamente no primeiro uso.

---

## Estrutura do projeto

```
src/
  main.py          — orquestrador principal
  config.py        — configuracoes
  recorder.py      — captura de audio do microfone
  transcriber.py   — interface com faster-whisper
  clipboard.py     — envio do texto (cursor ou clipboard)
  hardware.py      — deteccao de GPU/RAM
  tray.py          — icone na bandeja do sistema
  postprocess.py   — pos-processamento de pontuacao

tests/             — testes unitarios e de integracao
scripts/           — utilitarios (geracao de icone)
assets/            — icone e EULA
```

---

## Build (gerar executavel)

```bash
# Instale o PyInstaller
pip install pyinstaller

# Gere o executavel
pyinstaller scribe4me.spec --distpath dist --workpath build_scribe4me
```

Para gerar o instalador Windows, instale o [Inno Setup](https://jrsoftware.org/isdl.php) e compile `scribe4me_installer.iss`.

---

## Testes

```bash
pytest tests/ -v
```

---

## Tecnologias

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper otimizado com CTranslate2 (3-4x mais rapido)
- [pynput](https://github.com/moses-palmer/pynput) — captura global de teclado
- [pystray](https://github.com/moses-palmer/pystray) — icone na bandeja do sistema
- [sounddevice](https://python-sounddevice.readthedocs.io/) — captura de audio

---

## Privacidade

O Scribe4me processa audio **localmente** no seu computador. Nenhum audio ou texto e enviado para servidores externos. O unico acesso a internet acontece no primeiro uso, para baixar o modelo Whisper (~39 MB a ~1.5 GB dependendo do modelo escolhido).

---

## Licenca

[MIT](LICENSE)
