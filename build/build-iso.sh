#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Automated Live ISO Builder
# Builds a bootable hybrid UEFI/BIOS Live ISO for IRAM OS
# ==============================================================================
set -euo pipefail

# Target base release version: defaults to 26.04 (Resolute) or respects environment override
CODENAME="${BASE_CODENAME:-resolute}"
DISTRO_VERSION="${DISTRO_VERSION:-26.04}"
DISTRO_NAME="iram-os"
ARCH="amd64"
ROOTFS_DIR="/tmp/iram-rootfs"
ISO_DIR="/tmp/iram-iso"
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
log_step "Cleaning old build directories..."
umount -lf "${ROOTFS_DIR}/dev/pts" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/dev" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/proc" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/sys" 2>/dev/null || true
rm -rf "${ROOTFS_DIR}" "${ISO_DIR}" "${OUTPUT_DIR}"
mkdir -p "${ROOTFS_DIR}" "${ISO_DIR}/casper" "${ISO_DIR}/boot/grub" "${OUTPUT_DIR}"

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

# Ensure cleanup on trap
cleanup() {
    log_info "Cleaning up mounted virtual filesystems..."
    umount -lf "${ROOTFS_DIR}/dev/pts" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/dev" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/proc" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/sys" 2>/dev/null || true
}
trap cleanup EXIT

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
chroot "${ROOTFS_DIR}" /bin/bash -s "${CODENAME}" "${DISTRO_VERSION}" << 'CHROOT_EOF'
set -euo pipefail
CODENAME="$1"
DISTRO_VERSION="$2"
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
    curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xA54D23B62FF3FCC76EFF71E8FDBAAA1CF0CCF48E" | gpg --dearmor -o /etc/apt/keyrings/cppiber-hyprland.gpg 2>/dev/null || true
    echo "deb [signed-by=/etc/apt/keyrings/cppiber-hyprland.gpg] https://ppa.launchpadcontent.net/cppiber/hyprland/ubuntu ${CODENAME} main" > /etc/apt/sources.list.d/cppiber-hyprland.list
    apt-get update -y || true
fi

# Kernel & Live Boot Essentials
apt-get install -y --no-install-recommends \
    linux-generic \
    initramfs-tools \
    casper \
    discover \
    laptop-detect \
    os-prober \
    network-manager \
    net-tools \
    iw \
    wpasupplicant \
    sudo \
    curl \
    git \
    wget \
    nano \
    vim

# Audio, Bluetooth & Display Server
apt-get install -y --no-install-recommends \
    pipewire \
    wireplumber \
    pipewire-pulse \
    pipewire-alsa \
    libspa-0.2-bluetooth \
    bluez \
    blueman \
    pavucontrol \
    sddm

# Hyprland & Wayland Desktop Stack
apt-get install -y \
    hyprland \
    xdg-desktop-portal-hyprland \
    waybar \
    swaybg \
    swaylock \
    mako-notifier \
    wofi \
    alacritty \
    grim \
    slurp \
    wl-clipboard \
    cliphist \
    playerctl \
    wf-recorder \
    hyprpicker \
    tesseract-ocr \
    wlsunset \
    network-manager-gnome \
    polkit-kde-agent-1 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-3.0 \
    ripgrep \
    fd-find \
    tmux \
    fzf \
    zoxide \
    eza \
    bat \
    gawk \
    socat \
    fonts-jetbrains-mono \
    fonts-font-awesome \
    btop \
    jq || true

# Install Ollama & OpenClaw Agentic OS Stack inside ISO
curl -fsSL https://ollama.com/install.sh | sh || true
pip3 install --break-system-packages openclaw edge-tts ddgs || pip3 install openclaw edge-tts ddgs || true

# Setup IRAM OS system core directory
mkdir -p /usr/share/iram

# Setup default live user: 'iram' with passwordless sudo
mkdir -p /etc/sudoers.d
groupadd -f sudo
groupadd -f audio
groupadd -f video

useradd -m -s /bin/bash -G sudo,audio,video iram || true
echo "iram:iram" | chpasswd || true
echo "iram ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/iram
chmod 0440 /etc/sudoers.d/iram

# Autologin into Iram Hyprland session via SDDM
mkdir -p /etc/sddm.conf.d
cat << 'AUTOLOGIN_EOF' > /etc/sddm.conf.d/autologin.conf
[Autologin]
User=iram
Session=iram.desktop
AUTOLOGIN_EOF

# Enable essential systemd services
systemctl enable NetworkManager.service 2>/dev/null || true
systemctl enable bluetooth.service 2>/dev/null || true
systemctl enable sddm.service 2>/dev/null || true

# Clean apt cache and docs to ensure ISO size stays well under GitHub 2GB release limit
apt-get autoremove -y --purge
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/* /usr/share/doc/* /usr/share/man/* /usr/share/info/*
CHROOT_EOF

# ------------------------------------------------------------------------------
# 5. Inject Iram Desktop Configurations & Scripts
# ------------------------------------------------------------------------------
log_step "Injecting Iram scripts, systemd units, and skeleton user configs..."

# Copy IRAM OS sovereign system files into /usr/share/iram
mkdir -p "${ROOTFS_DIR}/usr/share/iram"
cp -a --remove-destination "${REPO_ROOT}/bin" "${REPO_ROOT}/config" "${REPO_ROOT}/themes" "${REPO_ROOT}/system" "${REPO_ROOT}/migrations" "${ROOTFS_DIR}/usr/share/iram/"
if [ -d "${REPO_ROOT}/assets" ]; then cp -a --remove-destination "${REPO_ROOT}/assets" "${ROOTFS_DIR}/usr/share/iram/"; fi
if [ -d "${REPO_ROOT}/applications" ]; then cp -a --remove-destination "${REPO_ROOT}/applications" "${ROOTFS_DIR}/usr/share/iram/"; fi

# Copy IRAM system-wide binaries & profile
mkdir -p "${ROOTFS_DIR}/usr/local/bin" "${ROOTFS_DIR}/usr/bin" "${ROOTFS_DIR}/usr/share/wayland-sessions" "${ROOTFS_DIR}/etc/profile.d"
cp -a --remove-destination "${REPO_ROOT}/bin/"* "${ROOTFS_DIR}/usr/local/bin/"
find "${ROOTFS_DIR}/usr/local/bin/" -type f -exec chmod 0755 {} + 2>/dev/null || true

# Symlink all iram binaries into /usr/bin
chroot "${ROOTFS_DIR}" /bin/bash << 'POST_CHROOT_EOF'
for bin_file in /usr/local/bin/iram* /usr/local/bin/craft*; do
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

# Copy skeleton configs so every user (and live user) gets them
mkdir -p "${ROOTFS_DIR}/etc/skel/.config" "${ROOTFS_DIR}/etc/skel/.local/bin" "${ROOTFS_DIR}/etc/skel/.local/share/applications" "${ROOTFS_DIR}/etc/skel/.local/share/icons/hicolor/128x128/apps"
cp -a --remove-destination "${REPO_ROOT}/config/"* "${ROOTFS_DIR}/etc/skel/.config/"
cp -a --remove-destination "${REPO_ROOT}/bin/"* "${ROOTFS_DIR}/etc/skel/.local/bin/"
cp -a --remove-destination "${REPO_ROOT}/applications/"*.desktop "${ROOTFS_DIR}/etc/skel/.local/share/applications/" 2>/dev/null || true
cp -a --remove-destination "${REPO_ROOT}/applications/icons/"*.png "${ROOTFS_DIR}/etc/skel/.local/share/icons/hicolor/128x128/apps/" 2>/dev/null || true

# Also copy into the live user's home directly
mkdir -p "${ROOTFS_DIR}/home/iram/.config" "${ROOTFS_DIR}/home/iram/.local/bin" "${ROOTFS_DIR}/home/iram/.local/share/applications" "${ROOTFS_DIR}/home/iram/.local/share/icons/hicolor/128x128/apps"
cp -a --remove-destination "${REPO_ROOT}/config/"* "${ROOTFS_DIR}/home/iram/.config/"
cp -a --remove-destination "${REPO_ROOT}/bin/"* "${ROOTFS_DIR}/home/iram/.local/bin/"
cp -a --remove-destination "${REPO_ROOT}/applications/"*.desktop "${ROOTFS_DIR}/home/iram/.local/share/applications/" 2>/dev/null || true
cp -a --remove-destination "${REPO_ROOT}/applications/icons/"*.png "${ROOTFS_DIR}/home/iram/.local/share/icons/hicolor/128x128/apps/" 2>/dev/null || true

# Copy systemd units
mkdir -p "${ROOTFS_DIR}/etc/skel/.config/systemd/user" "${ROOTFS_DIR}/home/iram/.config/systemd/user"
cp -a --remove-destination "${REPO_ROOT}/config/systemd/user/"* "${ROOTFS_DIR}/etc/skel/.config/systemd/user/" 2>/dev/null || true
cp -a --remove-destination "${REPO_ROOT}/config/systemd/user/"* "${ROOTFS_DIR}/home/iram/.config/systemd/user/" 2>/dev/null || true

# Fix permissions
chroot "${ROOTFS_DIR}" chown -R iram:iram /home/iram 2>/dev/null || true
chroot "${ROOTFS_DIR}" gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
chroot "${ROOTFS_DIR}" update-desktop-database 2>/dev/null || true

# Copy Wayland session desktop entry
if [ -f "${REPO_ROOT}/system/iram.desktop" ]; then
    cp -a --remove-destination "${REPO_ROOT}/system/iram.desktop" "${ROOTFS_DIR}/usr/share/wayland-sessions/iram.desktop"
fi

# Set custom OS Release Branding
cat << EOF > "${ROOTFS_DIR}/etc/os-release"
NAME="IRAM OS"
VERSION="${DISTRO_VERSION} (${CODENAME})"
ID=iram-os
ID_LIKE="debian"
PRETTY_NAME="IRAM OS ${DISTRO_VERSION} (${CODENAME})"
VERSION_ID="${DISTRO_VERSION}"
HOME_URL="https://github.com/apravint/iram-os"
SUPPORT_URL="https://github.com/apravint/iram-os/issues"
BUG_REPORT_URL="https://github.com/apravint/iram-os/issues"
PRIVACY_POLICY_URL="https://github.com/apravint/iram-os"
BASE_CODENAME=${CODENAME}
EOF

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
chroot "${ROOTFS_DIR}" dpkg-query -W --showformat='${Package} ${Version}\n' > "${ISO_DIR}/casper/filesystem.manifest" 2>/dev/null || true
printf $(du -sx --block-size=1 "${ROOTFS_DIR}" | cut -f1) > "${ISO_DIR}/casper/filesystem.size"

# Unmount virtual mounts before squashing
umount -lf "${ROOTFS_DIR}/dev/pts" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/dev" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/proc" 2>/dev/null || true
umount -lf "${ROOTFS_DIR}/sys" 2>/dev/null || true

mksquashfs "${ROOTFS_DIR}" "${ISO_DIR}/casper/filesystem.squashfs" \
    -comp xz -b 1048576 -Xbcj x86 -processors 4

# ------------------------------------------------------------------------------
# 7. Configure GRUB Bootloader for BIOS & UEFI Hybrid Boot
# ------------------------------------------------------------------------------
log_step "Creating GRUB boot menu..."
cat << 'EOF' > "${ISO_DIR}/boot/grub/grub.cfg"
set default="0"
set timeout=5

insmod part_gpt
insmod part_msdos
insmod fat
insmod iso9660
insmod all_video
insmod font

set menu_color_normal=white/black
set menu_color_highlight=black/light-cyan

menuentry "🚀 Start IRAM OS Live (Default)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper fsck.mode=skip quiet splash ---
    initrd /casper/initrd
}

menuentry "🛡️ Start IRAM OS Live (Safe Graphics)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nomodeset fsck.mode=skip quiet splash ---
    initrd /casper/initrd
}

menuentry "🔍 Check Disc for Defects" {
    linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
    initrd /casper/initrd
}

menuentry "⚡ Reboot System" {
    reboot
}

menuentry "⏻ Power Off System" {
    halt
}
EOF

# Generate md5sum.txt inside the ISO root for Casper integrity checks
log_step "Generating ISO root md5sum.txt for Casper media check..."
(cd "${ISO_DIR}" && find . -type f -not -name "md5sum.txt" -not -path "./boot/grub/*" -not -path "./isolinux/*" | sort | xargs md5sum > "${ISO_DIR}/md5sum.txt" 2>/dev/null || true)

# ------------------------------------------------------------------------------
# 8. Generate Hybrid UEFI/BIOS Bootable ISO
# ------------------------------------------------------------------------------
log_step "Generating hybrid UEFI/BIOS bootable ISO image..."
grub-mkrescue -o "${OUTPUT_DIR}/${ISO_NAME}" "${ISO_DIR}" \
    -- -volid "IRAM"

# ------------------------------------------------------------------------------
# 9. Compute Checksums & Finish
# ------------------------------------------------------------------------------
log_step "Calculating SHA256 checksum..."
cd "${OUTPUT_DIR}"
sha256sum "${ISO_NAME}" > "sha256sum.txt"

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}🎉 ISO Build Completed Successfully!${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "ISO File : ${GREEN}${OUTPUT_DIR}/${ISO_NAME}${NC}"
echo -e "Size     : $(du -h "${OUTPUT_DIR}/${ISO_NAME}" | cut -f1)"
echo -e "Checksum : $(cat "${OUTPUT_DIR}/sha256sum.txt")"
echo -e "${BLUE}======================================================${NC}"
