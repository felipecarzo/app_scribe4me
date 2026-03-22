# /authorize — Emitir ticket de autorização temporária

Uso: `/authorize <role> <permissões> <duração> [motivo]`

## Exemplos

```bash
/authorize ui-engineer bash:install 2h "Instalar dependência X"
/authorize senior-dev workspace:frontend/ 4h "Ajustar componente compartilhado"
/authorize qa-engineer bash:install,workspace:src/ 30m "Instalar dependência de teste"
```

## Permissões disponíveis

| Permissão | O que libera |
|-----------|-------------|
| `bash:install` | Comandos de instalação (pip, npm, choco, winget, apt) |
| `bash:*` | Qualquer comando Bash (sem restrição) |
| `workspace:<path>` | Escrita em diretório adicional (ex: `workspace:src/`) |
| `git:push` | Permissão temporária de git push |
| `git:pull` | Permissão temporária de git pull |
| `git:*` | Push + Pull |

## Duração

Formatos aceitos: `30m`, `1h`, `2h`, `4h`, `8h`, `1d`

## O que acontece

1. Verifica se o emissor é `eddie-morra` ou sem role (acesso total)
2. Cria ticket em `.claude/tickets/TKT-{timestamp}.json`
3. Registra no `docs/LIVE_STATUS.md`
4. Exibe o ticket emitido com ID e expiração

## Regras

- **Apenas eddie-morra (ou sem role) pode emitir tickets**
- Tickets expiram automaticamente pelo tempo definido
- O workspace-guard.sh verifica tickets válidos antes de bloquear
- Tickets expirados ficam no diretório como audit trail (status: "expired")

## Instrução para Claude

Ao receber `/authorize`, faça:

1. Parse os argumentos: role, permissões (comma-separated), duração, motivo opcional
2. Verifique se o terminal atual é eddie-morra ou sem role. Se não for, recuse.
3. Calcule `expires_at` baseado na duração (a partir de agora)
4. Crie o ticket JSON em `.claude/tickets/TKT-{YYYYMMDD}-{HHMMSS}.json`:

```json
{
  "id": "TKT-20260317-163000",
  "granted_to": "<role>",
  "granted_by": "eddie-morra",
  "permissions": ["bash:install", "workspace:frontend/"],
  "reason": "<motivo>",
  "created_at": "2026-03-17T16:30:00",
  "expires_at": "2026-03-17T18:30:00",
  "status": "active"
}
```

5. Registre no LIVE_STATUS.md: `[TICKET] TKT-xxx emitido para <role>: <permissões> (expira <hora>)`
6. Exiba resumo do ticket emitido
