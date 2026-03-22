---
description: Encerra a sessão de trabalho — verifica documentação, atualiza HANDOFF, faz commit e push
---

Você está encarregado do encerramento da sessão de trabalho. Seu papel é garantir que nenhuma informação importante fique para trás e que o HANDOFF seja atualizado corretamente. Execute cada passo em ordem.

---

1. **Estado real do repositório**
// turbo
Rodar `git status --short` e `git log --oneline -5` para entender o que está modificado, não rastreado e o último commit.

2. **Verificação do ROADMAP (`docs/ROADMAP.md`)**
Ler o arquivo e verificar:
- Todas as tasks concluídas nesta sessão estão marcadas como `✅`?
- Tasks desbloqueadas por essas conclusões estão como `⏳` (não `🔒`)?
- A linha `*Última atualização:*` no final reflete a data de hoje e o que foi feito?
*Se algo estiver desatualizado:* corrija agora usando as ferramentas de edição de arquivo.

3. **Verificação do diário (`docs/daily/YYYY-MM-DD.md`)**
Localizar o arquivo do dia de hoje (ou criá-lo se não existir). Verifique se contém:
- Resumo de todas as tasks processadas na sessão (arquivos tocados, decisões).
- Status final de testes e revisões para essas tasks.
*Se o diário estiver incompleto:* adicione as informações que faltam.

4. **Verificação do HANDOFF (`docs/HANDOFF.md`)**
Esta é a parte **mais crítica**. Sobrescreva ou atualize completamente o HANDOFF para refletir o estado exato do fim desta sessão:
- `Meta`: ajuste a hora, carimbe com "Antigravity", coloque o nome da máquina e o último commit.
- `Task em andamento` e `Próximo passo exato`: apontar exatamente para o que o próximo agente deve fazer.
- `Pendências de commit`: relatar o que o `git status` mostrou (ou "working tree limpa").
*O HANDOFF deve sempre ser commitado nesta sessão.*

5. **Verificação do MEMORY.md e Chitchat**
- Avaliar se algum aprendizado estável (armadilhas, regras novas) precisa ir para o `MEMORY.md`.
- Avaliar se alguma decisão de protocolo precisa ir para `docs/chitchat/antigravity-implementations.md` (seção de registro de sessão).
*Atualizar apenas se houver informação realmente nova.*

6. **Relatório e Aprovação**
Apresente ao usuário o seguinte relatório:
```
ENCERRAMENTO DE SESSÃO — <data>

ROADMAP:         ✅ atualizado / ⚠️ corrigido agora / ❌ problema encontrado
Diário:          ✅ completo / ⚠️ completado agora / ❌ problema encontrado
HANDOFF:         ✅ atualizado / ⚠️ corrigido agora / ❌ problema encontrado
MEMORY.md:       ✅ sem mudanças / ⚠️ atualizado / ❌ problema encontrado
Chitchat docs:   ✅ sem mudanças / ⚠️ atualizado / ❌ problema encontrado

Arquivos a commitar:
- <lista dos arquivos que serão incluídos no commit>

Mensagem de commit proposta:
  docs(session): encerramento YYYY-MM-DD — <resumo do que foi feito>
```
**PARE AQUI. Aguarde a aprovação clara do usuário antes de avançar para o passo 7.**

7. **Commit e Push**
Após a aprovação do usuário:
- Propor comando para commitar os arquivos modificados (sempre incluir o `docs/HANDOFF.md` e o diário).
- Mensagem de commit: `docs(session): encerramento YYYY-MM-DD — <resumo do dia>`
- Co-Authored-By: `Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>`
- Propor o `git push origin main`.
