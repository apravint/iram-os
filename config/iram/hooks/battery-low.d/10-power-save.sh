#!/usr/bin/env bash
# ==============================================================================
# Lifecycle Hook: battery-low.d/10-power-save.sh
# Engages power saving features when battery dips below critical threshold
# ==============================================================================
set -euo pipefail

PERCENT="${1:-15}"

# 1. Notify user
if command -v notify-send >/dev/null 2>&1; then
    notify-send -u critical -a "IRAM Power" "⚡ Low Battery (${PERCENT}%)" "IRAM OS engaged power-saver mode." 2>/dev/null || true
fi

# 2. Dim display brightness if brightnessctl is present
if command -v brightnessctl >/dev/null 2>&1; then
    brightnessctl set 30% 2>/dev/null || true
fi

# 3. Disable heavy Hyprland blur and animations temporarily to conserve battery
if command -v hyprctl >/dev/null 2>&1; then
    hyprctl keyword decoration:blur:enabled false >/dev/null 2>&1 || true
    hyprctl keyword animations:enabled false >/dev/null 2>&1 || true
fi
