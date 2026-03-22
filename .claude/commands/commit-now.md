---
name: commit-now
description: Commit rápido na branch atual com mensagem gerada automaticamente
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*)
---

Faça um commit rápido de tudo que está modificado na branch atual e push para o remoto.

Siga estes passos:

1. Rode `git status` para ver o que está staged e untracked.
2. Rode `git diff HEAD` para entender o que mudou.
3. Rode `git log --oneline -5` para seguir o padrão de mensagem de commit do projeto.
4. Analise as mudanças e gere uma mensagem de commit no formato do projeto:
   `type(scope): mensagem descritiva`
   - Types: feat, fix, docs, refactor, test, chore
   - Scope: módulo afetado
   - Mensagem curta e objetiva em português ou inglês (siga o padrão dos commits recentes)
5. Adicione os arquivos modificados com `git add` — prefira adicionar por nome, evite `git add .` se houver arquivos sensíveis.
6. Crie o commit com a mensagem usando HEREDOC:
   ```
   git commit -m "$(cat <<'EOF'
   type(scope): mensagem

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```
7. Faça push para a branch atual: `git push`
8. Confirme com `git status` que está limpo.

Regras:
- Nunca commite arquivos `.env`, credenciais ou segredos
- Se houver arquivos não relacionados ao escopo principal, commite apenas os relevantes
- Se `git push` falhar por upstream não configurado, use `git push -u origin $(git branch --show-current)`
- Informe o hash do commit e a branch no final
