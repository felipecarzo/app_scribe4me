---
name: pull-now
description: Avalia commits pendentes no remoto e faz git pull com aprovação do usuário
allowed-tools: Bash(git fetch:*), Bash(git log:*), Bash(git status:*), Bash(git pull:*), Bash(git branch:*)
---

Avalie o que há de novo no repositório remoto e peça aprovação antes de puxar.

Siga estes passos:

1. Rode `git fetch origin` para atualizar as referências remotas sem modificar a working tree.

2. Identifique a branch atual:
   ```
   git branch --show-current
   ```

3. Compare local vs remoto:
   ```
   git log HEAD..origin/<branch> --oneline --no-merges
   ```
   Se não houver commits novos, informe o usuário que o repositório já está atualizado e encerre.

4. Mostre um resumo claro dos commits pendentes com autor, data e mensagem:
   ```
   git log HEAD..origin/<branch> --pretty=format:"%h  %an  %ar  %s" --no-merges
   ```

5. Mostre também o diff estatístico (quais arquivos serão afetados):
   ```
   git diff --stat HEAD..origin/<branch>
   ```

6. Apresente ao usuário um relatório neste formato:
   ```
   Pull disponível — <branch>

   Commits novos: N
   Último push: <data relativa> por <autor> (<hash>)

   Commits:
   <hash>  <autor>  <data>  <mensagem>
   ...

   Arquivos afetados:
   <stat output>
   ```

7. **Aguarde aprovação explícita do usuário** usando AskUserQuestion:
   - Pergunta: "Deseja fazer o pull desses N commits?"
   - Se o usuário aprovar: execute `git pull origin <branch>`
   - Se o usuário recusar: encerre sem fazer nada

8. Após o pull bem-sucedido, confirme com `git log --oneline -3` para mostrar o estado atual da branch.

Regras:
- Nunca faça `git pull` sem aprovação explícita do usuário
- Se houver mudanças locais não commitadas (`git status`), avise o usuário antes de puxar — o pull pode causar conflito
- Se o pull falhar por conflito, informe e sugira resolver manualmente
- Informe o hash do commit mais recente e a branch ao final
