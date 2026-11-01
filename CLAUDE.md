# CLAUDE.md - Assistant Guidelines for IRAM OS

This repository contains the source code, packaging, and configuration for **IRAM OS**, an autonomous AI-native Wayland distribution.

## Key Build & Test Commands
- **Test suite (no root, no compositor)**: `tests/run.sh`
- **Dry-run installer**: `./install.sh --dry-run`
- **Shellcheck lint**: `shellcheck install.sh build/*.sh bin/iram*`
- **Build DEB packages**: `./build/package-deb.sh` (signed repo: `build/publish-apt-repo.sh`)
- **Build ISO image**: `sudo ./build/build-iso.sh` (requires debootstrap, squashfs-tools, xorriso)

## Architecture & Code Guidelines
- **Bash Scripts**: Use `set -euo pipefail`. Avoid blind `|| true` on installation and package deployment steps.
- **Backups**: Installer must create timestamped backups in `~/.config/iram/backups/` before modifying dotfiles.
- **Themes**: All themes live in `themes/` and use zero-restart dynamic template updates via `bin/iram-theme-switch`.
- **Security**: Do not hardcode secrets or credentials. Sudoers permissions in `system/sudoers.d/` must remain tightly restricted.
- **Agent Execution**: Model output and web requests go through `bin/iram_policy.py`. Never run them with `shell=True`, and never expose a Hyprland `exec` dispatcher.
- **Packages**: Add runtime dependencies to `packages/desktop.list`; the installer, ISO and `.deb` all read it.
- **Session Units**: Daemons are units under `hyprland-session.target`. Do not also start them with `exec-once`.
- **Reference**: Detailed agent guidelines and conventions are documented in `AGENTS.md`.
