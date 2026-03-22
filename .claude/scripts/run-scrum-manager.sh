#!/bin/bash
# Scrum Manager — Hook automático para fim de tarefas
#
# MODO: Background (automático)
# ACIONADOR: Hook Stop ao final de sessão (após code completion)
# COMPORTAMENTO: Propõe atualizações de ROADMAP para o usuário via prompt
#
# Roda apenas quando há código novo desde a última execução.
# Proteção anti-recursão: sub-agentes não disparam este hook.
# Proteção de role: só dispara em eddie-morra ou sem role.

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO: Substitua as variáveis abaixo para o seu projeto
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_SLUG="speedosper"            # slug do projeto (ex: ahtleta, myapp) — usado em vars de ambiente e lockfile
PROJECT="D:DocumentosTiprojetospp_speedosper"                 # caminho absoluto da raiz do projeto
CODE_PATHS=("D:DocumentosTiprojetospp_speedospersrc" "D:DocumentosTiprojetospp_speedospersrc")  # paths de código a monitorar (ex: "apps/backend/src" "apps/frontend/lib")
# ─────────────────────────────────────────────────────────────────────────────

# Proteção anti-recursão: sub-agentes não disparam este hook
AGENT_MODE_VAR="${PROJECT_SLUG^^}_AGENT_MODE"  # transforma slug em UPPERCASE
if [ -n "${!AGENT_MODE_VAR}" ]; then
  exit 0
fi

# Proteção de role: SM só dispara em eddie-morra ou sem role definido
ROLE_FILE="$PROJECT/.claude/instance-role.local.json"
if [ -f "$ROLE_FILE" ]; then
  CURRENT_ROLE=$(python3 -c "import json; d=json.load(open('$ROLE_FILE')); print(d.get('role', ''))" 2>/dev/null)
  if [ -n "$CURRENT_ROLE" ] && [ "$CURRENT_ROLE" != "eddie-morra" ]; then
    exit 0  # Não é eddie-morra, não disparar SM
  fi
fi

# ── Filtro inteligente ────────────────────────────────────────────────────────
# Só roda se houve código novo desde o último commit do Scrum Manager.

# Timestamp do último commit feito pelo Scrum Manager
LAST_SM_COMMIT=$(git -C "$PROJECT" log --format="%ct" \
  --grep="Scrum Manager" -1 2>/dev/null || echo 0)

# Timestamp do último commit que tocou código
LAST_CODE_COMMIT=$(git -C "$PROJECT" log --format="%ct" \
  -- "${CODE_PATHS[@]}" -1 2>/dev/null || echo 0)

# Mudanças de código não commitadas
UNCOMMITTED=$(git -C "$PROJECT" diff --name-only HEAD -- \
  "${CODE_PATHS[@]}" 2>/dev/null)

# Se não houve código novo (commitado ou não) desde o último SM → sai
if [ "$LAST_CODE_COMMIT" -le "$LAST_SM_COMMIT" ] && [ -z "$UNCOMMITTED" ]; then
  exit 0
fi

# ── Lock para evitar execuções concorrentes ───────────────────────────────────
LOCKFILE="/tmp/${PROJECT_SLUG}-scrum-manager.lock"

(
  flock -n 200 || exit 0

  PROMPT=$(cat "$PROJECT/.claude/agents/scrum-manager.md")

  export "${AGENT_MODE_VAR}=scrum-manager"
  claude --print \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
    -p "$PROMPT" \
    2>/dev/null

) 200>"$LOCKFILE"
