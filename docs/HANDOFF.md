# HANDOFF — Estado atual do projeto app_speedosper

> Arquivo vivo. Sobrescrito ao final de cada sessao, por qualquer agente.
> **Nao e um diario** — nao acumula historico. Para historico, ver `docs/daily/`.
> Qualquer agente (Claudio ou Antigravity) le este arquivo antes de qualquer acao.
> **Sempre validar contra `git status` + `git log` antes de confiar nas pendencias listadas aqui.**

---

## Meta
- **Ultima atualizacao:** 2026-03-25 — v2 completa (Sprints 4-7), arquitetura hibrida
- **Agente que escreveu:** Claudio
- **Maquina:** ALIENWARE-LIPE
- **Branch atual:** `main`
- **Ultimo commit:** `1ccc7ec` — feat(v2): modo hibrido — faster-whisper STT + Motor Ayvu translate/TTS

---

## Task em andamento
- **ID:** nenhuma
- **Descricao:** v2 feature-complete. Todas as tasks dos Sprints 0-7 concluidas.
- **Status:** aguardando proxima demanda do Felipe

---

## Proximo passo exato
1. Rodar `git status` e `git log --oneline -3` (protocolo anti-alucinacao)
2. Perguntar ao Felipe qual e a proxima direcao: teste em campo, novos features, ou bug fixes
3. Considerar: testes em maquina limpa com installer, documentacao de usuario

---

## Arquivos a ler no inicio da sessao
```text
CLAUDE.md
docs/ROADMAP.md
docs/HANDOFF.md
src/main.py         — orquestrador com 3 pipelines (scribe/translate/voice)
src/transcriber.py  — hibrido: faster-whisper STT + Motor Ayvu bridge
src/motor_bridge.py — wrapper ctypes para motor_ayvu.dll
src/config.py       — AppMode enum, SUPPORTED_LANGUAGES
```

---

## Contexto critico
- **Arquitetura hibrida v2:** faster-whisper (CTranslate2) para STT, Motor Ayvu (Rust ONNX) para translate/TTS
- STT via ONNX foi testado e rejeitado pelo Felipe por qualidade insuficiente
- Motor Ayvu DLL em: `D:\Documentos\Ti\projetos\app_ayvu\motor\target\release\motor_ayvu.dll`
- 3 modos: Scribe (transcreve), Translate (transcreve + traduz), Voice (transcreve + traduz + fala)
- 10 idiomas alvo suportados (en, es, fr, de, it, ja, ko, zh, ru, ar)
- 45 testes passando (pytest)
- Build: PyInstaller spec inclui motor_ayvu.dll + DirectML.dll
- Installer: Inno Setup v2.0.0

---

## Branches ativas

| Branch | Tipo | Ultimo commit | Estado |
|---|---|---|---|
| `main` | desenvolvimento ativo | `1ccc7ec` | v2 completa — Sprints 0-7 ✅ |

---

## Estado do ROADMAP (v2 completa)

| Sprint | Tasks | Status |
|---|---|---|
| Sprint 0 — Setup | SET-01, SET-02, SET-03 | ✅ |
| Sprint 1 — Core | REC-01, TRS-01, OUT-01, ORC-01 | ✅ |
| Sprint 2 — Integracao | AHK-01, AHK-02, E2E-01 | ✅ |
| Sprint 3 — Polimento | POL-01, POL-02, POL-03 | ✅ |
| Sprint 4 — C-ABI | FFI-01, FFI-02, FFI-03 | ✅ |
| Sprint 5 — Motor | INT-01 a INT-05 | ✅ |
| Sprint 6 — Translate | TRN-01 a TRN-05 | ✅ |
| Sprint 7 — Voice+Build | VOZ-01 a VOZ-03, BLD-01 a BLD-03 | ✅ |
