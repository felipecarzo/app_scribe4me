#!/bin/bash
# PreToolUse Hook — Workspace Isolation Guard
# Intercepta Edit, Write, Bash(rm/mv) e bloqueia se arquivo não está no workspace permitido
# Claude Code passa: CLAUDE_TOOL_NAME, CLAUDE_TOOL_PARAMS (JSON via stdin)
# Exit 2 = bloqueado; exit 0 = permitido

PROJECT="$(cd "$(dirname "$0")/../.." && pwd)"
# Converter path MSYS2 (/d/...) para Windows (D:/...) para Python
if [[ "$PROJECT" =~ ^/([a-zA-Z])/ ]]; then
    PROJECT_WIN="${BASH_REMATCH[1]^}:/${PROJECT:3}"
else
    PROJECT_WIN="$PROJECT"
fi
ROLE_FILE="$PROJECT_WIN/.claude/instance-role.local.json"
TICKETS_DIR="$PROJECT_WIN/.claude/tickets"

[ ! -f "$ROLE_FILE" ] && exit 0  # sem role = sem restrição

# Ler configuração de workspace e role
ROLE_INFO=$(python3 -c "
import json
try:
    with open('$ROLE_FILE') as f:
        d = json.load(f)
        ws = d.get('workspace_write', [])
        role = d.get('role', '')
        git_push = d.get('git_push', False)
        git_pull = d.get('git_pull', False)
        ws_str = '*' if '*' in ws else ','.join(ws)
        print(f'{role}|{ws_str}|{git_push}|{git_pull}')
except:
    print('||True|True')
" 2>/dev/null)

CURRENT_ROLE=$(echo "$ROLE_INFO" | cut -d'|' -f1)
WORKSPACE_WRITE=$(echo "$ROLE_INFO" | cut -d'|' -f2)
GIT_PUSH=$(echo "$ROLE_INFO" | cut -d'|' -f3)
GIT_PULL=$(echo "$ROLE_INFO" | cut -d'|' -f4)

# Se * = acesso total, permitir
if [ "$WORKSPACE_WRITE" = "*" ]; then
    exit 0
fi

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
DISPLAY_NAME=$(python3 -c "import json; d=json.load(open('$ROLE_FILE')); print(d.get('display_name', 'UNKNOWN'))" 2>/dev/null)

# Ler params JSON do stdin
read -r INPUT
FILE_PATH=""
IS_INSTALL=false
IS_GIT_PUSH=false
IS_GIT_PULL=false

# Extrair file_path baseado no tool
case "$TOOL_NAME" in
  Edit|Write)
    FILE_PATH=$(echo "$INPUT" | python3 -c "import json, sys; d=json.loads(sys.stdin.read()); print(d.get('file_path', ''))" 2>/dev/null)
    ;;
  Bash)
    COMMAND=$(echo "$INPUT" | python3 -c "import json, sys; d=json.loads(sys.stdin.read()); print(d.get('command', ''))" 2>/dev/null)

    # Checar se é comando de instalação
    if echo "$COMMAND" | grep -qE '^\s*(pip |npm |choco |winget |apt |apt-get |brew )'; then
      IS_INSTALL=true
    fi

    # Checar se é git push/pull
    if echo "$COMMAND" | grep -qE '^\s*git\s+push'; then
      IS_GIT_PUSH=true
    fi
    if echo "$COMMAND" | grep -qE '^\s*git\s+pull'; then
      IS_GIT_PULL=true
    fi

    # Para git push/pull — checar permissão do role + tickets
    if [ "$IS_GIT_PUSH" = true ] && [ "$GIT_PUSH" != "True" ]; then
      HAS_TICKET=$(python3 -c "
import json, glob, os
from datetime import datetime
tickets_dir = '$TICKETS_DIR'
role = '$CURRENT_ROLE'
if os.path.isdir(tickets_dir):
    for f in glob.glob(os.path.join(tickets_dir, 'TKT-*.json')):
        with open(f) as fh:
            t = json.load(fh)
            if t.get('status') != 'active': continue
            if t.get('granted_to') != role: continue
            exp = datetime.fromisoformat(t['expires_at'])
            if exp < datetime.now(): continue
            perms = t.get('permissions', [])
            if 'git:push' in perms or 'git:*' in perms:
                print('YES')
                exit()
print('NO')
" 2>/dev/null)

      if [ "$HAS_TICKET" != "YES" ]; then
        echo "BLOCKED — Role: $DISPLAY_NAME"
        echo "   git push nao permitido para este role."
        echo "   Solicite um ticket: /authorize $CURRENT_ROLE git:push <duracao>"
        exit 2
      fi
    fi

    if [ "$IS_GIT_PULL" = true ] && [ "$GIT_PULL" != "True" ]; then
      HAS_TICKET=$(python3 -c "
import json, glob, os
from datetime import datetime
tickets_dir = '$TICKETS_DIR'
role = '$CURRENT_ROLE'
if os.path.isdir(tickets_dir):
    for f in glob.glob(os.path.join(tickets_dir, 'TKT-*.json')):
        with open(f) as fh:
            t = json.load(fh)
            if t.get('status') != 'active': continue
            if t.get('granted_to') != role: continue
            exp = datetime.fromisoformat(t['expires_at'])
            if exp < datetime.now(): continue
            perms = t.get('permissions', [])
            if 'git:pull' in perms or 'git:*' in perms:
                print('YES')
                exit()
print('NO')
" 2>/dev/null)

      if [ "$HAS_TICKET" != "YES" ]; then
        echo "BLOCKED — Role: $DISPLAY_NAME"
        echo "   git pull nao permitido para este role."
        echo "   Solicite um ticket: /authorize $CURRENT_ROLE git:pull <duracao>"
        exit 2
      fi
    fi

    # Para comandos de instalação — checar ticket bash:install
    if [ "$IS_INSTALL" = true ]; then
      HAS_TICKET=$(python3 -c "
import json, glob, os
from datetime import datetime
tickets_dir = '$TICKETS_DIR'
role = '$CURRENT_ROLE'
if os.path.isdir(tickets_dir):
    for f in glob.glob(os.path.join(tickets_dir, 'TKT-*.json')):
        with open(f) as fh:
            t = json.load(fh)
            if t.get('status') != 'active': continue
            if t.get('granted_to') != role: continue
            exp = datetime.fromisoformat(t['expires_at'])
            if exp < datetime.now(): continue
            perms = t.get('permissions', [])
            if 'bash:install' in perms or 'bash:*' in perms:
                print('YES')
                exit()
print('NO')
" 2>/dev/null)

      if [ "$HAS_TICKET" != "YES" ]; then
        echo "BLOCKED — Role: $DISPLAY_NAME"
        echo "   Comandos de instalacao nao permitidos sem ticket."
        echo "   Solicite um ticket: /authorize $CURRENT_ROLE bash:install <duracao>"
        exit 2
      fi
      exit 0  # Tem ticket de install, permitir
    fi

    # Para rm/mv — extrair path alvo
    COMMAND_SHORT=$(echo "$COMMAND" | head -c 20)
    if [[ ! $COMMAND_SHORT =~ ^(rm|mv) ]]; then
      exit 0  # Não bloqueia outros comandos bash
    fi
    FILE_PATH=$(echo "$INPUT" | python3 -c "import json, sys; d=json.loads(sys.stdin.read()); cmd=d.get('command', ''); print(cmd.split()[-1] if cmd else '')" 2>/dev/null)
    ;;
esac

[ -z "$FILE_PATH" ] && exit 0  # sem file_path, permitir

# Normalizar path (converter para relativo)
FILE_PATH="${FILE_PATH#./}"
FILE_PATH="${FILE_PATH%/}"
# Remover prefixo absoluto do projeto se presente
FILE_PATH="${FILE_PATH#$PROJECT/}"
FILE_PATH="${FILE_PATH#$PROJECT_WIN/}"

# Checar se FILE_PATH está em WORKSPACE_WRITE
ALLOWED=false
for WS_PATH in ${WORKSPACE_WRITE//,/ }; do
  WS_PATH="${WS_PATH%/}"
  if [[ "$FILE_PATH" == "$WS_PATH" ]] || [[ "$FILE_PATH" == "$WS_PATH"/* ]]; then
    ALLOWED=true
    break
  fi
done

# Se não permitido pelo workspace, checar tickets de workspace extra
if [ "$ALLOWED" = false ]; then
  TICKET_GRANT=$(python3 -c "
import json, glob, os
from datetime import datetime
tickets_dir = '$TICKETS_DIR'
role = '$CURRENT_ROLE'
file_path = '$FILE_PATH'
if os.path.isdir(tickets_dir):
    for f in glob.glob(os.path.join(tickets_dir, 'TKT-*.json')):
        with open(f) as fh:
            t = json.load(fh)
            if t.get('status') != 'active': continue
            if t.get('granted_to') != role: continue
            exp = datetime.fromisoformat(t['expires_at'])
            if exp < datetime.now(): continue
            for perm in t.get('permissions', []):
                if perm.startswith('workspace:'):
                    ws = perm[10:].rstrip('/')
                    if file_path == ws or file_path.startswith(ws + '/'):
                        print('YES')
                        exit()
print('NO')
" 2>/dev/null)

  if [ "$TICKET_GRANT" = "YES" ]; then
    ALLOWED=true
  fi
fi

if [ "$ALLOWED" = false ]; then
  echo "BLOCKED — Role: $DISPLAY_NAME"
  echo "   Arquivo: $FILE_PATH"
  echo "   Workspace permitido: $WORKSPACE_WRITE"
  echo "   Solicite um ticket: /authorize $CURRENT_ROLE workspace:$(dirname $FILE_PATH)/ <duracao>"
  echo ""
  exit 2  # Bloqueado
fi

exit 0  # Permitido
