#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Automated Live ISO Builder
# Builds a bootable hybrid UEFI/BIOS Live ISO for IRAM OS
# ==============================================================================
set -euo pipefail

# Target base release: defaults to the current LTS, 26.04 (Resolute).
CODENAME="${BASE_CODENAME:-resolute}"
DISTRO_VERSION="${DISTRO_VERSION:-26.04}"
DISTRO_NAME="iram-os"
ARCH="amd64"
# zstd boots several times faster than xz for a modest size cost. xz for smallest image.
SQUASHFS_COMPRESSION="${SQUASHFS_COMPRESSION:-zstd}"
# Ollama adds gigabytes of GPU libraries; users get it from `iram ai-setup` instead.
ISO_INCLUDE_OLLAMA="${ISO_INCLUDE_OLLAMA:-0}"
OUTPUT_DIR="${PWD}/out"
ISO_NAME="${DISTRO_NAME}-${DISTRO_VERSION}-${ARCH}.iso"
APT_MIRROR="${APT_MIRROR:-http://archive.ubuntu.com/ubuntu/}"

# Colors for logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_step() { echo -e "${GREEN}[STEP]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$(id -u)" -ne 0 ]; then
    log_err "This script must be run as root (sudo)."
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ------------------------------------------------------------------------------
# 1. Install Build Dependencies on Host
# ------------------------------------------------------------------------------
log_step "Installing ISO build tools on host system..."
apt update -y
apt install -y \
    binutils \
    debootstrap \
    squashfs-tools \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    isolinux \
    syslinux-utils \
    zstd

# ------------------------------------------------------------------------------
# 2. Prepare Clean Directories
# ------------------------------------------------------------------------------
log_step "Preparing build directories..."
# A fresh private directory: predictable /tmp paths owned by root are a symlink risk,
# and rm -rf over a tree with a surviving bind mount would delete the host's /dev.
BUILD_DIR="$(mktemp -d /var/tmp/iram-iso-build-XXXXXX)"
ROOTFS_DIR="${BUILD_DIR}/rootfs"
ISO_DIR="${BUILD_DIR}/iso"
mkdir -p "${ROOTFS_DIR}" "${ISO_DIR}/casper" "${ISO_DIR}/boot/grub" "${OUTPUT_DIR}"
rm -f "${OUTPUT_DIR}"/*.iso "${OUTPUT_DIR}/sha256sum.txt"

# Not findmnt -R: it finds nothing when the directory itself is not a mountpoint,
# which is the case here, and would report bind mounts as gone while they are live.
mounts_under_rootfs() {
    findmnt -rno TARGET | awk -v root="${ROOTFS_DIR}/" 'index($0, root) == 1' | sort -r
}

unmount_virtual_filesystems() {
    local mountpoint
    while read -r mountpoint; do
        umount "$mountpoint" || log_warn "Could not unmount $mountpoint"
    done < <(mounts_under_rootfs)
}

cleanup() {
    log_info "Cleaning up build tree..."
    unmount_virtual_filesystems
    if [ -n "$(mounts_under_rootfs)" ]; then
        log_warn "Mounts remain under ${ROOTFS_DIR}; leaving ${BUILD_DIR} for manual cleanup."
    else
        rm -rf --one-file-system "${BUILD_DIR}"
    fi
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# 3. Bootstrap Base System
# ------------------------------------------------------------------------------
log_step "Bootstrapping minimal system base ${CODENAME} (${ARCH})..."

# Ensure debootstrap has a suite script for target codename (e.g. resolute -> gutsy)
if [ -d "/usr/share/debootstrap/scripts" ] && [ ! -e "/usr/share/debootstrap/scripts/${CODENAME}" ]; then
    log_info "Creating debootstrap suite link for ${CODENAME} -> gutsy..."
    ln -s gutsy "/usr/share/debootstrap/scripts/${CODENAME}" || true
fi

debootstrap --arch="${ARCH}" --variant=minbase "${CODENAME}" "${ROOTFS_DIR}" "${APT_MIRROR}"

# Configure DNS so chroot networking works reliably
mkdir -p "${ROOTFS_DIR}/etc"
echo "nameserver 1.1.1.1" > "${ROOTFS_DIR}/etc/resolv.conf"
echo "nameserver 8.8.8.8" >> "${ROOTFS_DIR}/etc/resolv.conf"

# Mount virtual filesystems for chroot
mount --bind /dev "${ROOTFS_DIR}/dev"
mount --bind /dev/pts "${ROOTFS_DIR}/dev/pts"
mount -t proc proc "${ROOTFS_DIR}/proc"
mount -t sysfs sysfs "${ROOTFS_DIR}/sys"

# Package maintainer scripts must not start services inside the chroot.
printf '#!/bin/sh\nexit 101\n' > "${ROOTFS_DIR}/usr/sbin/policy-rc.d"
chmod 0755 "${ROOTFS_DIR}/usr/sbin/policy-rc.d"

# Ship copyright files only; docs, man pages and foreign locales never get unpacked.
mkdir -p "${ROOTFS_DIR}/etc/dpkg/dpkg.cfg.d"
cat << 'EOF' > "${ROOTFS_DIR}/etc/dpkg/dpkg.cfg.d/01-iram-minimize"
path-exclude=/usr/share/doc/*
path-include=/usr/share/doc/*/copyright
path-exclude=/usr/share/man/*
path-exclude=/usr/share/info/*
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/en*
path-include=/usr/share/locale/locale.alias
path-exclude=/usr/share/gnome/help/*
path-exclude=/usr/share/lintian/*
EOF

# ------------------------------------------------------------------------------
# 4. Configure System Inside Chroot
# ------------------------------------------------------------------------------
log_step "Configuring packages, kernel, live-boot and desktop environment in chroot..."

# Setup apt sources with universe & multiverse
cat << EOF > "${ROOTFS_DIR}/etc/apt/sources.list"
deb ${APT_MIRROR} ${CODENAME} main restricted universe multiverse
deb ${APT_MIRROR} ${CODENAME}-updates main restricted universe multiverse
deb ${APT_MIRROR} ${CODENAME}-security main restricted universe multiverse
EOF

# Setup hostname and hosts
echo "iram" > "${ROOTFS_DIR}/etc/hostname"
cat << EOF > "${ROOTFS_DIR}/etc/hosts"
127.0.0.1   localhost
127.0.1.1   iram
::1         localhost ip6-localhost ip6-loopback
EOF

# Install packages inside chroot
mkdir -p "${ROOTFS_DIR}/tmp/iram-packages"
grep -hvE '^\s*(#|$)' "${REPO_ROOT}/packages/iso.list" > "${ROOTFS_DIR}/tmp/iram-packages/iso"
grep -hvE '^\s*(#|$)' "${REPO_ROOT}/packages/desktop.list" > "${ROOTFS_DIR}/tmp/iram-packages/desktop"

chroot "${ROOTFS_DIR}" /bin/bash -s "${CODENAME}" "${DISTRO_VERSION}" "${ISO_INCLUDE_OLLAMA}" << 'CHROOT_EOF'
set -euo pipefail
CODENAME="$1"
DISTRO_VERSION="$2"
ISO_INCLUDE_OLLAMA="$3"
export DEBIAN_FRONTEND=noninteractive

apt-get update -y

# Essential repository and certificate tools
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    software-properties-common

# If Hyprland is not available in base repositories, add cppiber PPA
if ! apt-cache show hyprland >/dev/null 2>&1; then
    echo "Hyprland not found in base repositories. Adding cppiber PPA for ${CODENAME}..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xA54D23B62FF3FCC76EFF71E8FDBAAA1CF0CCF48E" | gpg --dearmor -o /etc/apt/keyrings/cppiber-hyprland.gpg
    echo "deb [signed-by=/etc/apt/keyrings/cppiber-hyprland.gpg] https://ppa.launchpadcontent.net/cppiber/hyprland/ubuntu ${CODENAME} main" > /etc/apt/sources.list.d/cppiber-hyprland.list
    apt-get update -y
fi

# Kernel, live boot, and bare-metal installer tooling
mapfile -t ISO_PACKAGES < /tmp/iram-packages/iso
apt-get install -y --no-install-recommends "${ISO_PACKAGES[@]}"

# Desktop stack. Recommends stay off: they double the image for little benefit.
mapfile -t DESKTOP_PACKAGES < /tmp/iram-packages/desktop
apt-get install -y --no-install-recommends "${DESKTOP_PACKAGES[@]}"

if [ "$ISO_INCLUDE_OLLAMA" = "1" ]; then
    OLLAMA_TMP=$(mktemp)
    curl -fsSL https://ollama.com/install.sh -o "$OLLAMA_TMP"
    sh "$OLLAMA_TMP"
    rm -f "$OLLAMA_TMP"
fi
python3 -m venv --system-site-packages /opt/iram-ai
/opt/iram-ai/bin/pip install --quiet edge-tts ddgs
/opt/iram-ai/bin/python -c 'import site; print(site.getsitepackages()[0])' > /usr/lib/python3/dist-packages/iram-ai.pth

# Setup IRAM OS system core directory
mkdir -p /usr/share/iram

# Enable essential systemd services
systemctl enable NetworkManager.service 2>/dev/null || true
systemctl enable bluetooth.service 2>/dev/null || true
systemctl enable greetd.service

# Clean caches so the ISO stays under GitHub's 2 GB release asset limit
apt-get autoremove -y --purge
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/*
CHROOT_EOF

# ------------------------------------------------------------------------------
# 5. Inject Iram Desktop Configurations & Scripts
# ------------------------------------------------------------------------------
log_step "Injecting Iram scripts, systemd units, and skeleton user configs..."

# Copy IRAM OS sovereign system files into /usr/share/iram
mkdir -p "${ROOTFS_DIR}/usr/share/iram"
cp -a --remove-destination "${REPO_ROOT}/bin" "${REPO_ROOT}/config" "${REPO_ROOT}/default" "${REPO_ROOT}/themes" "${REPO_ROOT}/system" "${REPO_ROOT}/migrations" "${REPO_ROOT}/mcp" "${REPO_ROOT}/packages" "${ROOTFS_DIR}/usr/share/iram/"
if [ -d "${REPO_ROOT}/assets" ]; then
    # The README's showcase video and GIF do not belong on the install medium.
    mkdir -p "${ROOTFS_DIR}/usr/share/iram/assets"
    find "${REPO_ROOT}/assets" -mindepth 1 -maxdepth 1 ! -name '*.mp4' ! -name '*.gif' ! -name 'screenshots' \
        -exec cp -a --remove-destination {} "${ROOTFS_DIR}/usr/share/iram/assets/" \;
fi
if [ -d "${REPO_ROOT}/applications" ]; then cp -a --remove-destination "${REPO_ROOT}/applications" "${ROOTFS_DIR}/usr/share/iram/"; fi

# Copy IRAM system-wide binaries & profile
mkdir -p "${ROOTFS_DIR}/usr/local/bin" "${ROOTFS_DIR}/usr/bin" "${ROOTFS_DIR}/usr/share/wayland-sessions" "${ROOTFS_DIR}/etc/profile.d"
cp -a --remove-destination "${REPO_ROOT}/bin/"* "${ROOTFS_DIR}/usr/local/bin/"
find "${ROOTFS_DIR}/usr/local/bin/" -type f -exec chmod 0755 {} + 2>/dev/null || true

# Symlink all iram binaries into /usr/bin
chroot "${ROOTFS_DIR}" /bin/bash << 'POST_CHROOT_EOF'
for bin_file in /usr/local/bin/iram* /usr/local/bin/craft* /usr/local/bin/hyprland-start; do
    if [ -f "$bin_file" ] || [ -L "$bin_file" ]; then
        base_name="$(basename "$bin_file")"
        ln -sf "$bin_file" "/usr/bin/${base_name}" 2>/dev/null || true
    fi
done
if [ -f "/usr/local/bin/iram-agent-prompt" ]; then
    ln -sf "/usr/local/bin/iram-agent-prompt" "/usr/bin/a" 2>/dev/null || true
    ln -sf "/usr/local/bin/iram-agent-prompt" "/usr/local/bin/a" 2>/dev/null || true
fi
POST_CHROOT_EOF

if [ -f "${REPO_ROOT}/system/iram.conf" ]; then
    cp -a --remove-destination "${REPO_ROOT}/system/iram.conf" "${ROOTFS_DIR}/etc/iram.conf"
fi
if [ -f "${REPO_ROOT}/system/iram.sh" ]; then
    cp -a --remove-destination "${REPO_ROOT}/system/iram.sh" "${ROOTFS_DIR}/etc/profile.d/iram.sh"
fi
if ! grep -q "IRAM_PATH" "${ROOTFS_DIR}/etc/environment" 2>/dev/null; then
    echo "IRAM_PATH=/usr/share/iram" >> "${ROOTFS_DIR}/etc/environment"
fi
if [ -f "${REPO_ROOT}/system/sudoers.d/iram-theme-browser" ]; then
    mkdir -p "${ROOTFS_DIR}/etc/sudoers.d"
    cp -a --remove-destination "${REPO_ROOT}/system/sudoers.d/iram-theme-browser" "${ROOTFS_DIR}/etc/sudoers.d/iram-theme-browser"
    chmod 0440 "${ROOTFS_DIR}/etc/sudoers.d/iram-theme-browser"
fi
if [ -f "${REPO_ROOT}/system/iram-firstboot-auth.service" ]; then
    mkdir -p "${ROOTFS_DIR}/etc/systemd/system"
    cp -a --remove-destination "${REPO_ROOT}/system/iram-firstboot-auth.service" "${ROOTFS_DIR}/etc/systemd/system/iram-firstboot-auth.service"
    chroot "${ROOTFS_DIR}" systemctl enable iram-firstboot-auth.service 2>/dev/null || true
fi

bash "${REPO_ROOT}/bin/iram-install-nerd-font" "${ROOTFS_DIR}"
chroot "${ROOTFS_DIR}" /bin/bash -c 'if command -v fc-cache >/dev/null; then fc-cache -f; fi'

# Copy skeleton configs so every user (and live user) gets them
mkdir -p "${ROOTFS_DIR}/etc/skel/.config" "${ROOTFS_DIR}/etc/skel/.local/bin" "${ROOTFS_DIR}/etc/skel/.local/share/applications" "${ROOTFS_DIR}/etc/skel/.local/share/icons/hicolor/128x128/apps"
cp -a --remove-destination "${REPO_ROOT}/config/"* "${ROOTFS_DIR}/etc/skel/.config/"
cp -a --remove-destination "${REPO_ROOT}/bin/"* "${ROOTFS_DIR}/etc/skel/.local/bin/"
for f in "${REPO_ROOT}/applications/"*.desktop; do
    if [ -e "$f" ]; then
        cp -a --remove-destination "$f" "${ROOTFS_DIR}/etc/skel/.local/share/applications/"
    fi
done
for f in "${REPO_ROOT}/applications/icons/"*.png; do
    if [ -e "$f" ]; then
        cp -a --remove-destination "$f" "${ROOTFS_DIR}/etc/skel/.local/share/icons/hicolor/128x128/apps/"
    fi
done

# Everything hyprland.conf sources must exist, or the session opens on an error banner.
for hypr_include in monitors.conf webapps.conf theme.conf gpu.conf; do
    : > "${ROOTFS_DIR}/etc/skel/.config/hypr/${hypr_include}"
done
cp -a "${REPO_ROOT}/config/hypr/user-overrides.conf.example" "${ROOTFS_DIR}/etc/skel/.config/hypr/user-overrides.conf"

# Session units start for every user, without a per-home enable step.
SKEL_WANTS="${ROOTFS_DIR}/etc/skel/.config/systemd/user/graphical-session.target.wants"
mkdir -p "$SKEL_WANTS"
for unit in waybar swaybg swaync hypridle iram-cliphist iram-cliphist-image iram-polkit-agent iram-watchdog; do
    ln -sf "../${unit}.service" "$SKEL_WANTS/${unit}.service"
done
ln -sf ../iram-battery.timer "$SKEL_WANTS/iram-battery.timer"

# cp -a kept the build user's ownership. Left that way, whoever shares that UID on the
# target could rewrite scripts on root's PATH, and sudo ignores the sudoers fragment.
for owned_path in usr/share/iram usr/local/bin usr/local/share/fonts etc/skel etc/iram.conf etc/profile.d/iram.sh \
    etc/sudoers.d/iram-theme-browser etc/systemd/system/iram-firstboot-auth.service; do
    if [ -e "${ROOTFS_DIR}/${owned_path}" ]; then
        chown -hR root:root "${ROOTFS_DIR}/${owned_path}"
        chmod -R go-w "${ROOTFS_DIR}/${owned_path}"
    fi
done
chmod 0440 "${ROOTFS_DIR}/etc/sudoers.d/iram-theme-browser"

# Live user, created only now so that useradd copies the finished /etc/skel into its home.
chroot "${ROOTFS_DIR}" /bin/bash << 'LIVE_USER_EOF'
set -euo pipefail
for group in sudo audio video render input; do groupadd -f "$group"; done
useradd -m -s /bin/bash -G sudo,audio,video,render,input iram
echo "iram:iram" | chpasswd
echo "iram ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/iram
chmod 0440 /etc/sudoers.d/iram
cp /usr/share/iram/system/greetd/live.toml /etc/greetd/config.toml
sed -i 's|__PROJECTS_DIR__|/home/iram/Projects|' /home/iram/.config/mcp/iram_mcp_config.json
LIVE_USER_EOF

# Both tools come from packages a --no-install-recommends build may leave out.
chroot "${ROOTFS_DIR}" /bin/bash -c 'if command -v gtk-update-icon-cache >/dev/null; then gtk-update-icon-cache -f -t /usr/share/icons/hicolor; fi'
chroot "${ROOTFS_DIR}" /bin/bash -c 'if command -v update-desktop-database >/dev/null; then update-desktop-database; fi'

# Copy Wayland session desktop entry
if [ -f "${REPO_ROOT}/system/iram.desktop" ]; then
    cp -a --remove-destination "${REPO_ROOT}/system/iram.desktop" "${ROOTFS_DIR}/usr/share/wayland-sessions/iram.desktop"
fi

# Set custom OS Release Branding
cat << EOF > "${ROOTFS_DIR}/etc/os-release"
NAME="IRAM OS"
VERSION="${DISTRO_VERSION} (${CODENAME})"
ID=iram-os
ID_LIKE="ubuntu debian"
PRETTY_NAME="IRAM OS ${DISTRO_VERSION} (${CODENAME})"
VERSION_ID="${DISTRO_VERSION}"
HOME_URL="https://github.com/apravint/iram-os"
SUPPORT_URL="https://github.com/apravint/iram-os/issues"
BUG_REPORT_URL="https://github.com/apravint/iram-os/issues"
PRIVACY_POLICY_URL="https://github.com/apravint/iram-os"
UBUNTU_CODENAME=${CODENAME}
VERSION_CODENAME=${CODENAME}
BASE_CODENAME=${CODENAME}
EOF

# Remove build-only state so installs do not inherit it.
rm -f "${ROOTFS_DIR}/usr/sbin/policy-rc.d"
ln -sf ../run/systemd/resolve/stub-resolv.conf "${ROOTFS_DIR}/etc/resolv.conf"
: > "${ROOTFS_DIR}/etc/machine-id"
rm -f "${ROOTFS_DIR}/var/lib/dbus/machine-id"

# Without this, casper falls back to its defaults at boot: host "ubuntu", user "ubuntu".
cat << EOF > "${ROOTFS_DIR}/etc/casper.conf"
export USERNAME="iram"
export USERFULLNAME="IRAM Live User"
export HOST="iram"
export BUILD_SYSTEM="Ubuntu"
EOF
printf 'IRAM OS %s \\n \\l\n\n' "${DISTRO_VERSION}" > "${ROOTFS_DIR}/etc/issue"
printf 'IRAM OS %s\n' "${DISTRO_VERSION}" > "${ROOTFS_DIR}/etc/issue.net"
# Bake casper.conf into the initramfs that the ISO boots from.
chroot "${ROOTFS_DIR}" update-initramfs -u

# Copy kernel & initrd into casper directory for ISO booting
log_step "Extracting kernel and initrd for live boot..."
KERNEL_FILE=$(ls -1 "${ROOTFS_DIR}"/boot/vmlinuz* 2>/dev/null | head -n 1)
INITRD_FILE=$(ls -1 "${ROOTFS_DIR}"/boot/initrd.img* 2>/dev/null | head -n 1)

if [ -z "${KERNEL_FILE}" ] || [ -z "${INITRD_FILE}" ]; then
    log_err "Failed to locate kernel or initrd in ${ROOTFS_DIR}/boot"
    ls -la "${ROOTFS_DIR}/boot" || true
    exit 1
fi

log_info "Using kernel: ${KERNEL_FILE}"
log_info "Using initrd: ${INITRD_FILE}"
cp -L "${KERNEL_FILE}" "${ISO_DIR}/casper/vmlinuz"
cp -L "${INITRD_FILE}" "${ISO_DIR}/casper/initrd"

# ------------------------------------------------------------------------------
# 6. Compress Root Filesystem into SquashFS
# ------------------------------------------------------------------------------
log_step "Compressing root filesystem into filesystem.squashfs (this may take a few minutes)..."

# Generate filesystem manifest and size metadata for casper before unmounting
chroot "${ROOTFS_DIR}" dpkg-query -W --showformat='${Package} ${Version}\n' > "${ISO_DIR}/casper/filesystem.manifest"
printf "%s" "$(du -sx --block-size=1 "${ROOTFS_DIR}" | cut -f1)" > "${ISO_DIR}/casper/filesystem.size"

unmount_virtual_filesystems
if [ -n "$(mounts_under_rootfs)" ]; then
    log_err "Virtual filesystems are still mounted; refusing to squash host paths."
    exit 1
fi

case "${SQUASHFS_COMPRESSION}" in
    xz) SQUASHFS_ARGS=(-comp xz -Xbcj x86) ;;
    zstd) SQUASHFS_ARGS=(-comp zstd -Xcompression-level 19) ;;
    *) log_err "SQUASHFS_COMPRESSION must be zstd or xz."; exit 1 ;;
esac
mksquashfs "${ROOTFS_DIR}" "${ISO_DIR}/casper/filesystem.squashfs" "${SQUASHFS_ARGS[@]}" -b 1048576 -noappend

# ------------------------------------------------------------------------------
# 7. Configure GRUB Bootloader for BIOS & UEFI Hybrid Boot
# ------------------------------------------------------------------------------
log_step "Creating GRUB boot menu..."
cat << 'EOF' > "${ISO_DIR}/boot/grub/grub.cfg"
set default="0"
set timeout=5

# Serial console lets CI watch the boot; harmless where no serial port exists.
serial --unit=0 --speed=115200
terminal_input console serial
terminal_output console serial

insmod part_gpt
insmod part_msdos
insmod fat
insmod iso9660
insmod all_video
insmod font

set menu_color_normal=white/black
set menu_color_highlight=black/light-cyan

menuentry "Start IRAM OS Live (Default)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper fsck.mode=skip quiet console=ttyS0,115200 console=tty1 ---
    initrd /casper/initrd
}

menuentry "Start IRAM OS Live (Safe Graphics)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nomodeset fsck.mode=skip quiet console=ttyS0,115200 console=tty1 ---
    initrd /casper/initrd
}

menuentry "Check Disc for Defects" {
    linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
    initrd /casper/initrd
}

menuentry "Reboot System" {
    reboot
}

menuentry "Power Off System" {
    halt
}
EOF

# Generate md5sum.txt inside the ISO root for Casper integrity checks
log_step "Generating ISO root md5sum.txt for Casper media check..."
(cd "${ISO_DIR}" && find . -type f -not -name "md5sum.txt" -not -path "./boot/grub/*" -not -path "./isolinux/*" | sort | xargs md5sum > "${ISO_DIR}/md5sum.txt")

# ------------------------------------------------------------------------------
# 8. Generate Hybrid UEFI/BIOS Bootable ISO
# ------------------------------------------------------------------------------
log_step "Generating hybrid UEFI/BIOS bootable ISO image..."
grub-mkrescue -o "${OUTPUT_DIR}/${ISO_NAME}" "${ISO_DIR}" \
    -- -volid "IRAM"

# ------------------------------------------------------------------------------
# 9. Compute Checksums & Generate Release Notes Template
# ------------------------------------------------------------------------------
log_step "Calculating SHA256 checksum and generating release notes..."
cd "${OUTPUT_DIR}"
sha256sum "${ISO_NAME}" > "sha256sum.txt"

cat << RELEASE_EOF > "${OUTPUT_DIR}/release-notes-${DISTRO_VERSION}.md"
# IRAM OS Release v${DISTRO_VERSION}

**Architecture**: ${ARCH} (x86_64)
**Base**: Ubuntu ${CODENAME}
**Compositor**: Hyprland (from Ubuntu ${CODENAME})
**Theme Suite**: $(find "${REPO_ROOT}/themes" -mindepth 1 -maxdepth 1 -type d | wc -l) palettes

### Checksums
\`\`\`
SHA256: $(cat "${OUTPUT_DIR}/sha256sum.txt")
\`\`\`

### What's New in v${DISTRO_VERSION}
- **Autonomous Self-Healing Watchdog**: Automatic crash recovery and memory monitoring (\`iram-watchdog.service\`).
- **Unified Control Center**: Master GUI/TUI Control Center (\`iram-settings\` / \`Super + I\`).
- **Atomic Config Snapshots**: 1-second desktop state save and instant recovery (\`iram snapshot\`).
- **Voice-to-Action Engine**: Push-to-talk dictation & hands-free desktop agent control (\`iram-voice\` / \`Super + Shift + M\`).
- **Native Creator Studio**: Pipeline piping text into \`shorts-creator\`, \`video-gen\`, and \`BookGeneratorAI\` (\`iram-studio\` / \`Super + Shift + G\`).
- **Zero-Dependency Stdio MCP Server**: Tiered Model Context Protocol server (read, desktop, polkit-gated privileged).
- **Bare-Metal Installer**: \`sudo iram-install-disk\` from the live session; no live-session artifacts on disk.
RELEASE_EOF

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}🎉 ISO Build Completed Successfully!${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "ISO File : ${GREEN}${OUTPUT_DIR}/${ISO_NAME}${NC}"
echo -e "Size     : $(du -h "${OUTPUT_DIR}/${ISO_NAME}" | cut -f1)"
echo -e "Checksum : $(cat "${OUTPUT_DIR}/sha256sum.txt")"
echo -e "${BLUE}======================================================${NC}"
