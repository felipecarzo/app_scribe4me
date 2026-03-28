# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-03-27
- **Branch:** main
- **Ultimo commit:** a31585e — feat: Scribe4me v1.2.0
- **Release:** v1.2.0 publicada no GitHub

## Estado do projeto

Scribe4me v1.2.0 — app desktop Windows de speech-to-text local com Whisper.
Versao publica, funcional, com instalador disponivel para download.

## Task em andamento

Nenhuma — sessao encerrada com tudo entregue.

## Pendencias de commit

Nenhuma — working tree limpa.

## Proximo passo exato

Opcoes para a proxima sessao:
1. **Governanca** — criar ROADMAP.md com sprints e tasks formais
2. **SpeedOsper** — retomar integracao com Motor Ayvu (versao local, nao publicada)
3. **Melhorias Scribe4me** — novas features baseadas em feedback de uso

## Arquivos a ler

- `docs/SCRIBE4ME_V2_PLAN.md` — plano da v2 com Motor Ayvu (referencia futura)
- `src/tray.py` — menu do tray e estados visuais
- `src/prompt_editor.py` — editor de prompt personalizado
- `src/config.py` — persistencia de configuracao

## Contexto importante

- O repo remoto foi limpo — SpeedOsper v3 (29 commits) foi substituido pelo Scribe4me v1.2
- SpeedOsper existe apenas localmente no reflog (expira em ~90 dias)
- O instalador tem 192 MB (tkinter + dependencias extras inflaram o tamanho)
- O .gitignore inclui `.claude/`, `dist/`, `build_*/`, `installer_output/`
