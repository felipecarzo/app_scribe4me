---
description: Encerra uma sessão exploratória curta — atualiza o HANDOFF e faz commit/push
---

Você está encarregado do encerramento rápido de uma sessão de trabalho curta ou exploratória. Este workflow dispensa a verificação de ROADMAP e geração de diário, focando apenas em preservar o estado atual do repositório para o próximo agente.

---

1. **Estado real do repositório**
// turbo
Rodar `git status --short` e `git log --oneline -5` para entender exatamente o que foi modificado e qual o último commit.

2. **Verificação do HANDOFF (`docs/HANDOFF.md`)**
Sobrescreva ou atualize completamente o HANDOFF para refletir o estado de fim de sessão:
- `Meta`: ajuste a hora, carimbe com "Antigravity", coloque o nome da máquina e o último commit.
- `Task em andamento` e `Próximo passo exato`: apontar exatamente para onde o trabalho parou.
- `Pendências de commit`: relatar o que o `git status` mostrou.

3. **Relatório Rápido e Aprovação**
Apresente ao usuário o seguinte relatório:
```
ENCERRAMENTO RÁPIDO — <data>

HANDOFF:         ✅ atualizado

Arquivos a commitar:
- <lista dos arquivos que serão incluídos no commit>

Mensagem de commit proposta:
  docs(session): encerramento rápido YYYY-MM-DD — <resumo do que foi feito na exploração>
```
**PARE AQUI. Aguarde a aprovação clara do usuário antes de avançar para o passo 4.**

4. **Commit e Push**
Após a aprovação do usuário:
- Propor comando para commitar os arquivos modificados (sempre incluir o `docs/HANDOFF.md`).
- Mensagem de commit como definida no passo 3, incluindo a assinatura: `Co-Authored-By: Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>`
- Propor ou rodar o `git push origin main`.
