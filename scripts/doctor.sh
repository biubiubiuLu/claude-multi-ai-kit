#!/usr/bin/env bash
set -u

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${CLAUDE_MULTI_AI_ENV:-$HOME/.claude/.env}"
STATUS=0

ok() {
  printf '[✓] %s\n' "$1"
}

warn() {
  printf '[!] %s\n' "$1"
}

fail() {
  printf '[x] %s\n' "$1"
  STATUS=1
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
    ok "Env file: $ENV_FILE"
  else
    warn "Env file missing: $ENV_FILE"
  fi
}

check_cli() {
  label="$1"
  configured="$2"
  fallback="$3"
  path="$configured"
  if [ -z "$path" ]; then
    path="$(command -v "$fallback" 2>/dev/null || true)"
  fi
  if [ -n "$path" ] && [ -x "$path" ]; then
    ok "$label CLI: $path"
  else
    fail "$label CLI not found: set ${label}_CLI_PATH or install $fallback"
  fi
}

check_file() {
  if [ -f "$1" ]; then
    ok "$2: $1"
  else
    fail "$2 missing: $1"
  fi
}

load_env
check_file "$KIT_DIR/scripts/ship.py" "ship.py"
check_file "$KIT_DIR/scripts/cship" "cship"
check_cli GPT "${GPT_CLI_PATH:-}" codex
check_cli OPENCODE "${OPENCODE_CLI_PATH:-${DEEPSEEK_CLI_PATH:-}}" opencode
check_cli GEMINI "${GEMINI_CLI_PATH:-}" agy

if [ "${GPT_MODEL+x}" = x ]; then
  ok "GPT_MODEL=${GPT_MODEL:-<default>}"
else
  warn "GPT_MODEL not set; Codex default model will be used"
fi

ok "OPENCODE_MODEL=${OPENCODE_MODEL:-${DEEPSEEK_MODEL:-deepseek/deepseek-chat}}"
ok "Kit directory: $KIT_DIR"

exit "$STATUS"
