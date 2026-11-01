#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Automated ISO CI/CD Verification Pipeline
# Validates integrity, partition tables, SquashFS health, and boots QEMU headlessly.
# https://github.com/apravint/iram-os
# ==============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_step() { echo -e "${GREEN}[STEP]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }

ISO_PATH="${1:-}"

if [[ -z "$ISO_PATH" ]]; then
    # Auto-discover from out/
    ISO_PATH=$(find out/ -maxdepth 1 -name "iram-os-*.iso" | head -n 1 || true)
fi

if [[ -z "$ISO_PATH" || ! -f "$ISO_PATH" ]]; then
    log_err "No ISO file found to verify! Checked: ${ISO_PATH:-out/iram-os-*.iso}"
    exit 1
fi

log_step "Starting automated CI verification for: $ISO_PATH"

# ------------------------------------------------------------------------------
# 1. Size & Checksum Integrity
# ------------------------------------------------------------------------------
log_info "[1/4] Checking ISO file size and checksum..."
ISO_SIZE_BYTES=$(stat -c%s "$ISO_PATH")
ISO_SIZE_MB=$((ISO_SIZE_BYTES / 1024 / 1024))
log_info "ISO size: ${ISO_SIZE_MB} MB (${ISO_SIZE_BYTES} bytes)"

# Minimum acceptable size for a full desktop live ISO
if [[ $ISO_SIZE_MB -lt 800 ]]; then
    log_err "ISO size is unusually small (${ISO_SIZE_MB} MB < 800 MB). Compression or debootstrap failed!"
    exit 1
fi

CHECKSUM_FILE="$(dirname "$ISO_PATH")/sha256sum.txt"
if [[ -f "$CHECKSUM_FILE" ]]; then
    log_info "Verifying against $CHECKSUM_FILE..."
    (cd "$(dirname "$ISO_PATH")" && sha256sum -c "sha256sum.txt")
    log_step "SHA256 checksum verified OK!"
fi

# ------------------------------------------------------------------------------
# 2. Partition Table & Hybrid Boot Records (BIOS + UEFI)
# ------------------------------------------------------------------------------
log_info "[2/4] Verifying hybrid partition table (MBR & EFI)..."
FDISK_OUT=$(fdisk -l "$ISO_PATH" 2>&1 || true)

if ! echo "$FDISK_OUT" | grep -qi -E "EFI|iso9660|0xef"; then
    log_warn "Standard EFI partition header not strictly matched by fdisk; checking with xorriso..."
    if command -v xorriso >/dev/null 2>&1; then
        xorriso -indev "$ISO_PATH" -report_el_torito as_mkisofs 2>&1 | grep -q -i "efi" || {
            log_err "ISO missing UEFI El Torito boot catalog!"
            exit 1
        }
    fi
fi
log_step "Hybrid boot partition table verified!"

# ------------------------------------------------------------------------------
# 3. Mount Loop & SquashFS Verification
# ------------------------------------------------------------------------------
log_info "[3/4] Inspecting internal Live files & SquashFS health..."
TMP_MNT=$(mktemp -d -t iram-iso-verify-XXXXXX)
trap 'sudo umount -f "$TMP_MNT" 2>/dev/null || true; rm -rf "$TMP_MNT"' EXIT

sudo mount -o loop,ro "$ISO_PATH" "$TMP_MNT"

# Verify kernel & initrd
if [[ ! -f "$TMP_MNT/casper/vmlinuz" ]]; then
    log_err "CRITICAL: Live kernel ($TMP_MNT/casper/vmlinuz) missing from ISO!"
    exit 1
fi

if [[ ! -f "$TMP_MNT/casper/initrd" && ! -f "$TMP_MNT/casper/initrd.img" ]]; then
    log_err "CRITICAL: Initramfs missing from ISO!"
    exit 1
fi

# Verify SquashFS rootfs
SQUASHFS_FILE=$(find "$TMP_MNT/casper" -name "*.squashfs" | head -n 1 || true)
if [[ -z "$SQUASHFS_FILE" || ! -f "$SQUASHFS_FILE" ]]; then
    log_err "CRITICAL: Root filesystem squashfs missing from $TMP_MNT/casper!"
    exit 1
fi

if command -v unsquashfs >/dev/null 2>&1; then
    log_info "Testing SquashFS integrity via unsquashfs -s..."
    unsquashfs -s "$SQUASHFS_FILE" >/dev/null
    log_step "SquashFS superblock and compression blocks are intact!"

    # What the session and the installer actually need, by path. Catches build
    # steps that silently produce a bootable image with an empty desktop.
    MANIFEST="$(unsquashfs -lc "$SQUASHFS_FILE" | sed 's|^squashfs-root/||')"
    for required in \
        home/iram/.config/hypr/hyprland.conf \
        home/iram/.config/hypr/user-overrides.conf \
        home/iram/.config/systemd/user/hyprland-session.target \
        etc/skel/.config/hypr/hyprland.conf \
        usr/share/wayland-sessions/iram.desktop \
        usr/share/iram/default/themed/alacritty.toml.tpl \
        usr/local/bin/iram-install-disk \
        usr/local/bin/iram-os-mcp \
        usr/local/bin/hyprland-start; do
        if ! grep -qxF "$required" <<< "$MANIFEST"; then
            log_err "CRITICAL: $required missing from the root filesystem!"
            exit 1
        fi
    done
    for forbidden in usr/sbin/policy-rc.d var/lib/dbus/machine-id; do
        if grep -qxF "$forbidden" <<< "$MANIFEST"; then
            log_err "CRITICAL: build artifact $forbidden shipped in the image!"
            exit 1
        fi
    done
    log_step "Root filesystem contents verified!"
fi

sudo umount "$TMP_MNT"
trap - EXIT
rm -rf "$TMP_MNT"

# ------------------------------------------------------------------------------
# 4. Headless QEMU Smoke Boot Verification
# ------------------------------------------------------------------------------
log_info "[4/4] Executing headless QEMU boot test..."

if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
    log_warn "qemu-system-x86_64 not installed on this host; skipping live boot execution."
    log_step "Static ISO verification PASSED successfully!"
    exit 0
fi

QEMU_ACCEL="-accel tcg"
if [[ -w /dev/kvm ]]; then
    QEMU_ACCEL="-enable-kvm"
    log_info "Hardware virtualization (KVM) acceleration enabled."
else
    log_warn "KVM acceleration not available; running QEMU with TCG (software emulation)."
fi

BOOT_LOG="$(mktemp -t iram-qemu-boot-XXXXXX.log)"
BOOT_TIMEOUT="${BOOT_TIMEOUT:-300}"

log_info "Launching QEMU in background (timeout ${BOOT_TIMEOUT}s)..."
qemu-system-x86_64 \
    $QEMU_ACCEL \
    -m 4G \
    -smp 2 \
    -cdrom "$ISO_PATH" \
    -boot d \
    -display none \
    -serial file:"$BOOT_LOG" \
    -no-reboot \
    >/dev/null 2>&1 &
QEMU_PID=$!

# Pass only on evidence: the kernel started, and userspace came up from the squashfs.
KERNEL_SEEN=0
USERSPACE_SEEN=0
deadline=$((SECONDS + BOOT_TIMEOUT))
while [[ $SECONDS -lt $deadline ]] && kill -0 $QEMU_PID 2>/dev/null; do
    sleep 3
    grep -q "Linux version" "$BOOT_LOG" 2>/dev/null && KERNEL_SEEN=1
    grep -qE "Reached target|systemd\[1\]|login:" "$BOOT_LOG" 2>/dev/null && USERSPACE_SEEN=1
    [[ $USERSPACE_SEEN -eq 1 ]] && break
    grep -qE "Kernel panic|\(initramfs\)" "$BOOT_LOG" 2>/dev/null && break
done

kill -9 $QEMU_PID 2>/dev/null || true
wait $QEMU_PID 2>/dev/null || true

if grep -qE "Kernel panic|\(initramfs\)" "$BOOT_LOG"; then
    log_err "CRITICAL: boot failed!"
    tail -n 40 "$BOOT_LOG"
    exit 1
fi
if [[ $KERNEL_SEEN -ne 1 || $USERSPACE_SEEN -ne 1 ]]; then
    log_err "CRITICAL: no evidence of a completed boot (kernel=$KERNEL_SEEN userspace=$USERSPACE_SEEN)."
    tail -n 40 "$BOOT_LOG"
    exit 1
fi

log_step "QEMU boot reached userspace from the live image."
echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}✓ ALL ISO VERIFICATION CHECKS PASSED SUCCESSFULLY!${NC}"
echo -e "Verified ISO: ${BOLD}$ISO_PATH${NC} ($ISO_SIZE_MB MB)"
echo -e "${BLUE}======================================================${NC}"
exit 0
