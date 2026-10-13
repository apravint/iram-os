#!/usr/bin/env bash
# ==============================================================================
# Lifecycle Hook: post-update.d/10-run-migrations.sh
# Automatically runs all pending migrations after an IRAM OS update
# ==============================================================================
set -euo pipefail

if command -v iram-migrate >/dev/null 2>&1; then
    iram-migrate run || true
fi
