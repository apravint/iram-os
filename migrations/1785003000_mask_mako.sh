#!/usr/bin/env bash
# ==============================================================================
# Migration: 1785003000_mask_mako.sh
# mako.service and swaync.service both claim org.freedesktop.Notifications, and
# systemd refuses to load whichever comes second. On a machine that still has
# mako-notifier installed, that could leave SwayNC, the daemon IRAM uses, unloaded.
# ==============================================================================
set -euo pipefail

systemctl --user disable --now mako.service >/dev/null 2>&1 || true
systemctl --user mask mako.service >/dev/null 2>&1 || true
systemctl --user daemon-reload >/dev/null 2>&1 || true
