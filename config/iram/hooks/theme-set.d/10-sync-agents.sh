#!/usr/bin/env bash
# ==============================================================================
# Lifecycle Hook: theme-set.d/10-sync-agents.sh
# Synchronizes active IRAM theme to AI coding assistants (Claude, OpenCode, Agy)
# ==============================================================================
set -euo pipefail

THEME_NAME="${1:-$(cat "$HOME/.local/state/iram/current/theme.name" 2>/dev/null || echo "Tokyo Storm")}"

# 1. Sync Claude Code theme setting if config exists
CLAUDE_CONFIG="$HOME/.claude/settings.json"
if [ -d "$HOME/.claude" ]; then
    mkdir -p "$HOME/.claude"
    if [ ! -f "$CLAUDE_CONFIG" ]; then
        echo '{}' > "$CLAUDE_CONFIG"
    fi
    # Map to light/dark
    case "$THEME_NAME" in
        *Light*|*White*|*Latte*)
            claude_theme="light"
            ;;
        *)
            claude_theme="dark"
            ;;
    esac
    if command -v jq >/dev/null 2>&1; then
        tmp=$(mktemp)
        jq --arg t "$claude_theme" '.theme = $t' "$CLAUDE_CONFIG" > "$tmp" && mv "$tmp" "$CLAUDE_CONFIG" 2>/dev/null || rm -f "$tmp"
    fi
fi

# 2. Record active theme for agy / antigravity sidecar
mkdir -p "$HOME/.local/state/iram/current"
echo "$THEME_NAME" > "$HOME/.local/state/iram/current/agent-theme.name"
