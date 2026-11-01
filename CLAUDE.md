# CLAUDE.md - Assistant Guidelines for IRAM OS

This repository contains the source code, packaging, and configuration for **IRAM OS**, an autonomous AI-native Wayland distribution.

## Key Build & Test Commands
- **Dry-run installer**: `./install.sh --dry-run`
- **Shellcheck lint**: `shellcheck install.sh build/*.sh bin/iram*`
- **Build DEB package**: `./build/package-deb.sh`
- **Build ISO image**: `sudo ./build/build-iso.sh` (requires debootstrap, squashfs-tools, xorriso)

## Architecture & Code Guidelines
- **Bash Scripts**: Use `set -euo pipefail`. Avoid blind `|| true` on installation and package deployment steps.
- **Backups**: Installer must create timestamped backups in `~/.config/iram/backups/` before modifying dotfiles.
- **Themes**: All 43 themes live in `themes/` and use zero-restart dynamic template updates via `bin/iram-theme-switch`.
- **Security**: Do not hardcode secrets or credentials. Sudoers permissions in `system/sudoers.d/` must remain tightly restricted.
- **Reference**: Detailed agent guidelines and conventions are documented in `AGENTS.md`.
