# 🌐 DistroWatch Official Distribution Submission Application

Use the details below to submit **IRAM OS** to the global Linux registry at **[https://distrowatch.com/dwres.php?resource=submit](https://distrowatch.com/dwres.php?resource=submit)**.

---

### 📋 General Distribution Information

* **Distribution Name**: IRAM OS
* **Distribution Category**: Desktop, Live Medium
* **Based On**: Independent / Debian
* **Origin**: India
* **Default Desktop / Window Manager**: Hyprland (Wayland)
* **Architecture**: x86_64 (64-bit AMD/Intel)
* **Current Status**: Active
* **Release Model**: Rolling Compositor & Theme Updates
* **Initial Release Date**: 2026-10-03
* **Official Homepage**: `https://github.com/apravint/iram-os`
* **Documentation URL**: `https://github.com/apravint/iram-os#readme`
* **Bug Tracker URL**: `https://github.com/apravint/iram-os/issues`

---

### 📦 Download & Verification Links

* **Latest Release Page**: `https://github.com/apravint/iram-os/releases/tag/v26.10.0`
* **Direct ISO Download**: `https://github.com/apravint/iram-os/releases/download/v26.10.0/iram-os-26.10-amd64.iso`
* **SHA256 Checksum URL**: `https://github.com/apravint/iram-os/releases/download/v26.04.0/sha256sum.txt`
* **Live Session Credentials**:
  - **Username**: `iram`
  - **Password**: `iram` *(Passwordless sudo enabled)*

---

### 📝 Short Description (For DistroWatch Catalog)

> **IRAM OS** is a turnkey, 64-bit Linux operating system distribution engineered with an integrated agentic AI stack and the fluid dynamics of the Hyprland Wayland compositor. It ships with out-of-the-box multi-display collision handling, studio-grade PipeWire audio routing, managed systemd user daemons, and a curated 22-theme suite with zero-restart live palette synchronization. Available as a hybrid UEFI/BIOS bootable live ISO image.

---

### 🛠️ Key Technical Innovations (For Reviewers)

1. **Automated Dual-Display Intelligence (`iram-displays-gui`)**:
   - Built-in monitor daemon prevents multi-monitor overlapping at `0x0` coordinates and auto-arranges geometry for secondary screens and 4K TVs.
2. **Production-Grade Daemon Architecture**:
   - Status bar and wallpaper services run as managed systemd units (`waybar.service`, `swaybg.service`) with hardware-readiness polling loops, eliminating fragile background script race conditions.
3. **Studio-Grade PipeWire Audio**:
   - Non-blocking audio output switching (`Super + Shift + A`) with ALSA stereo fallback profiles to prevent HDMI converter stalls.
4. **Zero-Restart Theming Suite**:
   - Dynamic synchronization engine re-tints Hyprland borders, Waybar pills, Wofi launcher, Alacritty terminal, and Mako notifications simultaneously without restarting the desktop session.
5. **Turnkey Live Environment & Installer**:
   - Boots directly from bare metal into an autologin graphical Hyprland desktop session, ready to test or install to SSD/NVMe storage.

---

### 👤 Maintainer Contact Information

* **Maintainer / Founder**: `apravint`
* **Project Repository**: `https://github.com/apravint/iram-os`
* **License**: MIT Open Source License
