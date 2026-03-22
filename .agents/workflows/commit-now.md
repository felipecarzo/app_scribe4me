---
description: commit rápido com padrão type(scope) + Co-Authored-By
---

1. Rodar `git status --short` para ver o que está staged/unstaged
// turbo
2. Rodar `git diff --name-only HEAD` para confirmar arquivos modificados
// turbo
3. Com base nos arquivos, determinar:
   - `type`: feat / fix / docs / refactor / test / chore
   - `scope`: módulo afetado (adapte para os escopos do seu projeto)
   - `mensagem`: curta, imperativa (seguir padrão já usado no repo)

4. Propor o comando de commit no formato:
```
git add {arquivos relevantes}
git commit -m "{type}({scope}): {mensagem curta}

{corpo opcional se necessário}

Co-Authored-By: Antigravity (Gemini Advanced, Google DeepMind) <noreply@google.com>"
```

5. Após aprovação do usuário, rodar `git push origin main`
