#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Debian/Ubuntu Package Builder
# Builds separate, signable packages, so a user can take the desktop without the
# AI stack or the 400 MB of wallpapers:
#
#   iram-themes    Theme palettes and wallpapers (arch-independent data)
#   iram-desktop   Hyprland session, scripts, configs and units
#   iram-ai        Agent stack dependencies, and the MCP server's recommendations
#   iram-os        Metapackage: all of the above
#
# Usage: ./build/package-deb.sh [version]
# https://github.com/apravint/iram-os
# ==============================================================================
set -euo pipefail

VERSION="${1:-26.4.3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/out"
BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf "$BUILD_ROOT"' EXIT
mkdir -p "$OUTPUT_DIR"

MAINTAINER="Ayyappa Pravin <apravint@gmail.com>"
HOMEPAGE="https://github.com/apravint/iram-os"

new_stage() {
    STAGE="$BUILD_ROOT/$1"
    mkdir -p "$STAGE/DEBIAN"
}

write_control() { # package depends recommends description
    {
        echo "Package: $1"
        echo "Version: $VERSION"
        echo "Section: x11"
        echo "Priority: optional"
        echo "Architecture: all"
        echo "Maintainer: $MAINTAINER"
        echo "Homepage: $HOMEPAGE"
        [ -n "$2" ] && echo "Depends: $2"
        [ -n "$3" ] && echo "Recommends: $3"
        echo "Description: $4"
    } > "$STAGE/DEBIAN/control"
}

build_package() {
    # --root-owner-group: files must be root-owned on the target however this was built.
    dpkg-deb --build --root-owner-group -Zzstd "$STAGE" "$OUTPUT_DIR/$1_${VERSION}_all.deb" >/dev/null
    echo "  $1_${VERSION}_all.deb ($(du -h "$OUTPUT_DIR/$1_${VERSION}_all.deb" | cut -f1))"
}

as_depends() { # file: one package per line, comments allowed
    grep -vE '^\s*(#|$)' "$1" | paste -sd, | sed 's/,/, /g'
}

echo "Building IRAM OS packages, version $VERSION:"

# ---- iram-themes ---------------------------------------------------------------
new_stage iram-themes
mkdir -p "$STAGE/usr/share/iram"
cp -a "$REPO_ROOT/themes" "$STAGE/usr/share/iram/"
write_control iram-themes "" "" "IRAM OS theme palettes and wallpapers
 Color palettes, wallpapers and previews for the IRAM OS live theme engine."
build_package iram-themes

# ---- iram-desktop --------------------------------------------------------------
new_stage iram-desktop
mkdir -p "$STAGE/usr/bin" "$STAGE/usr/share/iram" "$STAGE/usr/share/wayland-sessions" \
    "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/128x128/apps" \
    "$STAGE/usr/lib/systemd/user" "$STAGE/usr/lib/systemd/system" \
    "$STAGE/etc/profile.d" "$STAGE/etc/sudoers.d" "$STAGE/etc/sysctl.d" "$STAGE/etc/modules-load.d"

for component in bin config default system migrations mcp packages applications; do
    cp -a "$REPO_ROOT/$component" "$STAGE/usr/share/iram/"
done
if [ -d "$REPO_ROOT/assets/hub" ]; then
    mkdir -p "$STAGE/usr/share/iram/assets"
    cp -a "$REPO_ROOT/assets/hub" "$STAGE/usr/share/iram/assets/"
fi

# One copy of each script: /usr/bin links into /usr/share/iram/bin, so that a
# script's relative lookups (iram_policy.py, assets/) resolve the same everywhere.
find "$STAGE/usr/share/iram/bin" -maxdepth 1 -type f -exec chmod 0755 {} +
for script in "$REPO_ROOT"/bin/*; do
    ln -s "../share/iram/bin/$(basename "$script")" "$STAGE/usr/bin/$(basename "$script")"
done
ln -s ../share/iram/bin/iram-agent-prompt "$STAGE/usr/bin/a"

cp "$REPO_ROOT/system/iram.desktop" "$STAGE/usr/share/wayland-sessions/"
cp "$REPO_ROOT/system/iram.conf" "$STAGE/etc/iram.conf"
install -m 0644 "$REPO_ROOT/system/iram.sh" "$STAGE/etc/profile.d/iram.sh"
install -m 0644 "$REPO_ROOT/system/sysctl.d/99-iram-performance.conf" "$STAGE/etc/sysctl.d/"
install -m 0644 "$REPO_ROOT/system/modules-load.d/bbr.conf" "$STAGE/etc/modules-load.d/bbr.conf"
for sudoers_file in "$REPO_ROOT"/system/sudoers.d/*; do
    install -m 0440 "$sudoers_file" "$STAGE/etc/sudoers.d/$(basename "$sudoers_file")"
done
mkdir -p "$STAGE/usr/share/sddm/themes"
cp -r "$REPO_ROOT/system/sddm/iram" "$STAGE/usr/share/sddm/themes/iram"
install -m 0644 "$REPO_ROOT/system/iram-firstboot-auth.service" "$STAGE/usr/lib/systemd/system/"

find "$REPO_ROOT/applications" -maxdepth 1 -name '*.desktop' -exec cp {} "$STAGE/usr/share/applications/" \;
find "$REPO_ROOT/applications/icons" -maxdepth 1 -name '*.png' -exec cp {} "$STAGE/usr/share/icons/hicolor/128x128/apps/" \;
cp -a "$REPO_ROOT/config/systemd/user/." "$STAGE/usr/lib/systemd/user/"

# dpkg keeps a locally edited conffile across upgrades instead of overwriting it.
(cd "$STAGE" && find etc -type f | sed 's|^|/|') > "$STAGE/DEBIAN/conffiles"

write_control iram-desktop "$(as_depends "$REPO_ROOT/packages/desktop.list"), iram-themes (= $VERSION)" "" \
"IRAM OS Hyprland desktop session
 Hyprland session with managed systemd user services, a live theme engine,
 hardware-aware GPU configuration, config snapshots and a tiered MCP server."

cat > "$STAGE/DEBIAN/postinst" << 'SCRIPT'
#!/bin/sh
set -e
if [ "$1" = configure ]; then
    # A sudoers fragment with bad syntax can disable sudo for the whole machine.
    for fragment in /etc/sudoers.d/iram-theme-browser /etc/sudoers.d/iram-login-theme; do
        if [ -f "$fragment" ] && ! visudo -cf "$fragment" >/dev/null 2>&1; then
            echo "iram-desktop: removing invalid sudoers fragment $fragment" >&2
            rm -f "$fragment"
        fi
    done
    grep -q '^IRAM_PATH=' /etc/environment 2>/dev/null || echo "IRAM_PATH=/usr/share/iram" >> /etc/environment
    command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
    sysctl -q -p /etc/sysctl.d/99-iram-performance.conf >/dev/null 2>&1 || true
    iram-install-nerd-font || echo "iram-desktop: run 'sudo iram-install-nerd-font' for Waybar icons." >&2
    # Per-user dotfiles are not touched here, since this runs as root.
    # hyprland-start provisions them at each user's first login.
fi
exit 0
SCRIPT
cat > "$STAGE/DEBIAN/postrm" << 'SCRIPT'
#!/bin/sh
set -e
if [ "$1" = purge ]; then
    sed -i '/^IRAM_PATH=/d' /etc/environment 2>/dev/null || true
fi
exit 0
SCRIPT
chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
build_package iram-desktop

# ---- iram-ai -------------------------------------------------------------------
new_stage iram-ai
write_control iram-ai "iram-desktop (= $VERSION), python3-venv" "tesseract-ocr, nodejs" \
"IRAM OS agent stack integration
 Pulls in the requirements of the context assistant and the MCP servers.
 Run 'iram ai-setup' after installing to choose local models for this hardware."
build_package iram-ai

# ---- iram-os -------------------------------------------------------------------
new_stage iram-os
write_control iram-os "iram-desktop (= $VERSION), iram-themes (= $VERSION), iram-ai (= $VERSION)" "" \
"IRAM OS complete desktop (metapackage)
 Installs the IRAM OS desktop, themes and agent stack."
build_package iram-os

echo "Done: $OUTPUT_DIR. Publish with: build/publish-apt-repo.sh $OUTPUT_DIR <repo-dir>"
