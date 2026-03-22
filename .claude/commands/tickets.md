# /tickets — Listar tickets de autorização

Uso: `/tickets [role]`

## Exemplos

```bash
/tickets              # Lista todos os tickets ativos
/tickets ui-engineer  # Lista tickets do ui-engineer
/tickets all          # Lista todos (ativos + expirados)
```

## Instrução para Claude

Ao receber `/tickets`, faça:

1. Leia todos os arquivos em `.claude/tickets/TKT-*.json`
2. Para cada ticket, verifique se `expires_at` já passou:
   - Se sim e status é "active", atualize para "expired" (escreva de volta no arquivo)
3. Filtre por role se especificado
4. Exiba em formato tabela:

```
Tickets Ativos:
| ID | Role | Permissões | Expira em | Motivo |
|----|------|-----------|-----------|--------|
| TKT-20260317-163000 | ui-engineer | bash:install | 1h 23m | Instalar poppler |

Tickets Expirados (últimos 5):
| ID | Role | Permissões | Expirou em | Motivo |
|----|------|-----------|-----------|--------|
| TKT-20260317-140000 | senior-dev | workspace:frontend/ | 2h atrás | Fix compartilhado |
```

Se não houver tickets, exiba: "Nenhum ticket ativo."
