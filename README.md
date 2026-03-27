# Scribe4me

Speech-to-text local usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2). Roda 100% offline, com CUDA ou CPU.

## Features

- **Transcricao precisa** — Whisper large-v3 com pontuacao automatica real
- **Push-to-talk** (Ctrl+Alt+H) e **toggle** (Ctrl+Alt+T)
- **Saida flexivel** — cola direto no cursor ativo ou copia pro clipboard
- **Profiles customizaveis** — crie prompts especializados (.txt) para melhorar reconhecimento por dominio
- **Voice Coding** — comandos de voz para programar (tab, enter, def, print, if, etc.)
- **GUI opcional** — janela com log real-time, controles e dark theme
- **System tray** — icone de microfone com estados visuais (gravando, transcrevendo, pronto)
- **Selecao de modelo** — de tiny (rapido) a large-v3 (preciso), direto pelo tray menu

## Requisitos

- Python 3.12+
- Windows 10/11
- GPU NVIDIA com CUDA (opcional — funciona com CPU, mais lento)

## Instalacao

```bash
git clone https://github.com/felipecarzo/app_scribe4me.git
cd app_scribe4me
pip install -r requirements.txt
```

## Uso

```bash
python run_scribe4me.py
```

Ou com opcoes:

```bash
python run_scribe4me.py --clipboard     # saida via clipboard (padrao: cursor)
python run_scribe4me.py --model medium  # modelo especifico
python run_scribe4me.py --no-gui        # sem janela GUI
```

## Hotkeys

| Hotkey | Acao |
|---|---|
| Ctrl+Alt+H | Push-to-talk (segura e fala) |
| Ctrl+Alt+T | Toggle gravacao (aperta pra iniciar/parar) |
| Ctrl+Q | Sair |

## Profiles

Profiles sao arquivos `.txt` em `%LOCALAPPDATA%/Scribe4me/profiles/`. Cada profile define um `initial_prompt` que melhora o reconhecimento de vocabulario especifico.

**Formato:**
```
Nome do Profile
Texto do prompt aqui. Inclua palavras e frases do seu dominio
para que o Whisper reconheca melhor termos tecnicos, nomes, etc.
```

Para ativar voice coding, adicione `@code_mode` na segunda linha:
```
Code Mode
@code_mode
Fiz o deploy no staging e rodei o pipeline de CI/CD...
```

3 profiles vem incluidos: **Geral**, **Tech-Dev** e **Code Mode**.

## Voice Coding

Com um profile `@code_mode` ativo, comandos falados viram acoes:

| Comando | Acao |
|---|---|
| "tab" / "tabulacao" | Tab |
| "enter" / "nova linha" | Enter |
| "abre parenteses" | ( |
| "fecha chaves" | } |
| "def funcao X" | def X(): |
| "print de X" | print(X) |
| "comentario X" | # X |
| "desfazer" / "undo" | Ctrl+Z |
| "salvar" | Ctrl+S |

E muitos outros. Veja `src/voice_commands.py` para a lista completa.

## Estrutura

```
src/
  main.py              — orquestrador principal
  recorder.py          — captura de audio do microfone
  transcriber.py       — interface com faster-whisper
  clipboard.py         — envio de texto para cursor/clipboard
  postprocess.py       — pos-processamento de pontuacao
  voice_commands.py    — engine de comandos de voz
  profiles.py          — sistema de profiles customizaveis
  gui.py               — janela GUI (tkinter, opcional)
  tray.py              — system tray icon
  config.py            — configuracoes
  hardware.py          — deteccao de GPU e recomendacao de modelo
```

## Build (PyInstaller)

```bash
python -m PyInstaller scribe4me.spec --noconfirm --distpath dist_scribe4me
```

## Licenca

MIT
