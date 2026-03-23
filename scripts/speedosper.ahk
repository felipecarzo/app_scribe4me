; speedosper.ahk — Intercepta Win+H e redireciona para o app Python
; O AHK bloqueia o Win+H nativo e envia F20/F21 como teclas internas.
; O app Python escuta F20 (push-to-talk) e F21 (toggle).
;
; Requer AutoHotkey v2.0+
; Rodar ANTES de iniciar o app Python.

#Requires AutoHotkey v2.0

; Win+H pressionado -> envia F20 down
#h::{
    Send "{F20 down}"
    KeyWait "h"
    Send "{F20 up}"
}

; Win+Shift+H -> envia F21 (toggle, so precisa do press)
#+h::{
    Send "{F21}"
}
