#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
BIN_DIR="$HOME/bin"
ENV_FILE="$CLAUDE_DIR/.env"

mkdir -p "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands" "$BIN_DIR"

install_file() {
  src="$1"
  dest="$2"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  printf '[✓] installed %s\n' "$dest"
}

write_env_if_missing() {
  if [ -f "$ENV_FILE" ]; then
    printf '[✓] env exists %s\n' "$ENV_FILE"
    return
  fi
  cp "$KIT_DIR/templates/env.example" "$ENV_FILE"
  if command -v codex >/dev/null 2>&1; then
    sed -i.bak "s|^GPT_CLI_PATH=.*|GPT_CLI_PATH=$(command -v codex)|" "$ENV_FILE"
  fi
  if command -v opencode >/dev/null 2>&1; then
    sed -i.bak "s|^OPENCODE_CLI_PATH=.*|OPENCODE_CLI_PATH=$(command -v opencode)|" "$ENV_FILE"
    sed -i.bak "s|^DEEPSEEK_CLI_PATH=.*|DEEPSEEK_CLI_PATH=$(command -v opencode)|" "$ENV_FILE"
  fi
  if command -v agy >/dev/null 2>&1; then
    sed -i.bak "s|^GEMINI_CLI_PATH=.*|GEMINI_CLI_PATH=$(command -v agy)|" "$ENV_FILE"
  fi
  rm -f "$ENV_FILE.bak"
  printf '[✓] env created %s\n' "$ENV_FILE"
}

ln -sf "$KIT_DIR/scripts/cship" "$BIN_DIR/cship"
printf '[✓] linked %s\n' "$BIN_DIR/cship"

install_file "$KIT_DIR/agents/coder-opencode.md" "$CLAUDE_DIR/agents/coder-opencode.md"
install_file "$KIT_DIR/agents/reviewer-gpt.md" "$CLAUDE_DIR/agents/reviewer-gpt.md"
install_file "$KIT_DIR/agents/frontend-gemini.md" "$CLAUDE_DIR/agents/frontend-gemini.md"
install_file "$KIT_DIR/commands/ship.md" "$CLAUDE_DIR/commands/ship.md"
write_env_if_missing

"$KIT_DIR/scripts/doctor.sh"
