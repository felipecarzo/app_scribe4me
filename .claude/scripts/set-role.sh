#!/bin/bash
# set-role.sh — Implementação do comando /set-role
# Uso: bash .claude/scripts/set-role.sh <role-name>
# Exemplo: bash .claude/scripts/set-role.sh qa-engineer

ROLE_NAME="${1:-}"
[ -z "$ROLE_NAME" ] && {
  echo "[ERROR] Uso: set-role.sh <role-name>"
  echo ""
  echo "Roles disponíveis:"
  echo "  - eddie-morra   (Orquestrador, acesso total)"
  echo "  - senior-dev    (Backend)"
  echo "  - ui-engineer   (Frontend)"
  echo "  - fullstack     (Front + Back)"
  echo "  - qa-engineer   (Tester)"
  echo "  - tech-writer   (Pesquisa & Docs)"
  echo "  - data-analyst  (Cientista de dados)"
  echo "  - observer      (Monitor, somente leitura)"
  exit 1
}

ROLE_FILE=".claude/roles/$ROLE_NAME.json"
INSTANCE_FILE=".claude/instance-role.local.json"

[ ! -f "$ROLE_FILE" ] && {
  echo "❌ Role não encontrado: $ROLE_FILE"
  exit 1
}

# Copiar template para instance-role.local.json
cp "$ROLE_FILE" "$INSTANCE_FILE"

# Adicionar timestamp + instance_id (para roles multi-instância)
python3 -c "
import json, os, random, string
from datetime import datetime

with open('$INSTANCE_FILE') as f:
    data = json.load(f)

data['started_at'] = datetime.now().isoformat()

# Gerar instance_id unico para roles multi-instancia
role = data.get('role', '')
ts = datetime.now().strftime('%Y%m%d-%H%M%S')
suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
data['instance_id'] = f'{role}-{ts}-{suffix}'

with open('$INSTANCE_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"

# Exibir o que foi ativado
DISPLAY_NAME=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print(d.get('display_name', 'UNKNOWN'))" 2>/dev/null)
WORKSPACE_WRITE=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); ws=d.get('workspace_write',[]); print(', '.join(ws) if '*' not in ws else '*')" 2>/dev/null)
WORKSPACE_READ=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print(d.get('workspace_read', ['*'])[0])" 2>/dev/null)
GIT_COMMIT=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print('[OK]' if d.get('git_commit') else '[NO]')" 2>/dev/null)
GIT_PUSH=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print('[OK]' if d.get('git_push') else '[NO]')" 2>/dev/null)
GIT_PULL=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print('[OK]' if d.get('git_pull') else '[NO]')" 2>/dev/null)

INSTANCE_ID=$(python3 -c "import json; d=json.load(open('$INSTANCE_FILE')); print(d.get('instance_id', 'unknown'))" 2>/dev/null)

echo ""
echo "[OK] Role ativado: $DISPLAY_NAME"
echo "Instance ID:      $INSTANCE_ID"
echo ""
echo "Workspace Write:  $WORKSPACE_WRITE"
echo "Workspace Read:   $WORKSPACE_READ"
echo "Git Commit:       $GIT_COMMIT"
echo "Git Push:         $GIT_PUSH"
echo "Git Pull:         $GIT_PULL"
echo ""
echo "Use o instance_id nos nomes de arquivo para evitar colisao entre instancias."
echo "Ex: reports/${INSTANCE_ID}_resultado.json"
echo ""

# Escrever arquivo por sessão (para statusline por terminal)
SESSION_TMP=".claude/current-session.tmp"
if [ -f "$SESSION_TMP" ]; then
  SESSION_ID=$(tr -d '\r\n' < "$SESSION_TMP")
  if [ -n "$SESSION_ID" ]; then
    mkdir -p ".claude/sessions"
    cp "$INSTANCE_FILE" ".claude/sessions/${SESSION_ID}.json"
    echo "Session file: .claude/sessions/${SESSION_ID}.json"
  fi
fi

# Registrar no LIVE_STATUS
bash .claude/scripts/status-log.sh "$DISPLAY_NAME" "Role ativado — Instance: $INSTANCE_ID"
