# Scribe4me — Conteudo para Portfolio (carzo.com.br)

Arquivo de referencia com textos, links e assets para a pagina do projeto no portfolio.

---

## Titulo

**Scribe4me** — Speech-to-text local com IA

## Subtitulo / tagline

Transcreva sua voz em texto em qualquer campo, sem internet, sem assinatura.

## Descricao curta (para card no portfolio)

Aplicativo de transcrição de voz para texto com IA, 100% local e privado. Funciona como um assistente invisível na bandeja do sistema: pressione um atalho, fale, e o texto aparece onde seu cursor estiver. Suporta Whisper local (offline) e APIs externas (OpenAI, Groq, Gemini, Deepgram) para maior velocidade.

## Descricao longa (para pagina do projeto)

O Scribe4me nasceu de uma necessidade real: transcrever voz para texto de forma rápida, discreta e sem depender de serviços de nuvem. Ele roda silenciosamente na bandeja do sistema e é ativado por atalhos de teclado configuráveis.

### Como funciona

1. Pressione **Ctrl+Alt+H** (segure e fale) — ou configure o atalho que preferir
2. Fale normalmente
3. Solte a tecla
4. O texto transcrito aparece onde seu cursor estiver — ou na área de transferência

Nenhum dado sai do seu computador por padrão. O modelo Whisper roda 100% localmente, com suporte a GPU NVIDIA para acelerar a transcrição.

### Para quem é

- Profissionais que ditam textos, e-mails ou documentos
- Desenvolvedores que querem transcrição sem subscrição
- Qualquer pessoa que prefere falar a digitar

### Destaques técnicos

- **Whisper local** via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2 — sem PyTorch)
- **4 backends de API opcionais**: OpenAI, Groq, Gemini, Deepgram
- **Realtime WebSocket** com Deepgram: texto parcial aparece enquanto fala
- **Overlay flutuante** para feedback visual no modo realtime
- **Janela de configurações unificada**: modelo, atalhos, prompt e API em um só lugar
- Detecção automática de hardware (VRAM, RAM) para recomendar o modelo ideal
- Logs diários em arquivo — recupere qualquer transcrição de qualquer dia
- **Cross-platform**: Windows, Linux e macOS

## Stack / Tecnologias (para tags no portfolio)

Python · Whisper · faster-whisper · pystray · pynput · tkinter · PyInstaller · WebSocket · httpx · sounddevice · GitHub Actions

## Links

- **GitHub**: https://github.com/felipecarzo/app_scribe4me
- **Download Windows**: https://github.com/felipecarzo/app_scribe4me/releases/latest
- **Download macOS**: https://github.com/felipecarzo/app_scribe4me/releases/latest
- **Download Linux**: https://github.com/felipecarzo/app_scribe4me/releases/latest

## Botoes sugeridos para a pagina

```
[Ver no GitHub]  →  https://github.com/felipecarzo/app_scribe4me
[Baixar para Windows]  →  link direto para o .exe no release
[Baixar para macOS]  →  link direto para o .dmg no release
[Baixar para Linux]  →  link direto para o AppImage no release
```

## Screenshots / Assets disponíveis

- `assets/banner.png` — banner do projeto (usa no header da pagina)
- `assets/scribe4me_256.png` — icone do app

## Versao atual

v1.5.0

## Categoria sugerida no portfolio

Ferramentas de produtividade / Inteligência Artificial / Desktop Apps
