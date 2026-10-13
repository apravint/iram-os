#!/usr/bin/env bash
# ==============================================================================
# Migration: 1785000000_init_lifecycle_and_agent_dirs.sh
# Sets up standard directory hierarchy for IRAM lifecycle hooks and agent telemetry
# ==============================================================================
set -euo pipefail

echo "Initializing lifecycle hooks and agent state hierarchy..."

# 1. User hooks directories
mkdir -p "$HOME/.config/iram/hooks/theme-set.d"
mkdir -p "$HOME/.config/iram/hooks/battery-low.d"
mkdir -p "$HOME/.config/iram/hooks/post-boot.d"
mkdir -p "$HOME/.config/iram/hooks/post-update.d"
mkdir -p "$HOME/.config/iram/hooks/font-set.d"

# 2. System hooks directories
mkdir -p "$HOME/iram-os/config/iram/hooks/theme-set.d"
mkdir -p "$HOME/iram-os/config/iram/hooks/battery-low.d"
mkdir -p "$HOME/iram-os/config/iram/hooks/post-boot.d"
mkdir -p "$HOME/iram-os/config/iram/hooks/post-update.d"
mkdir -p "$HOME/iram-os/config/iram/hooks/font-set.d"

# 3. Agent usage state directory
mkdir -p "$HOME/.local/state/iram/agents/usage"
mkdir -p "$HOME/.local/state/iram/agents/accounts"

# 4. Standard developer workspace directory
mkdir -p "$HOME/Work"

echo "Directories initialized successfully."
