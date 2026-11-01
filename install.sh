#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Automated Installer
# Experience authentic IRAM OS (Hyprland + Themes + Waybar)
# https://github.com/apravint/iram-os
# ==============================================================================
set -euo pipefail
trap 'echo -e "\033[0;31m[ERROR] Iram installation failed at line $LINENO. Exiting gracefully.\033[0m"; exit 1' ERR

# BASH_SOURCE is empty when piped into bash (curl | bash), which set -u would reject.
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
if [ ! -d "$REPO_DIR/bin" ] || [ ! -d "$REPO_DIR/system" ]; then
    TMP_CLONE=$(mktemp -d)
    trap 'rm -rf "$TMP_CLONE"' EXIT
    git clone --depth 1 https://github.com/apravint/iram-os.git "$TMP_CLONE"
    REPO_DIR="$TMP_CLONE"
fi

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse command line flags & target profile
DRY_RUN=false
INSTALL_TARGET="all"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--dry-run] [all|core|ai|craft]"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n    Simulate installation without making system changes"
            echo "  --help, -h       Show this help message"
            echo "  all              Full installation (Desktop + AI agent stack + Creative tools)"
            echo "  core             Minimal desktop environment (Hyprland + Themes + Waybar)"
            echo "  ai               Desktop foundation + Ollama & MCP agent stack"
            echo "  craft            Desktop foundation + Creative tools & Storytold craft"
            exit 0
            ;;
        core|ai|craft|all)
            INSTALL_TARGET="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./install.sh [--dry-run] [all|core|ai|craft]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}            IRAM OS - Modular Distribution Setup${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Target Profile: ${GREEN}${INSTALL_TARGET^^}${NC} (options: core | ai | craft | all)"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode:           ${RED}DRY-RUN (Simulation only, no files modified)${NC}"
fi
echo -e "${BLUE}------------------------------------------------------${NC}"

# Check for sudo/root in real mode
if [ "$DRY_RUN" = false ]; then
    if ! sudo -v &>/dev/null; then
        echo -e "${RED}Error: sudo access is required to install system packages.${NC}"
        exit 1
    fi
fi

warn() { echo -e "${YELLOW}Notice: $*${NC}" >&2; }

read_package_list() {
    grep -vE '^\s*(#|$)' "$REPO_DIR/packages/$1"
}

# ------------------------------------------------------------------------------
# 1. Desktop foundation & system dependencies
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/6] Installing desktop foundation & system dependencies...${NC}"
mapfile -t DESKTOP_PACKAGES < <(read_package_list desktop.list)
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would update apt repositories and install ${#DESKTOP_PACKAGES[@]} packages:${NC}"
    echo "  ${DESKTOP_PACKAGES[*]}"
else
    sudo apt-get update
    MISSING_PACKAGES=()
    for pkg in "${DESKTOP_PACKAGES[@]}"; do
        apt-cache show "$pkg" >/dev/null 2>&1 || MISSING_PACKAGES+=("$pkg")
    done
    if [ "${#MISSING_PACKAGES[@]}" -gt 0 ]; then
        echo -e "${RED}Error: not available from your apt sources: ${MISSING_PACKAGES[*]}${NC}"
        echo "IRAM OS targets Ubuntu 26.04 LTS or newer with the universe component enabled."
        exit 1
    fi
    sudo apt-get install -y "${DESKTOP_PACKAGES[@]}"
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would install the pinned JetBrainsMono Nerd Font${NC}"
else
    sudo bash "$REPO_DIR/bin/iram-install-nerd-font" || warn "Nerd Font not installed; Waybar icons will be missing. Retry: sudo iram-install-nerd-font"
fi

# Starship prompt: optional, from apt only. The prompt is not worth a curl | sh.
if [ "$DRY_RUN" = false ] && ! command -v starship >/dev/null 2>&1; then
    if apt-cache show starship >/dev/null 2>&1; then
        sudo apt-get install -y starship || warn "Starship prompt not installed."
    fi
fi

# Install Ollama & the agent stack (if profile is 'all' or 'ai')
if [ "$INSTALL_TARGET" = "all" ] || [ "$INSTALL_TARGET" = "ai" ]; then
    AI_VENV="$HOME/.local/share/iram/ai-venv"
    mapfile -t AI_PYTHON_PACKAGES < <(read_package_list ai-python.list)
    if [ "$DRY_RUN" = true ]; then
        command -v ollama >/dev/null 2>&1 || echo -e "${BLUE}[DRY-RUN] Would download and run https://ollama.com/install.sh${NC}"
        echo -e "${BLUE}[DRY-RUN] Would install into $AI_VENV: ${AI_PYTHON_PACKAGES[*]}${NC}"
    else
        if ! command -v ollama >/dev/null 2>&1; then
            echo "Installing Ollama Local LLM Engine..."
            OLLAMA_TMP=$(mktemp)
            if curl -fsSL https://ollama.com/install.sh -o "$OLLAMA_TMP"; then
                sh "$OLLAMA_TMP" || warn "The Ollama installer failed. Retry later with: iram ai-setup"
            else
                warn "Could not download the Ollama installer. Retry later with: iram ai-setup"
            fi
            rm -f "$OLLAMA_TMP"
        fi

        # A venv, not --break-system-packages: it cannot shadow apt's Python libraries
        # for other programs' dependency resolution, and removing it is one rm -rf.
        echo "Installing the agent stack into $AI_VENV..."
        python3 -m venv --system-site-packages "$AI_VENV"
        AI_FAILED=()
        AI_LOG="$(mktemp -t iram-ai-pip-XXXXXX.log)"
        for pkg in "${AI_PYTHON_PACKAGES[@]}"; do
            "$AI_VENV/bin/pip" install --quiet "$pkg" >> "$AI_LOG" 2>&1 || AI_FAILED+=("$pkg")
        done
        if [ "${#AI_FAILED[@]}" -gt 0 ]; then
            warn "These Python packages failed (details: $AI_LOG): ${AI_FAILED[*]}"
        else
            rm -f "$AI_LOG"
        fi
        # IRAM's tools run under /usr/bin/python3, so expose the venv through a .pth file.
        USER_SITE="$(python3 -m site --user-site)"
        mkdir -p "$USER_SITE"
        "$AI_VENV/bin/python" -c 'import site; print(site.getsitepackages()[0])' > "$USER_SITE/iram-ai.pth"
    fi
    if command -v npm >/dev/null 2>&1; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${BLUE}[DRY-RUN] Would run npm install -g repomix${NC}"
        else
            sudo npm install -g repomix >/dev/null || warn "Optional repomix package not installed."
        fi
    fi
else
    echo "Skipping AI daemon dependencies (iram-desktop-core mode active)."
fi

# ------------------------------------------------------------------------------
# 2. Deploy IRAM OS core system files & theme suite
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[2/6] Installing IRAM OS core system files & theme suite...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would deploy IRAM OS system files to /usr/share/iram${NC}"
    echo -e "${BLUE}[DRY-RUN] Would copy binaries to /usr/local/bin and link them from /usr/bin${NC}"
else
    sudo mkdir -p /usr/share/iram
    echo "Deploying IRAM OS core from $REPO_DIR..."
    for component in bin config default themes system migrations mcp assets applications packages; do
        if [ -d "$REPO_DIR/$component" ]; then
            sudo rm -rf "/usr/share/iram/$component"
            sudo cp -a --no-preserve=ownership "$REPO_DIR/$component" /usr/share/iram/
        fi
    done

    echo "Linking IRAM CLI binaries to /usr/local/bin and /usr/bin..."
    # Root must own these, whatever a previous install left: sudoers runs one of them as
    # root without a password, so a user-owned copy would be a privilege escalation.
    sudo chmod -R go-w /usr/share/iram
    sudo chown -R root:root /usr/share/iram
    sudo cp -a --no-preserve=ownership "$REPO_DIR/bin/"* /usr/local/bin/
    for b in "$REPO_DIR"/bin/*; do
        bname="$(basename "$b")"
        sudo chown -h root:root "/usr/local/bin/$bname"
        [ -L "$b" ] && continue
        sudo chmod 0755 "/usr/local/bin/$bname"
        case "$bname" in
            iram*|craft*|hyprland-start) sudo ln -sf "/usr/local/bin/$bname" "/usr/bin/$bname" ;;
        esac
    done
    sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/local/bin/a
    sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/bin/a

    # A bad sudoers file can lock everyone out of sudo, so validate before installing.
    SUDOERS_SRC="$REPO_DIR/system/sudoers.d/iram-theme-browser"
    if ! sudo visudo -cf "$SUDOERS_SRC" >/dev/null; then
        echo -e "${RED}Error: $SUDOERS_SRC failed visudo validation.${NC}"
        exit 1
    fi
    sudo install -m 0440 -o root -g root "$SUDOERS_SRC" /etc/sudoers.d/iram-theme-browser
fi

# ------------------------------------------------------------------------------
# 3. Configure system environment & session entries
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[3/6] Configuring system environment & session entries...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would configure /etc/iram.conf, /etc/profile.d/iram.sh, and Wayland session${NC}"
else
    sudo cp "$REPO_DIR/system/iram.conf" /etc/iram.conf
    sudo cp "$REPO_DIR/system/iram.sh" /etc/profile.d/iram.sh
    if ! grep -q "IRAM_PATH" /etc/environment 2>/dev/null; then
        echo "IRAM_PATH=/usr/share/iram" | sudo tee -a /etc/environment >/dev/null
    fi
    sudo mkdir -p /usr/share/wayland-sessions
    sudo cp "$REPO_DIR/system/iram.desktop" /usr/share/wayland-sessions/iram.desktop

    # Install kernel & networking sysctl optimizations (TCP BBR & interactive tuning)
    sudo cp "$REPO_DIR/system/sysctl.d/99-iram-performance.conf" /etc/sysctl.d/99-iram-performance.conf
    sudo cp "$REPO_DIR/system/modules-load.d/bbr.conf" /etc/modules-load.d/bbr.conf
    sudo modprobe tcp_bbr 2>/dev/null || warn "tcp_bbr module not loaded; BBR applies after reboot."
    # sysctl --system returns non-zero for any unrelated bad key on the machine.
    sudo sysctl -q -p /etc/sysctl.d/99-iram-performance.conf >/dev/null || warn "Some sysctl values were not applied."
fi

# ------------------------------------------------------------------------------
# 4. User dotfiles, timestamped backups & scripts
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/6] Installing user dotfiles & scripts (with timestamped backups)...${NC}"
if [ "$DRY_RUN" = true ]; then
    bash "$REPO_DIR/bin/iram-user-setup" --source "$REPO_DIR" --with-bin --dry-run
else
    bash "$REPO_DIR/bin/iram-user-setup" --source "$REPO_DIR" --with-bin
fi

# ------------------------------------------------------------------------------
# 5. Initialize default theme, migrations & services
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[5/6] Initializing default Iram theme, migrations & services...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would run migrations, apply default theme, and enable systemd user units${NC}"
else
    export IRAM_PATH=/usr/share/iram
    export PATH="$HOME/.local/bin:$PATH"

    echo "Running IRAM OS migrations..."
    iram-migrate run || warn "A migration failed. Inspect with: iram migrate status"

    # An upgrade keeps the user's theme; only a machine without one gets the default.
    if [ ! -f "$HOME/.local/state/iram/current/theme.name" ]; then
        iram theme set "Cyberpunk Neon" || iram theme set "Tokyo Storm" || warn "Could not apply a default theme."
    else
        iram-theme-sync-all || warn "Theme sync failed."
    fi

    # Opt-in only, and deliberately absent here: iram-organizer.timer (moves files in
    # ~/Downloads), iram-dual-wifi-keepalive (specific hardware), iram-mcp-server (no auth).
    CORE_UNITS=(
        waybar.service swaybg.service swaync.service hypridle.service
        iram-cliphist.service iram-cliphist-image.service iram-polkit-agent.service
        iram-watchdog.service iram-battery.timer iram-healthd.timer iram-security.timer
    )
    AI_UNITS=(iram-agentd.socket iram-hub.service iram-nexus.service)
    ENABLE_UNITS=("${CORE_UNITS[@]}")
    if [ "$INSTALL_TARGET" = "all" ] || [ "$INSTALL_TARGET" = "ai" ]; then
        ENABLE_UNITS+=("${AI_UNITS[@]}")
    fi
    if systemctl --user daemon-reload 2>/dev/null; then
        for unit in "${ENABLE_UNITS[@]}"; do
            systemctl --user enable "$unit" >/dev/null 2>&1 || warn "Could not enable $unit"
        done
        # Inside a running session, apply now. Otherwise they start at next login.
        if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
            hyprctl reload >/dev/null || warn "hyprctl reload failed."
            iram-session-bootstrap || warn "Could not restart the session services."
        fi
    else
        warn "No user systemd instance here; units were not enabled. Re-run install.sh from a login session."
    fi
fi

# ------------------------------------------------------------------------------
# 6. Verification
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[6/6] Verifying Hyprland configuration...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Verification complete (Simulation mode).${NC}"
else
    HYPR_CONFIG="$HOME/.config/hypr/hyprland.conf"
    if command -v Hyprland >/dev/null 2>&1; then
        if Hyprland --verify-config --config "$HYPR_CONFIG" >/dev/null 2>&1; then
            echo -e "${GREEN}Hyprland configuration verified: OK!${NC}"
        else
            warn "Hyprland reports problems in $HYPR_CONFIG. Check with: Hyprland --verify-config --config $HYPR_CONFIG"
        fi
    else
        warn "Hyprland binary not found; configuration not verified."
    fi
fi

echo -e "\n${BLUE}======================================================${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${GREEN}🎉 Dry-Run Simulation Finished! No files modified.${NC}"
else
    echo -e "${GREEN}🎉 Installation Complete!${NC}"
fi
echo -e "${BLUE}======================================================${NC}"
echo -e "To start using Iram:"
echo -e "1. Log out of your current session."
echo -e "2. In the display manager (login screen), select ${GREEN}Iram${NC} from the session menu."
echo -e "3. Log in and enjoy authentic Iram tiling!"
echo -e "\n${YELLOW}Useful Shortcuts:${NC}"
echo -e "  • ${GREEN}?? <query>${NC}                    : 🧠 Natural Language Shell Copilot (e.g. ?? find large files)"
echo -e "  • ${GREEN}Super + C${NC}                     : 🧭 Context-Aware Assistant (sees active window + clipboard)"
echo -e "  • ${GREEN}Super + Alt + C${NC}                 : 🧭 Context-Aware Assistant with Screen Region OCR"
echo -e "  • ${GREEN}Super + A${NC}                     : 🤖 Launch Iram Agentic OS Assistant"
echo -e "  • ${GREEN}Super + Shift + A${NC}               : 💬 Launch Agent Interactive Sidecar Window"
echo -e "  • ${GREEN}Super + Ctrl + H${NC}                : 🛡️ Instant OS Self-Healing & Service Audit"
echo -e "  • ${GREEN}Super + Ctrl + V${NC}                : 🎙️ AI Voice Assistant & Hands-Free Control"
echo -e "  • ${GREEN}Super + Shift + Print${NC}           : 👁️ Screen Vision AI Analyst & OCR"
echo -e "  • ${GREEN}Super + Ctrl + G${NC}                : 🛡️ AI Security Guard & Firewall Audit"
echo -e "  • ${GREEN}Super + Shift + V${NC}               : 🪄 AI Smart Clipboard & Code Assistant"
echo -e "  • ${GREEN}Super + Ctrl + W${NC}                : 🎨 AI Dynamic Ambient Wallpaper & Theme Palette"
echo -e "  • ${GREEN}Super + Ctrl + F${NC}                : 📂 AI Downloads & Workspace File Curator"
echo -e "  • ${GREEN}Super + Alt + M${NC}                 : 🤖 AI Model Manager GUI (Download & Manage GGUF/Ollama Models)"
echo -e "  • ${GREEN}Super + Alt + N${NC}                 : 📈 Live Stock Market News & Wofi GUI"
echo -e "  • ${GREEN}Super + Space${NC}                 : Wofi Application Launcher"
echo -e "  • ${GREEN}Super + Return${NC}                : Terminal (Alacritty)"
echo -e "  • ${GREEN}Super + Alt + Return${NC}          : Tmux Terminal Session"
echo -e "  • ${GREEN}Super + K${NC}                     : Keybindings Cheat Sheet Menu"
echo -e "  • ${GREEN}Super + V${NC}                     : Clipboard History Manager"
echo -e "  • ${GREEN}Super + N${NC}                     : 🔔 SwayNC Notification Center"
echo -e "  • ${GREEN}Super + Shift + R${NC}             : 🌟 Flagship Rice Showcase Mode (4-Tile Fastfetch/Cava/Btop/Telemetry)"
echo -e "  • ${GREEN}Super + Ctrl + Shift + Space${NC}  : 🎨 Iram 55-Theme Switcher (Zero-Restart)"
echo -e "  • ${GREEN}iram theme auto${NC}               : 🦎 Dynamic Wallpaper Theme (Auto-Chameleon)"
echo -e "  • ${GREEN}Super + Ctrl + Space${NC}          : Next Background in Active Theme"
echo -e "  • ${GREEN}Super + \` (Grave)${NC} / ${GREEN}Super + S${NC} : Toggle Scratchpad"
echo -e "  • ${GREEN}Super + Ctrl + T${NC}              : Activity Monitor (btop)"
echo -e "  • ${GREEN}Super + Escape${NC}                : Power Menu (Lock, Sleep, Logout, Shutdown)"
echo -e "  • ${GREEN}Super + Shift + S${NC}             : Screenshot Snipping Tool"
echo -e "  • ${GREEN}Super + Ctrl + Print${NC}          : OCR Text Extraction to Clipboard"
echo -e "  • ${GREEN}Super + Ctrl + R${NC}              : Set Reminder (Timer + Message)"
echo -e "  • ${GREEN}Super + Ctrl + Alt + T / W / B${NC}: Date/Time, Weather & Battery Notices"
echo -e "  • ${GREEN}Super + Ctrl + D${NC}              : Display & Monitor Settings GUI"
echo -e "  • ${GREEN}Super + Alt + D${NC}               : Instant Dictionary Definition Lookup"
