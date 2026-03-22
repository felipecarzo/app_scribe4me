---
description: pull do último commit do origin/main com verificação de estado local
---

1. Rodar `git status --short` para verificar se há mudanças locais não commitadas
// turbo
2. Rodar `git log --oneline -3` para ver o estado atual do repo local
// turbo
3. Se houver mudanças locais não commitadas: alertar o usuário antes de continuar — não fazer pull sem resolver
4. Se estiver limpo: rodar `git pull origin main`
// turbo
5. Rodar `git log --oneline -3` para confirmar o que foi puxado
// turbo
