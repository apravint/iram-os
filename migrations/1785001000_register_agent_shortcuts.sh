#!/usr/bin/env bash
# ==============================================================================
# Migration: 1785001000_register_agent_shortcuts.sh
# Verifies agent router 'a' and default agent configuration
# ==============================================================================
set -euo pipefail

echo "Registering agent shortcuts and default agent config..."

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/iram"
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/default-agent" ]; then
    echo "agy" > "$CONFIG_DIR/default-agent"
fi

if [ -f "$HOME/.local/bin/a" ]; then
    chmod +x "$HOME/.local/bin/a"
fi

echo "Agent configuration verified."
