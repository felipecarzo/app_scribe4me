#!/bin/bash
# Helper — Append-only log para docs/LIVE_STATUS.md
# Uso: status-log.sh "mensagem"
# Exemplo: status-log.sh "pytest AgentTest — PASS 100/100"

MESSAGE="${1:-}"
[ -z "$MESSAGE" ] && exit 1

ROLE_FILE=".claude/instance-role.local.json"
ROLE_NAME="UNKNOWN"

if [ -f "$ROLE_FILE" ]; then
  ROLE_NAME=$(python3 -c "import json; d=json.load(open('$ROLE_FILE')); print(d.get('display_name', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LIVE_STATUS_FILE="docs/LIVE_STATUS.md"

# Append ao arquivo (simples, sem lock)
echo "[$TIMESTAMP] [$ROLE_NAME]: $MESSAGE" >> "$LIVE_STATUS_FILE"

exit 0
