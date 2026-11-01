#!/usr/bin/env bash
# ==============================================================================
# Migration: 1785002000_session_target_and_unit_cleanup.sh
# Moves desktop daemons to hyprland-session.target. Removes units that no longer
# ship (one formed an ordering cycle with timers.target), and turns off services
# that are now opt-in: the unauthenticated MCP SSE port and the file organizer.
# ==============================================================================
set -euo pipefail

UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

for unit in iram-mcp-server.service iram-mcp.service iram-organizer.timer iram-dual-wifi-keepalive.service iram-health-agent.timer; do
    systemctl --user disable --now "$unit" >/dev/null 2>&1 || true
done
rm -f "$UNIT_DIR/iram-mcp.service" "$UNIT_DIR/iram-health-agent.service" "$UNIT_DIR/iram-health-agent.timer"

systemctl --user daemon-reload >/dev/null 2>&1 || true

# mako and swaync both claim org.freedesktop.Notifications; only swaync remains in use.
pkill -x mako >/dev/null 2>&1 || true
