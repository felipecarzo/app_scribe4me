# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-04-06
- **Branch:** main
- **Ultimo commit:** 0bf7700 — feat: suporte Linux — abstracao de plataforma, AppImage e instalador
- **Release:** v1.3.0 publicada no GitHub (v1.4.0 pendente — falta AppImage)

## Estado do projeto

Scribe4me v1.4.0 (pre-release) — app desktop Windows/Linux de speech-to-text local com Whisper.
Codigo cross-platform pronto. Falta buildar o AppImage no Linux e publicar release v1.4.0.

## Task em andamento

Nenhuma de codigo — pendencia manual: buildar AppImage no Linux.

## Pendencias de commit

Nenhuma — working tree limpa.

## Proximo passo exato

1. **Buildar AppImage no Linux** — clonar repo numa maquina Linux, `pip install -r requirements.txt pyinstaller`, rodar `./scripts/build_appimage.sh`, testar o .AppImage
2. **Publicar release v1.4.0** — subir o .AppImage + instalador Windows no GitHub Releases
3. **Testar instalador Linux** — rodar `curl -fsSL .../install_linux.sh | bash` numa maquina limpa

## Arquivos a ler

- `src/platform/__init__.py` — auto-detect de plataforma
- `src/platform/_linux.py` — backend Linux (config_dir, RAM, flock, zenity, xdg-open)
- `src/platform/_windows.py` — backend Windows (extraido do codigo original)
- `scribe4me_linux.spec` — PyInstaller spec para Linux
- `scripts/build_appimage.sh` — build do AppImage
- `scripts/install_linux.sh` — instalador curl|bash

## Contexto importante

- O repo remoto esta atualizado (push feito)
- Suporte Linux usa X11/XWayland — Wayland puro nao suportado (pynput)
- Dependencias Linux: xclip, libportaudio2, libappindicator3-1
- Hotkeys sao persistidos em config_dir/config.json (~/.config/Scribe4me/ no Linux)
- NAO sugerir modelos menores ou streaming para STT — Felipe ja testou, qualidade cai demais em PT-BR
- Tarefa de buildar AppImage foi adicionada no Kanban do vault (SECONDBRAIN)
