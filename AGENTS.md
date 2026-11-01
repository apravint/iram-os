# AGENTS.md - Developer & Agent Guide for IRAM OS

## Project Overview
**IRAM OS** is an autonomous, agentic Wayland distribution built upon Ubuntu Linux and Hyprland. It integrates local AI models (Ollama, fastmcp), dynamic theme synchronization across 55 palettes, zero-restart configuration reloading, and voice/vision capabilities.

---

## Directory Architecture

```
iram-os/
├── bin/              # System CLI utilities, agent dispatchers, hardware controllers
├── config/           # Desktop configuration and systemd user units (config/systemd/user)
├── themes/           # 55 curated themes with palettes, wallpapers, and templates
├── applications/     # .desktop application launchers and hicolor icons (51 apps)
├── build/            # ISO build automation (build-iso.sh) and Debian packager (package-deb.sh)
├── system/           # Sudoers configuration, system-wide profiles, and Wayland session
├── iram_voice/       # Speech synthesis engine and local edge-tts bridges
├── migrations/       # Non-destructive schema and config migrations
├── packages/         # Package manifests shared by install.sh, the ISO and the .deb
├── tests/            # tests/run.sh: needs no root, compositor or network
└── install.sh        # Modular system installer with rollback backups & --dry-run mode
```

---

## Core Development Commands

### 1. Verification & Dry-Run
Always test the installer in simulation mode before running on live hardware:
```bash
./install.sh --dry-run
./install.sh --dry-run core
./install.sh --help
```

### 2. Linting & Shell Safety
All shell scripts must pass ShellCheck without errors or critical warnings:
```bash
shellcheck install.sh build/*.sh bin/iram*
```

### 3. Packaging Debian Release
```bash
./build/package-deb.sh
```

### 4. Building Bootable Live ISO (Requires Root / Ubuntu Host)
```bash
sudo ./build/build-iso.sh
```

---

## Coding Standards & Conventions

1. **Strict Shell Safety**:
   - Every bash script must begin with `set -euo pipefail`.
   - Never use `|| true` on critical command chains (package installation, user creation, checksum calculation).
   - Differentiate fatal errors from non-fatal notifications using explicit error logging.

2. **Clean Case Patterns**:
   - Avoid redundant wildcards in case arms (e.g., use `region)` or `*)`, never `region|*)`).

3. **Subshell Exit Code Preservation**:
   - Split local variable declarations from command substitutions to prevent masking exit codes (ShellCheck SC2155):
     ```bash
     # DO NOT:
     local output=$(command)
     # DO:
     local output
     output=$(command)
     ```

4. **Security & Permissions**:
   - Sudoers rules in `system/sudoers.d/` must enforce strict input validation (e.g. 6-hex-character color hex values only).
   - Live ISO user (`iram:iram`) must be prompted for password initialization on target installation.

5. **Backup & Rollback Integrity**:
   - Changes to user configuration must respect the timestamped backup mechanism (`~/.config/iram/backups/`).
