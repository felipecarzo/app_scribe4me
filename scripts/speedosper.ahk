; speedosper.ahk — Bloqueia Win+H nativo do Windows
; O app Python (main.py) captura Win+H via lib keyboard.
; Este script e uma camada extra para garantir que o
; Windows Voice Typing nao ative junto.
;
; Como usar: rodar este .ahk ANTES de iniciar o app Python.
; Requer AutoHotKey v2 instalado.

#Requires AutoHotkey v2.0

; Bloqueia Win+H nativo (Windows Voice Typing)
#h::return

; Bloqueia Win+Shift+H nativo (se existir)
#+h::return
