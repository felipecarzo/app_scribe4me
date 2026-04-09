# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-04-09
- **Branch:** main (commit unico — repo recriado limpo)
- **Ultimo commit:** 436980f — Scribe4me v1.5.0 — speech-to-text local com Whisper + API backends
- **Release:** v1.5.0 publicada no GitHub

## Estado do projeto

Scribe4me v1.5.0 — app desktop Windows/Linux de speech-to-text local com Whisper.
Feature de API transcription completa: OpenAI, Groq, Gemini, Deepgram (batch + realtime).
Repo GitHub recriado do zero sem rastros de co-authorship externo.
Historico squashado em 1 commit limpo.

## Task em andamento

Nenhuma de codigo — pendencia manual: buildar AppImage no Linux.

## Pendencias de commit

Nenhuma — working tree limpa.

## Proximo passo exato

1. **Buildar AppImage no Linux** — clonar repo numa maquina Linux, `pip install -r requirements.txt pyinstaller`, rodar `./scripts/build_appimage.sh`, testar o .AppImage
2. **Publicar AppImage no GitHub** — adicionar o .AppImage na release v1.5.0 (ou criar v1.5.1)
3. **Testar instalador Linux** — rodar `curl -fsSL .../install_linux.sh | bash` numa maquina limpa

## Arquivos a ler

- `src/transcriber_api.py` — backends OpenAI/Groq/Gemini/Deepgram batch
- `src/realtime_manager.py` — WebSocket Deepgram com callbacks on_partial/on_final/on_fragment
- `src/realtime_overlay.py` — overlay flutuante de texto parcial
- `src/api_settings_editor.py` — UI de configuracao de API keys
- `src/main.py` — roteador local/batch/realtime + injecao fragmento a fragmento no cursor

## Contexto importante

- Repo GitHub recriado: github.com/felipecarzo/app_scribe4me (historico limpo, 1 commit)
- Branch local `feat/api-transcription` existe localmente — pode ser deletada (ja mergeada e squashada)
- Backups dos instaladores antigos em `_releases_backup/` (gitignored) — podem ser deletados
- Suporte Linux usa X11/XWayland — Wayland puro nao suportado (pynput)
- NAO sugerir modelos menores ou streaming para STT — Felipe ja testou, qualidade cai demais em PT-BR
- Modo realtime cursor: cada frase confirmada pelo Deepgram e injetada via Ctrl+V imediatamente (on_fragment)
- Modelo local nao carrega no startup quando backend API esta configurado

## Novas dependencias (v1.5.0)

```
httpx>=0.27.0
websocket-client>=1.8.0
soundfile>=0.12.1
```
