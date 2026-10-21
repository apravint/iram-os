#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Debian/Ubuntu Package Builder (.deb)
# Packages IRAM OS Desktop into a sovereign, single-file distribution package
# https://github.com/apravint/iram-os
# ==============================================================================
set -euo pipefail

VERSION="${1:-2.0.0}"
PKG_NAME="iram-os-desktop"
ARCH="all"
FULL_PKG_NAME="${PKG_NAME}_${VERSION}_${ARCH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/out"
BUILD_ROOT="/tmp/iram-deb-build"
STAGE_DIR="${BUILD_ROOT}/${FULL_PKG_NAME}"

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}      IRAM OS - Packaging Debian Package (.deb)${NC}"
echo -e "      Package: ${BOLD}${FULL_PKG_NAME}.deb${NC}"
echo -e "${BLUE}======================================================${NC}"

# Clean previous build artifacts
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/DEBIAN" "${OUTPUT_DIR}"

# 1. Create System Directories
mkdir -p "${STAGE_DIR}/usr/bin" \
         "${STAGE_DIR}/usr/local/bin" \
         "${STAGE_DIR}/usr/share/iram" \
         "${STAGE_DIR}/usr/share/wayland-sessions" \
         "${STAGE_DIR}/usr/share/applications" \
         "${STAGE_DIR}/usr/share/icons/hicolor/128x128/apps" \
         "${STAGE_DIR}/usr/lib/systemd/user" \
         "${STAGE_DIR}/etc/profile.d" \
         "${STAGE_DIR}/etc/sudoers.d"

# 2. Deploy IRAM Core System Files into /usr/share/iram
echo "Copying IRAM OS core assets into /usr/share/iram..."
cp -a "${REPO_ROOT}/bin" "${STAGE_DIR}/usr/share/iram/"
cp -a "${REPO_ROOT}/config" "${STAGE_DIR}/usr/share/iram/"
cp -a "${REPO_ROOT}/themes" "${STAGE_DIR}/usr/share/iram/"
cp -a "${REPO_ROOT}/system" "${STAGE_DIR}/usr/share/iram/"
cp -a "${REPO_ROOT}/migrations" "${STAGE_DIR}/usr/share/iram/"
if [ -d "${REPO_ROOT}/assets" ]; then cp -a "${REPO_ROOT}/assets" "${STAGE_DIR}/usr/share/iram/"; fi
if [ -d "${REPO_ROOT}/applications" ]; then cp -a "${REPO_ROOT}/applications" "${STAGE_DIR}/usr/share/iram/"; fi

# Ensure executable permissions on all binaries
find "${STAGE_DIR}/usr/share/iram/bin" -type f -exec chmod 0755 {} +

# 3. Expose Binaries to /usr/bin
echo "Copying all IRAM and Craft binaries to /usr/bin..."
for b in "${REPO_ROOT}/bin/"*; do
    if [ -f "$b" ] || [ -L "$b" ]; then
        cp -a "$b" "${STAGE_DIR}/usr/bin/"
    fi
done
find "${STAGE_DIR}/usr/bin" -type f -exec chmod 0755 {} +

# Universal agent launcher 'a'
if [ -f "${REPO_ROOT}/bin/iram-agent-prompt" ]; then
    cp -a "${REPO_ROOT}/bin/iram-agent-prompt" "${STAGE_DIR}/usr/bin/a"
    chmod 0755 "${STAGE_DIR}/usr/bin/a"
fi

# 4. Desktop Sessions & Environment
if [ -f "${REPO_ROOT}/system/iram.desktop" ]; then
    cp -a "${REPO_ROOT}/system/iram.desktop" "${STAGE_DIR}/usr/share/wayland-sessions/iram.desktop"
fi
if [ -f "${REPO_ROOT}/system/iram.conf" ]; then
    cp -a "${REPO_ROOT}/system/iram.conf" "${STAGE_DIR}/etc/iram.conf"
fi
if [ -f "${REPO_ROOT}/system/iram.sh" ]; then
    cp -a "${REPO_ROOT}/system/iram.sh" "${STAGE_DIR}/etc/profile.d/iram.sh"
    chmod 0644 "${STAGE_DIR}/etc/profile.d/iram.sh"
fi
if [ -f "${REPO_ROOT}/system/sudoers.d/iram-theme-browser" ]; then
    cp -a "${REPO_ROOT}/system/sudoers.d/iram-theme-browser" "${STAGE_DIR}/etc/sudoers.d/iram-theme-browser"
    chmod 0440 "${STAGE_DIR}/etc/sudoers.d/iram-theme-browser"
fi

# 5. Desktop Entries and Application Icons
if [ -d "${REPO_ROOT}/applications" ]; then
    cp "${REPO_ROOT}/applications/"*.desktop "${STAGE_DIR}/usr/share/applications/" 2>/dev/null || true
    if [ -d "${REPO_ROOT}/applications/icons" ]; then
        cp "${REPO_ROOT}/applications/icons/"*.png "${STAGE_DIR}/usr/share/icons/hicolor/128x128/apps/" 2>/dev/null || true
    fi
fi

# 5b. Systemd User Services and Daemons
if [ -d "${REPO_ROOT}/systemd/user" ]; then
    echo "Installing systemd user unit definitions..."
    cp -a "${REPO_ROOT}/systemd/user/"* "${STAGE_DIR}/usr/lib/systemd/user/"
fi

# 6. Generate DEBIAN/control
echo "Writing package control manifest..."
cat << EOF > "${STAGE_DIR}/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: x11
Priority: optional
Architecture: ${ARCH}
Maintainer: Pravin <apravint@gmail.com>
Depends: hyprland, waybar, wofi, swaybg, swaylock, mako-notifier, grim, slurp, wl-clipboard, cliphist, playerctl, alacritty, btop, tesseract-ocr, ripgrep, fd-find, tmux, fzf, zoxide, eza, bat, jq, curl, wlsunset, python3, python3-pip, python3-gi, gir1.2-gtk-3.0, pavucontrol, blueman, polkit-kde-agent-1, socat
Recommends: ollama, mpv, fastmcp, qdrant-client
Homepage: https://github.com/apravint/iram-os
Description: IRAM OS Desktop - Sovereign Autonomous Agentic Linux
 IRAM OS is an agentic Linux operating environment built on Ubuntu 26.10
 and Hyprland, tailored for digital artists, engineers, and AI pair programming.
 Features the Storytold Creative Suite, live zero-restart theming, PipeWire
 hardware DSP studio audio tuning, non-destructive migrations, and first-class
 AI coding agent orchestration.
EOF

# 7. Generate DEBIAN/postinst
cat << 'EOF' > "${STAGE_DIR}/DEBIAN/postinst"
#!/bin/bash
set -e

# Setup global environment variable
if ! grep -q "IRAM_PATH" /etc/environment 2>/dev/null; then
    echo "IRAM_PATH=/usr/share/iram" >> /etc/environment
fi

# Refresh desktop databases
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Run baseline migrations if user is active
if [ -x "/usr/bin/iram-migrate" ]; then
    /usr/bin/iram-migrate run 2>/dev/null || true
fi

# Reload systemd user daemon definitions if available
if command -v systemctl >/dev/null 2>&1; then
    systemctl --global daemon-reload 2>/dev/null || true
fi

exit 0
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/postinst"

# 8. Generate DEBIAN/prerm
cat << 'EOF' > "${STAGE_DIR}/DEBIAN/prerm"
#!/bin/bash
set -e

if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -f /usr/share/wayland-sessions/iram.desktop
fi

exit 0
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/prerm"

# 9. Build the Debian Archive with dpkg-deb
echo -e "\n${YELLOW}Compiling Debian archive (.deb)...${NC}"
dpkg-deb --build --root-owner-group "${STAGE_DIR}" "${OUTPUT_DIR}/${FULL_PKG_NAME}.deb"

# 10. Verify Package
DEB_FILE="${OUTPUT_DIR}/${FULL_PKG_NAME}.deb"
SIZE=$(du -h "${DEB_FILE}" | cut -f1)
MD5=$(md5sum "${DEB_FILE}" | cut -d' ' -f1)

echo -e "\n${GREEN}✔ Package Built Successfully!${NC}"
echo -e "  File:   ${BOLD}${DEB_FILE}${NC}"
echo -e "  Size:   ${BOLD}${SIZE}${NC}"
echo -e "  MD5:    ${BOLD}${MD5}${NC}"
echo -e "\nTo install on any Ubuntu/Debian system:"
echo -e "  ${CYAN}sudo apt install ${DEB_FILE}${NC}"
