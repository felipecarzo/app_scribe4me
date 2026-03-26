# UIP-01 — UI Polish + Migracao pynput

## Objetivo
Eliminar dependencia do AutoHotkey e da lib `keyboard`, migrando hotkeys para `pynput`. Adicionar estados visuais completos no tray icon, notificacoes nativas Windows, menu de contexto enriquecido, e bundle PyInstaller sem console.

## Arquivos afetados

| Arquivo | Acao | Impacto |
|---------|------|---------|
| `src/config.py` | Alterar hotkeys de F20/F21 para combinacoes pynput | Baixo |
| `src/tray.py` | Reescrever — novos estados, piscar, menu, notificacoes | Alto |
| `src/clipboard.py` | Expor ultimo texto para menu "copiar ultimo" | Baixo |
| `src/main.py` | Reescrever parcialmente — remover AHK/keyboard, usar pynput Listener | Alto |
| `requirements.txt` | Adicionar pystray/Pillow, remover keyboard | Baixo |
| `speedosper.spec` | console=False, remover AHK, hiddenimports | Medio |
| `scripts/speedosper.ahk` | Remover | Baixo |

## Mudancas detalhadas

### src/config.py
- `hotkey_push_to_talk`: `"f20"` -> combinacao pynput `<cmd>+h` (Win+H)
- `hotkey_toggle`: `"f21"` -> `<cmd>+<shift>+h` (Win+Shift+H)
- Adicionar `hotkey_quit: str = "<ctrl>+q"`

### src/tray.py

**Novo enum AppState:**
- IDLE = verde `#4CAF50`
- RECORDING = vermelho `#F44336`
- TRANSCRIBING = vermelho `#F44336` **piscando** (alterna com transparente a cada 500ms)
- READY_TO_COPY = azul `#2196F3` (novo estado)

**Menu de contexto:**
```
SpeedOsper (titulo, desabilitado)
---
Copiar ultimo texto  -> pyperclip.copy(last_text)
Abrir log            -> os.startfile(log_path)
---
Sair (Ctrl+Q)        -> quit
```

**Notificacoes:** Usar `pystray.Icon.notify()` primeiro (balloon tips nativos). Se insuficiente, avaliar `winotify`.

### src/main.py

**Remover:** import keyboard, subprocess, _find_ahk_exe(), _start_ahk(), _stop_ahk(), _ahk_process, logica F20/F21.

**Adicionar:** pynput Listener unico com on_press/on_release, tracking de modifiers.

**Fluxo de estados:**
```
IDLE --[Win+H press]--> RECORDING --[Win+H release]--> TRANSCRIBING --[texto pronto]--> READY_TO_COPY --[Ctrl+V ou timeout 10s]--> IDLE
```

**Abordagem:** Listener unico de baixo nivel (Opcao A). Detecta Win+H press/release para push-to-talk, Win+Shift+H para toggle, Ctrl+Q para quit.

### src/clipboard.py
- Armazenar `self._last_text` em `send()`
- Expor via propriedade `last_text`

### requirements.txt
- Adicionar: `pystray>=0.19.5`, `Pillow>=10.0.0`
- Remover: `keyboard>=0.13.5`
- Avaliar: `winotify>=1.1.0` (so se pystray.notify for insuficiente)

### speedosper.spec
- Remover `('scripts/speedosper.ahk', 'scripts')` dos datas
- `console=False`
- Adicionar hiddenimports: pystray, pynput, winotify (se usado)

### scripts/speedosper.ahk
- Deletar arquivo

## Ordem de implementacao

| Passo | Descricao | Arquivos |
|-------|-----------|----------|
| 1 | Atualizar config com hotkeys pynput | `src/config.py` |
| 2 | Reescrever tray.py: novos estados, piscar, menu, notificacoes | `src/tray.py` |
| 3 | Alterar clipboard.py: last_text | `src/clipboard.py` |
| 4 | Reescrever hotkeys em main.py: remover AHK/keyboard, pynput Listener | `src/main.py` |
| 5 | Atualizar requirements.txt | `requirements.txt` |
| 6 | Atualizar spec: console=False, remover AHK | `speedosper.spec` |
| 7 | Remover scripts/speedosper.ahk | `scripts/` |
| 8 | Teste manual E2E | -- |

## Riscos

| Risco | Prob. | Mitigacao |
|-------|-------|-----------|
| pynput nao suprime Win+H nativo (abre dictation) | Media-Alta | `win32_event_filter` com suppress. Se falhar, hotkey alternativa (Ctrl+Shift+H) |
| winotify nao funciona no PyInstaller | Media | Fallback: pystray.notify() |
| console=False esconde prints | Baixa | Redirecionar para logging/arquivo |

## Decisoes pendentes (Felipe)

1. **Supressao Win+H:** Se pynput nao conseguir, qual alternativa? (Ctrl+Shift+H, Ctrl+Alt+H, outra)
2. **Notificacoes:** pystray.notify() (simples) vs winotify (mais bonito). Testar pystray primeiro?
3. **Logging:** Adicionar logging para arquivo agora (necessario com console=False) ou task futura?

## Criterios de done

- [ ] Win+H push-to-talk funciona via pynput
- [ ] Win+Shift+H toggle funciona via pynput
- [ ] Ctrl+Q encerra o app
- [ ] Win+H nativo suprimido
- [ ] Tray: verde (idle), vermelho (gravando), vermelho piscando (processando), azul (texto pronto)
- [ ] Notificacao nativa em cada transicao
- [ ] Menu: "Copiar ultimo texto", "Abrir log", "Sair"
- [ ] App roda sem terminal (console=False)
- [ ] speedosper.ahk removido
- [ ] keyboard removido do requirements
- [ ] PyInstaller build funciona
