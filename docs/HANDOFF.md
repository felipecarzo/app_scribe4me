# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** cbfc1ff — feat(ui): UI premium dark mode + overlay pilula + fix build
- **Agente:** Claude Opus 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Scribe4me v1.5.0 — app desktop speech-to-text cross-platform (Windows/Linux/macOS).
Release v1.5.0 atualizada no GitHub com instalador Windows rebuilado (inclui customtkinter + darkdetect).
Scribe4me v2.0 iniciado em repo separado (`app_scribe4me_v2`) com Tauri + Svelte.

## Task em andamento

Nenhuma de codigo no v1. Pendencias manuais:
1. Build AppImage Linux (precisa de maquina Linux)
2. Testar build macOS em hardware real (CI gera DMG ao criar tag)
3. Atualizar portfolio carzo.com.br com conteudo de `docs/portfolio.md`

## Pendencias de commit

Nenhuma — working tree limpa apos commit `cbfc1ff`.

## Proximo passo exato

### Para este repo (v1.5.0):
- Pendencias manuais apenas (S5-07, S5-08, S5-09) — nao ha codigo a implementar

### Para o repo v2.0 (app_scribe4me_v2):
1. Abrir sessao no diretorio `D:\documentos\ti\projetos\app_scribe4me_v2`
2. Rodar /start-session para carregar contexto do v2
3. Iniciar Sprint 2: migrar modulos Python do v1 para sidecar
4. Usar /autopilot para execucao autonoma

## Arquivos relevantes para proxima sessao

- `docs/portfolio.md` — conteudo pronto para carzo.com.br
- `scribe4me.spec` — atualizado com customtkinter/darkdetect
- `scribe4me_installer.iss` — VersionInfo corrigida para 1.5.0
- `src/settings_window.py` — migrado para CustomTkinter (Antigravity)
- `src/realtime_overlay.py` — redesign pilula (Antigravity)

## Estado do ROADMAP

| Task | Status |
|------|--------|
| S5-03 Configuracoes unificadas | CONCLUIDO |
| S5-04 Suporte macOS | CONCLUIDO |
| S5-05 README atualizado | CONCLUIDO |
| S5-06 Portfolio content | CONCLUIDO |
| S5-07 Build AppImage Linux | PENDENTE (manual) |
| S5-08 Testar macOS em hardware | PENDENTE (aguarda CI) |
| S5-09 Portfolio carzo.com.br | PENDENTE (manual) |

## Contexto importante

- Repo v1: github.com/felipecarzo/app_scribe4me
- Repo v2: github.com/felipecarzo/app_scribe4me_v2 (Tauri + Svelte + Python sidecar)
- Release v1.5.0 no GitHub tem .exe rebuilado (2026-04-12) e .dmg do CI
- NAO sugerir modelos menores ou streaming para STT — qualidade em PT-BR cai
- Inno Setup em `C:\Users\lfeli.ALIENWARE-LIPE\AppData\Local\Programs\Inno Setup 6\ISCC.exe`
- SpeedOsper (fork com Motor Ayvu) — projeto separado, apenas local, nao publicar
