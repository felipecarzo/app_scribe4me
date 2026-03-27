<p align="center">
  <img src="assets/banner.png?v=3" alt="Scribe4me" width="100%">
</p>

<p align="center">
  <strong>Speech-to-text local com IA</strong> — transcreve sua voz em texto usando Whisper, direto no seu computador.<br>
  Nenhum dado e enviado para a nuvem. 100% privado.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6" alt="Windows">
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

## Download

<p align="center">
  <a href="../../releases/latest">
    <img src="https://img.shields.io/badge/Baixar%20Scribe4me-v1.2.0-brightgreen?style=for-the-badge&logo=windows" alt="Download">
  </a>
</p>

Baixe o instalador na [pagina de Releases](../../releases/latest) e execute. A instalacao leva menos de 1 minuto.

> No primeiro uso, o modelo Whisper e baixado automaticamente (~39 MB a ~1.5 GB dependendo do modelo). Apos isso, tudo funciona offline.

---

## Funcionalidades

<table>
<tr>
<td width="50%">

**Transcricao**
- Whisper (OpenAI) roda 100% local via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Push-to-talk (Ctrl+Alt+H) — segura e fala
- Toggle (Ctrl+Alt+T) — aperta pra iniciar/parar
- Pontuacao automatica — virgulas, pontos e maiusculas
- Prompt personalizado — configure o estilo de transcricao

</td>
<td width="50%">

**Interface**
- Tray icon com estados visuais (verde/vermelho/amarelo/azul)
- Deteccao automatica de hardware (GPU/CPU)
- Troca de modelo pelo menu do tray
- Modo cursor (cola direto) ou clipboard
- Ajuda integrada com link para documentacao

</td>
</tr>
</table>

---

## Atalhos

| Atalho | Acao |
|--------|------|
| **Ctrl+Alt+H** | Push-to-talk (segura e fala) |
| **Ctrl+Alt+T** | Toggle gravacao (iniciar/parar) |
| **Ctrl+Q** | Sair do aplicativo |

---

## Modelos Whisper

O app detecta seu hardware e recomenda o melhor modelo. Troque pelo menu do tray (botao direito no icone).

| Modelo | Tamanho | VRAM minima | Qualidade |
|--------|---------|-------------|-----------|
| tiny | ~39 MB | - | Basica |
| base | ~74 MB | - | Razoavel |
| small | ~244 MB | 2 GB | Boa |
| medium | ~769 MB | 4 GB | Muito boa |
| large | ~1.5 GB | 6 GB | Excelente |

---

## Requisitos

- **Windows 10/11** (64-bit)
- **Microfone**
- **GPU NVIDIA com CUDA** (opcional — funciona em CPU, mais lento)

---

## Rodar pelo codigo fonte

```bash
git clone https://github.com/felipecarzo/app_scribe4me.git
cd app_scribe4me

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python run_scribe4me.py
```

> Para CUDA, instale o [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) separadamente.

---

## Build

```bash
pip install pyinstaller
pyinstaller scribe4me.spec --distpath dist --workpath build_scribe4me
```

Para gerar o instalador, instale o [Inno Setup 6](https://jrsoftware.org/isdl.php) e compile `scribe4me_installer.iss`.

---

## Testes

```bash
pytest tests/ -v
```

---

## Estrutura

```
src/
  main.py            — orquestrador principal
  config.py          — configuracoes e persistencia
  recorder.py        — captura de audio do microfone
  transcriber.py     — interface com faster-whisper
  clipboard.py       — envio do texto (cursor ou clipboard)
  hardware.py        — deteccao de GPU/RAM
  tray.py            — icone na bandeja do sistema
  postprocess.py     — pos-processamento de pontuacao
  prompt_editor.py   — editor de prompt personalizado

tests/               — testes unitarios e de integracao
scripts/             — utilitarios (geracao de icone)
assets/              — icone, banner e EULA
```

---

## Tecnologias

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper otimizado com CTranslate2
- [pynput](https://github.com/moses-palmer/pynput) — captura global de teclado
- [pystray](https://github.com/moses-palmer/pystray) — icone na bandeja do sistema
- [sounddevice](https://python-sounddevice.readthedocs.io/) — captura de audio

---

## Privacidade

O Scribe4me processa audio **localmente** no seu computador. Nenhum audio ou texto e enviado para servidores externos. O unico acesso a internet acontece no primeiro uso, para baixar o modelo Whisper.

---

## Licenca

[MIT](LICENSE)
