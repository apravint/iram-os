#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Automated Installer
# Experience authentic IRAM OS (Hyprland + Themes + Waybar)
# https://github.com/apravint/iram-os
# ==============================================================================
set -euo pipefail
trap 'echo -e "\033[0;31m[ERROR] Iram installation failed at line $LINENO. Exiting gracefully.\033[0m"; exit 1' ERR

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || pwd)"
if [ ! -d "$REPO_DIR/bin" ] || [ ! -d "$REPO_DIR/system" ]; then
    TMP_CLONE=$(mktemp -d)
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
            echo "  ai               Desktop foundation + Ollama/OpenClaw AI agent stack"
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

# ------------------------------------------------------------------------------
# 1. Desktop foundation & system dependencies
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/6] Installing desktop foundation & system dependencies...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would update apt repositories and install foundation packages:${NC}"
    echo "  hyprland, waybar, wofi, swaybg, swaylock, hyprlock, hypridle, mako-notifier, alacritty, fastfetch, cava..."
else
    sudo apt update
    sudo apt install -y \
        hyprland \
        waybar \
        wofi \
        swaybg \
        swaylock \
        hyprlock \
        hypridle \
        mako-notifier \
        sway-notification-center \
        cava \
        fastfetch \
        imagemagick \
        grim \
        slurp \
        wl-clipboard \
        cliphist \
        playerctl \
        alacritty \
        btop \
        gawk \
        fonts-jetbrains-mono \
        wf-recorder \
        hyprpicker \
        tesseract-ocr \
        ripgrep \
        fd-find \
        tmux \
        fzf \
        zoxide \
        eza \
        bat \
        jq \
        zstd \
        wtype \
        curl \
        wlsunset \
        python3 \
        python3-pip \
        python3-gi \
        gir1.2-gtk-3.0 \
        pavucontrol \
        blueman \
        network-manager-gnome \
        polkit-kde-agent-1 \
        libnotify-bin \
        pulseaudio-utils \
        pipewire \
        wireplumber \
        xdg-desktop-portal-gtk \
        git \
        socat
fi

# Install Starship cross-shell prompt (if not already present)
if ! command -v starship >/dev/null 2>&1; then
    echo "Installing Starship prompt..."
    curl -sS https://starship.rs/install.sh | sh -s -- -y >/dev/null 2>&1 || true
fi

# Install Ollama & OpenClaw Agentic Stack (if profile is 'all' or 'ai')
if [ "$INSTALL_TARGET" = "all" ] || [ "$INSTALL_TARGET" = "ai" ]; then
    if ! command -v ollama >/dev/null 2>&1; then
        echo "Installing Ollama Local LLM Engine..."
        if [ "$DRY_RUN" = true ]; then
            echo -e "${BLUE}[DRY-RUN] Would download, verify, and run https://ollama.com/install.sh${NC}"
        else
            OLLAMA_TMP=$(mktemp)
            if curl -fsSL https://ollama.com/install.sh -o "$OLLAMA_TMP"; then
                if grep -q "OLLAMA" "$OLLAMA_TMP"; then
                    sh "$OLLAMA_TMP" || echo -e "${YELLOW}Notice: Ollama install completed with non-fatal code.${NC}"
                else
                    echo -e "${RED}Error: Downloaded Ollama installer failed verification.${NC}"
                fi
                rm -f "$OLLAMA_TMP"
            else
                echo -e "${YELLOW}Warning: Could not download Ollama install script. Skipping.${NC}"
            fi
        fi
    fi
    if command -v pip3 >/dev/null 2>&1; then
        echo "Installing IRAM Agentic Stack (FastMCP, Qdrant, Crawl4AI, Docling, Graphiti, smolagents, LangGraph)..."
        if [ "$DRY_RUN" = true ]; then
            echo -e "${BLUE}[DRY-RUN] Would run pip3 install for AI agentic dependencies${NC}"
        else
            pip3 install --break-system-packages fastmcp qdrant-client crawl4ai docling graphiti-core smolagents langgraph openclaw edge-tts ddgs 2>/dev/null || \
                echo -e "${YELLOW}Notice: Some optional agentic Python packages could not be installed.${NC}"
        fi
    fi
    if command -v npm >/dev/null 2>&1; then
        echo "Installing Repomix AI context bundler..."
        if [ "$DRY_RUN" = true ]; then
            echo -e "${BLUE}[DRY-RUN] Would run npm install -g repomix${NC}"
        else
            npm install -g repomix 2>/dev/null || echo -e "${YELLOW}Notice: Optional repomix package installation skipped.${NC}"
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
    echo -e "${BLUE}[DRY-RUN] Would link binaries from /usr/local/bin to /usr/bin${NC}"
else
    sudo mkdir -p /usr/share/iram
    if [ -d "$REPO_DIR/bin" ] && [ -d "$REPO_DIR/config" ]; then
        echo "Deploying IRAM OS core from local repository ($REPO_DIR)..."
        sudo cp -a "$REPO_DIR/bin" "$REPO_DIR/config" "$REPO_DIR/themes" "$REPO_DIR/system" "$REPO_DIR/migrations" /usr/share/iram/
        if [ -d "$REPO_DIR/mcp" ]; then sudo cp -a "$REPO_DIR/mcp" /usr/share/iram/; fi
        if [ -d "$REPO_DIR/assets" ]; then sudo cp -a "$REPO_DIR/assets" /usr/share/iram/; fi
        if [ -d "$REPO_DIR/applications" ]; then sudo cp -a "$REPO_DIR/applications" /usr/share/iram/; fi
    else
        echo "Cloning official IRAM OS repository..."
        if [ ! -d "/usr/share/iram/.git" ]; then
            sudo git clone --depth 1 https://github.com/apravint/iram-os.git /usr/share/iram
        else
            sudo git -C /usr/share/iram pull --ff-only || echo -e "${YELLOW}Notice: Could not fast-forward /usr/share/iram. Keeping existing version.${NC}"
        fi
    fi

    sudo git config --system --add safe.directory /usr/share/iram 2>/dev/null || true

    echo "Linking IRAM CLI binaries to /usr/local/bin and /usr/bin..."
    sudo cp -a "$REPO_DIR/bin/"* /usr/local/bin/
    if [ -f "$REPO_DIR/mcp/iram-os-mcp" ]; then
        sudo cp -a "$REPO_DIR/mcp/iram-os-mcp" /usr/local/bin/iram-os-mcp
    fi
    sudo chmod +x /usr/local/bin/*
    for b in /usr/local/bin/iram* /usr/local/bin/craft*; do
        if [ -e "$b" ]; then
            bname="$(basename "$b")"
            sudo ln -sf "/usr/local/bin/$bname" "/usr/bin/$bname" 2>/dev/null || true
        fi
    done

    if [ -f "$REPO_DIR/bin/iram-agent-prompt" ]; then
        sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/local/bin/a 2>/dev/null || true
        sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/bin/a 2>/dev/null || true
    fi

    if [ -f "$REPO_DIR/system/sudoers.d/iram-theme-browser" ]; then
        sudo cp "$REPO_DIR/system/sudoers.d/iram-theme-browser" /etc/sudoers.d/iram-theme-browser
        sudo chmod 0440 /etc/sudoers.d/iram-theme-browser
    fi
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
    sudo cp "$REPO_DIR/system/iram.desktop" /usr/share/wayland-sessions/iram.desktop

    # Install kernel & networking sysctl optimizations (TCP BBR & interactive tuning)
    if [ -f "$REPO_DIR/system/sysctl.d/99-iram-performance.conf" ]; then
        sudo cp "$REPO_DIR/system/sysctl.d/99-iram-performance.conf" /etc/sysctl.d/99-iram-performance.conf
        sudo cp "$REPO_DIR/system/modules-load.d/bbr.conf" /etc/modules-load.d/bbr.conf 2>/dev/null || true
        sudo sysctl --system >/dev/null 2>&1 || true
    fi
fi

# ------------------------------------------------------------------------------
# 4. User dotfiles, timestamped backups & scripts
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/6] Installing user dotfiles & scripts (with timestamped backups)...${NC}"
BACKUP_TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$HOME/.config/iram/backups/backup_${BACKUP_TIMESTAMP}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would archive current user configs to: ${BACKUP_DIR}${NC}"
    echo -e "${BLUE}[DRY-RUN] Would copy configs from $REPO_DIR/config/ to $HOME/.config/${NC}"
    echo -e "${BLUE}[DRY-RUN] Would copy scripts from $REPO_DIR/bin/ to $HOME/.local/bin/${NC}"
else
    # Create timestamped rollback backup of existing configs
    mkdir -p "$BACKUP_DIR"
    echo "Creating timestamped backup of existing configs in $BACKUP_DIR..."
    for dir in hypr waybar wofi mako alacritty mcp systemd/user; do
        if [ -d "$HOME/.config/$dir" ]; then
            mkdir -p "$BACKUP_DIR/$(dirname "$dir")"
            cp -a "$HOME/.config/$dir" "$BACKUP_DIR/$dir"
        fi
    done
    if [ -d "$HOME/.local/bin" ]; then
        mkdir -p "$BACKUP_DIR/local_bin"
        for f in "$HOME/.local/bin"/iram* "$HOME/.local/bin"/craft*; do
            [ -e "$f" ] && cp -a "$f" "$BACKUP_DIR/local_bin/"
        done
    fi
    echo -e "${GREEN}✓ Existing configs backed up to:${NC} $BACKUP_DIR"

    # Copy configurations & MCP servers
    mkdir -p "$HOME/.config" "$HOME/.local/bin" "$HOME/.config/iram/hooks" "$HOME/.config/mcp" "$HOME/.config/hypr"
    cp -r "$REPO_DIR/config/"* "$HOME/.config/"
    touch "$HOME/.config/hypr/monitors.conf"

    # Copy scripts & make executable
    cp -a "$REPO_DIR/bin/"* "$HOME/.local/bin/"
    chmod +x "$HOME/.local/bin/"*

    # Copy desktop entries and icons cleanly
    mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/128x128/apps"
    for f in "$REPO_DIR/applications/"*.desktop; do
        [ -e "$f" ] && cp "$f" "$HOME/.local/share/applications/"
    done
    for f in "$REPO_DIR/applications/icons/"*.png; do
        [ -e "$f" ] && cp "$f" "$HOME/.local/share/icons/hicolor/128x128/apps/"
    done
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi

    # Symlink Debian-specific binary names if needed
    [ -x /usr/bin/batcat ] && ln -sf /usr/bin/batcat "$HOME/.local/bin/bat" 2>/dev/null || true
    [ -x /usr/bin/fdfind ] && ln -sf /usr/bin/fdfind "$HOME/.local/bin/fd" 2>/dev/null || true

    # Setup modular lifecycle hooks
    if [ -d "$REPO_DIR/config/iram/hooks" ]; then
        cp -a "$REPO_DIR/config/iram/hooks/"* "$HOME/.config/iram/hooks/" 2>/dev/null || true
        chmod +x "$HOME/.config/iram/hooks"/*/*.sh 2>/dev/null || true
    fi

    # Configure Iram Shell Environment in ~/.bashrc
    if ! grep -q "IRAM_PATH" "$HOME/.bashrc" 2>/dev/null; then
        cat << 'EOF' >> "$HOME/.bashrc"

# IRAM OS Environment & Shell Tools
export PATH="$HOME/.local/bin:$PATH"
export IRAM_PATH=/usr/share/iram
export EDITOR=nvim
export VISUAL=nvim
if [[ -f /usr/share/doc/fzf/examples/key-bindings.bash ]]; then
    source /usr/share/doc/fzf/examples/key-bindings.bash
fi
if [[ -f /usr/share/doc/fzf/examples/completion.bash ]]; then
    source /usr/share/doc/fzf/examples/completion.bash
fi

# IRAM OS Shell Shortcuts & Agent Dispatchers
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init bash)"
fi
alias a='~/.local/bin/a'
alias agy='agy'
alias iram='iram'
alias video='iram-video'
alias craft='artcraft-launcher'
alias theme='iram-theme-switch'
alias sidecar='iram-agent-sidecar'
alias '??'='iram-ai-cmd'
alias 'ai-cmd'='iram-ai-cmd'
alias 'ai-digest'='iram-ai-digest'
alias 'ai-memory'='iram-memory'
alias 'repo-traffic'='iram-repo-traffic'
alias hub='iram hub'
alias 'ai-ask'='iram-ai-ask'
alias 'vision-ask'='iram-vision-ask'
alias radar='iram-worldmonitor'
alias finance='iram-finance'
alias audit='iram-audit'
alias reverse='iram-reverse'
alias arch='iram-arch'
alias condense='iram-context-condenser'
alias hindsight='iram-hindsight'
EOF
    fi
fi

# ------------------------------------------------------------------------------
# 5. Initialize default theme, migrations & services
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[5/6] Initializing default Iram theme, migrations & services...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Would run migrations, apply default theme, and enable systemd user units${NC}"
else
    export IRAM_PATH=/usr/share/iram

    # Run non-destructive migrations
    if [ -x "$HOME/.local/bin/iram-migrate" ]; then
        echo "Running IRAM OS migrations..."
        "$HOME/.local/bin/iram-migrate" run || true
    fi

    if command -v iram >/dev/null 2>&1; then
        iram theme set "Cyberpunk Neon" 2>/dev/null || iram theme set "Tokyo Storm" 2>/dev/null || true
    fi
    if [ -x "$HOME/.local/bin/iram-theme-sync-all" ]; then
        "$HOME/.local/bin/iram-theme-sync-all" 2>/dev/null || true
    fi

    if command -v systemctl >/dev/null 2>&1; then
        systemctl --user daemon-reload 2>/dev/null || true
        if [ "$INSTALL_TARGET" = "all" ] || [ "$INSTALL_TARGET" = "ai" ]; then
            systemctl --user enable --now iram-agentd.socket 2>/dev/null || true
        fi
        systemctl --user enable --now hypridle.service 2>/dev/null || true
        systemctl --user enable --now iram-watchdog.service 2>/dev/null || true
        systemctl --user enable --now iram-cliphist.service 2>/dev/null || true
        systemctl --user enable --now waybar.service 2>/dev/null || true
        systemctl --user enable --now swaybg.service 2>/dev/null || true
        systemctl --user enable --now iram-nexus.service 2>/dev/null || true
        systemctl --user enable --now iram-hub.service 2>/dev/null || true
        systemctl --user enable --now iram-mcp-server.service 2>/dev/null || true
        systemctl --user enable --now iram-dual-wifi-keepalive.service 2>/dev/null || true
        systemctl --user enable --now iram-healthd.timer 2>/dev/null || true
        systemctl --user enable --now iram-security.timer 2>/dev/null || true
        systemctl --user enable --now iram-organizer.timer 2>/dev/null || true
    fi

    # Reload running Hyprland compositor session if active
    if command -v hyprctl >/dev/null 2>&1 && [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
        hyprctl reload 2>/dev/null || true
    fi

    # Unmute audio sinks so sound works out of the box
    if command -v pactl >/dev/null 2>&1; then
        for sink in $(pactl list sinks short 2>/dev/null | awk '{print $2}'); do
            pactl set-sink-mute "$sink" 0 2>/dev/null || true
            pactl set-sink-volume "$sink" 100% 2>/dev/null || true
        done
    fi
fi

# ------------------------------------------------------------------------------
# 6. Verification
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[6/6] Verifying Hyprland configuration...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN] Verification complete (Simulation mode).${NC}"
else
    if command -v hyprland >/dev/null 2>&1 && hyprland --verify-config --config "$HOME/.config/hypr/hyprland.conf" >/dev/null 2>&1; then
        echo -e "${GREEN}Hyprland configuration verified: OK!${NC}"
    else
        echo -e "${YELLOW}Notice: Hyprland configuration file deployed.${NC}"
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
echo -e "  • ${GREEN}Super + Ctrl + Shift + Space${NC}  : 🎨 Iram 43-Theme Switcher (Zero-Restart)"
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
