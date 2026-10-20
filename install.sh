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

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}            IRAM OS - Setup & Installation${NC}"
echo -e "${BLUE}======================================================${NC}"

# Check for sudo/root
if ! sudo -v &>/dev/null; then
    echo -e "${RED}Error: sudo access is required to install system packages.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[1/6] Installing required Wayland & Hyprland packages...${NC}"
sudo apt update
sudo apt install -y \
    hyprland \
    waybar \
    wofi \
    swaybg \
    swaylock \
    mako-notifier \
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
    git \
    socat

# Install Ollama & OpenClaw Agentic Stack
if ! command -v ollama >/dev/null 2>&1; then
    echo "Installing Ollama Local LLM Engine..."
    curl -fsSL https://ollama.com/install.sh | sh || true
fi
if command -v pip3 >/dev/null 2>&1; then
    echo "Installing Iram Agentic Stack (FastMCP, Qdrant, Crawl4AI, Docling, Graphiti, smolagents, LangGraph, Phoenix)..."
    pip3 install --break-system-packages fastmcp qdrant-client crawl4ai docling graphiti-core smolagents langgraph arize-phoenix openclaw edge-tts ddgs 2>/dev/null || true
fi
if command -v npm >/dev/null 2>&1; then
    echo "Installing Repomix AI context bundler..."
    npm install -g repomix 2>/dev/null || true
fi

echo -e "\n${YELLOW}[2/6] Installing IRAM OS core system files & theme suite...${NC}"
sudo mkdir -p /usr/share/iram

# If REPO_DIR has IRAM OS files, deploy directly; otherwise clone official repository
if [ -d "$REPO_DIR/bin" ] && [ -d "$REPO_DIR/config" ]; then
    echo "Deploying IRAM OS core from local repository ($REPO_DIR)..."
    sudo cp -a "$REPO_DIR/bin" "$REPO_DIR/config" "$REPO_DIR/themes" "$REPO_DIR/system" "$REPO_DIR/migrations" /usr/share/iram/
    if [ -d "$REPO_DIR/assets" ]; then sudo cp -a "$REPO_DIR/assets" /usr/share/iram/; fi
    if [ -d "$REPO_DIR/applications" ]; then sudo cp -a "$REPO_DIR/applications" /usr/share/iram/; fi
else
    echo "Cloning official IRAM OS repository..."
    if [ ! -d "/usr/share/iram/.git" ]; then
        sudo git clone --depth 1 https://github.com/apravint/iram-os.git /usr/share/iram
    else
        sudo git -C /usr/share/iram pull --ff-only || true
    fi
fi

# Ensure safe.directory
sudo git config --system --add safe.directory /usr/share/iram 2>/dev/null || true

# Symlink all IRAM CLI binaries to system PATH
echo "Linking IRAM CLI binaries to /usr/local/bin and /usr/bin..."
sudo cp -a "$REPO_DIR/bin/"* /usr/local/bin/
sudo chmod +x /usr/local/bin/*
for b in /usr/local/bin/iram* /usr/local/bin/craft*; do
    if [ -f "$b" ]; then
        bname="$(basename "$b")"
        sudo ln -sf "/usr/local/bin/$bname" "/usr/bin/$bname" 2>/dev/null || true
    fi
done

# Universal agent launcher 'a'
if [ -f "$REPO_DIR/bin/iram-agent-prompt" ]; then
    sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/local/bin/a 2>/dev/null || true
    sudo ln -sf /usr/local/bin/iram-agent-prompt /usr/bin/a 2>/dev/null || true
fi

if [ -f "$REPO_DIR/system/sudoers.d/iram-theme-browser" ]; then
    sudo cp "$REPO_DIR/system/sudoers.d/iram-theme-browser" /etc/sudoers.d/iram-theme-browser
    sudo chmod 0440 /etc/sudoers.d/iram-theme-browser
fi

echo -e "\n${YELLOW}[3/6] Configuring system environment & session entries...${NC}"
# System-wide IRAM_PATH
sudo cp "$REPO_DIR/system/iram.conf" /etc/iram.conf
sudo cp "$REPO_DIR/system/iram.sh" /etc/profile.d/iram.sh
if ! grep -q "IRAM_PATH" /etc/environment 2>/dev/null; then
    echo "IRAM_PATH=/usr/share/iram" | sudo tee -a /etc/environment >/dev/null
fi

# Install Wayland session
sudo cp "$REPO_DIR/system/iram.desktop" /usr/share/wayland-sessions/iram.desktop

echo -e "\n${YELLOW}[4/6] Installing user dotfiles & scripts...${NC}"
mkdir -p "$HOME/.config" "$HOME/.local/bin" "$HOME/.config/iram/hooks"

# Backup existing configs if they exist and are not symlinks
for dir in hypr waybar wofi mako; do
    if [ -d "$HOME/.config/$dir" ] && [ ! -d "$HOME/.config/$dir.bak" ]; then
        echo "Backing up existing ~/.config/$dir to ~/.config/$dir.bak..."
        cp -r "$HOME/.config/$dir" "$HOME/.config/$dir.bak"
    fi
done

# Copy configurations & MCP servers
mkdir -p "$HOME/.config/mcp"
cp -r "$REPO_DIR/config/"* "$HOME/.config/"

# Copy scripts & make executable
cp -a "$REPO_DIR/bin/"* "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/"*

# Copy Iram desktop webapps and icons
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/128x128/apps"
cp "$REPO_DIR/applications/"*.desktop "$HOME/.local/share/applications/" 2>/dev/null || true
cp "$REPO_DIR/applications/icons/"*.png "$HOME/.local/share/icons/hicolor/128x128/apps/" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# Symlink Debian-specific binary names if needed
ln -sf /usr/bin/batcat "$HOME/.local/bin/bat" 2>/dev/null || true
ln -sf /usr/bin/fdfind "$HOME/.local/bin/fd" 2>/dev/null || true

# Setup modular lifecycle hooks
mkdir -p "$HOME/.config/iram/hooks"
if [ -d "$REPO_DIR/config/iram/hooks" ]; then
    cp -a "$REPO_DIR/config/iram/hooks/"* "$HOME/.config/iram/hooks/" 2>/dev/null || true
    chmod +x "$HOME/.config/iram/hooks"/*/*.sh 2>/dev/null || true
fi

# Configure Iram Shell Environment in ~/.bashrc
if ! grep -q "IRAM_PATH" "$HOME/.bashrc" 2>/dev/null; then
    cat << 'EOF' >> "$HOME/.bashrc"

# IRAM OS Environment & Shell Tools
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
EOF
fi

echo -e "\n${YELLOW}[5/6] Initializing default Iram theme, migrations & services...${NC}"
export IRAM_PATH=/usr/share/iram

# Run non-destructive migrations
if [ -x "$HOME/.local/bin/iram-migrate" ]; then
    echo "Running IRAM OS migrations..."
    "$HOME/.local/bin/iram-migrate" run || true
fi

iram theme set "Cyberpunk Neon" || iram theme set "Tokyo Storm" || true
"$HOME/.local/bin/iram-theme-sync-all" || true
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable --now iram-agentd.service 2>/dev/null || true
systemctl --user enable --now iram-cliphist.service 2>/dev/null || true
systemctl --user enable --now iram-hub.service 2>/dev/null || true
systemctl --user enable --now iram-mcp-server.service 2>/dev/null || true
systemctl --user enable --now iram-dual-wifi-keepalive.service 2>/dev/null || true
systemctl --user enable --now iram-healthd.timer 2>/dev/null || true
systemctl --user enable --now iram-security.timer 2>/dev/null || true
systemctl --user enable --now iram-organizer.timer 2>/dev/null || true

# Unmute audio sinks so sound works out of the box
for sink in $(pactl list sinks short 2>/dev/null | awk '{print $2}'); do
    pactl set-sink-mute "$sink" 0 2>/dev/null || true
    pactl set-sink-volume "$sink" 100% 2>/dev/null || true
done

echo -e "\n${YELLOW}[6/6] Verifying Hyprland configuration...${NC}"
if hyprland --verify-config --config "$HOME/.config/hypr/hyprland.conf" >/dev/null 2>&1; then
    echo -e "${GREEN}Hyprland configuration verified: OK!${NC}"
else
    echo -e "${YELLOW}Warning: Hyprland configuration check had warnings, but file was installed successfully.${NC}"
fi

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}🎉 Installation Complete!${NC}"
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
echo -e "  • ${GREEN}Super + Ctrl + Shift + Space${NC}  : Iram 22-Theme Switcher"
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

