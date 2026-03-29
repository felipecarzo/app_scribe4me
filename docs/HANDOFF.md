# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-03-29
- **Branch:** main
- **Ultimo commit:** 195ee9b — feat: cancelar gravacao, toggle modo saida e README atualizado
- **Release:** v1.3.0 publicada no GitHub

## Estado do projeto

Scribe4me v1.3.0 — app desktop Windows de speech-to-text local com Whisper.
Versao publica com atalhos personalizaveis, cancelamento de gravacao, toggle de modo de saida e logs diarios.

## Task em andamento

Nenhuma — sessao encerrada com tudo entregue.

## Pendencias de commit

Nenhuma — working tree limpa.

## Proximo passo exato

Opcoes para a proxima sessao:
1. **Governanca** — criar ROADMAP.md com sprints e tasks formais
2. **SpeedOsper** — retomar integracao com Motor Ayvu (versao local, nao publicada)
3. **Melhorias Scribe4me** — novas features baseadas em feedback de uso
4. **Testes** — criar suite de testes para as novas features (hotkey_editor, config persistence)

## Arquivos a ler

- `src/hotkey_editor.py` — editor de atalhos (novo na v1.3)
- `src/config.py` — persistencia de hotkeys e output_mode
- `src/main.py` — orquestrador com hotkeys dinamicos
- `src/tray.py` — menu com labels dinamicos e toggle de modo
- `docs/SCRIBE4ME_V2_PLAN.md` — plano da v2 com Motor Ayvu (referencia futura)

## Contexto importante

- O repo remoto esta atualizado (push feito, release v1.3.0 publicada)
- Hotkeys sao persistidos em %LOCALAPPDATA%/Scribe4me/config.json
- Output mode tambem persiste no config.json
- Logs diarios em %LOCALAPPDATA%/Scribe4me/logs/YYYY-MM-DD.log (sem expiracao)
- NAO sugerir modelos menores ou streaming para STT — Felipe ja testou, qualidade cai demais em PT-BR
- O instalador tem 194 MB (tkinter + dependencias)
- O .gitignore inclui `.claude/`, `dist/`, `build_*/`, `installer_output/`
