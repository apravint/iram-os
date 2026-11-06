#!/usr/bin/env bash
# ==============================================================================
# Lifecycle Hook: post-update.d/10-run-migrations.sh
# Automatically runs all pending migrations after an IRAM OS update
# ==============================================================================
set -euo pipefail

if command -v iram-migrate >/dev/null 2>&1; then
    # install.sh has already run them; this catches any added by a later hook.
    iram-migrate run
fi
