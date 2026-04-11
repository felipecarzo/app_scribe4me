# HANDOFF — Scribe4me

## Meta

- **Data:** 2026-04-11
- **Branch:** main
- **Ultimo commit:** 7bcdb26 — feat(macos): suporte a macOS — tray main thread, backend de plataforma, spec e CI
- **Agente:** Claude Sonnet 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Scribe4me v1.5.0 — app desktop speech-to-text cross-platform (Windows/Linux/macOS).
- Janela de configuracoes unificada (4 abas: Geral, Atalhos, Prompt, API)
- Suporte macOS implementado: platform backend, tray run_blocking para Cocoa main thread
- CI GitHub Actions para build macOS automatico (tag v*)
- README e portfolio content atualizados

## Task em andamento

Nenhuma de codigo. Pendencias manuais:
1. Build AppImage Linux (precisa de maquina Linux)
2. Testar build macOS em hardware real (CI vai gerar o DMG)
3. Atualizar portfolio carzo.com.br com conteudo de `docs/portfolio.md`

## Pendencias de commit

Nenhuma — working tree limpa apos commit `7bcdb26`.

## Proximo passo exato

### Para buildar AppImage Linux:
1. Clonar repo numa maquina Linux
2. `pip install -r requirements.txt pyinstaller`
3. `chmod +x scripts/build_appimage.sh && ./scripts/build_appimage.sh`
4. Testar o .AppImage gerado
5. Adicionar na GitHub Release v1.5.0 (ou criar v1.5.1)

### Para build macOS via CI:
1. Criar tag `v1.5.0` no GitHub: `git tag v1.5.0 && git push origin v1.5.0`
2. O workflow `.github/workflows/build-macos.yml` roda automaticamente
3. Baixar o DMG do artifacts e testar num Mac

### Para portfolio carzo.com.br:
- Conteudo pronto em `docs/portfolio.md`
- Downloads devem apontar para `github.com/felipecarzo/app_scribe4me/releases/latest`

## Arquivos relevantes para proxima sessao

- `docs/portfolio.md` — conteudo pronto para carzo.com.br
- `.github/workflows/build-macos.yml` — CI macOS
- `scribe4me_macos.spec` — spec PyInstaller para macOS
- `src/platform/_macos.py` — backend macOS
- `src/tray.py` — run_blocking() para macOS (linha ~180)
- `src/main.py` — _run_app_logic() e run() com logica macOS (linha ~451)
- `scripts/build_appimage.sh` — script de build Linux

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

- Repo GitHub: github.com/felipecarzo/app_scribe4me
- macOS requer permissao de acessibilidade para pynput (hotkeys globais) — usuario precisa conceder manualmente na primeira execucao
- macOS: `LSUIElement=True` no Info.plist — app nao aparece no Dock, apenas na barra de status
- NAO sugerir modelos menores ou streaming para STT local — Felipe ja testou, qualidade cai em PT-BR
- SpeedOsper (fork com Motor Ayvu) — projeto separado, apenas local, nao publicar
- Inno Setup em `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
