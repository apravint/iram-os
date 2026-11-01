<div align="center">

# IRAM OS 🌌

### The Sovereign Autonomous Agentic Desktop Operating System (v26.04.2)

A high-performance Linux operating system powered by Hyprland, featuring sharp geometric tiling, zero-restart live theme switching across 22+ curated palettes, studio-grade PipeWire audio routing, automated multi-display intelligence, autonomous self-healing watchdog supervision, atomic 1-second configuration snapshots, native creator studio pipelines, push-to-talk voice-to-action, zero-config native stdio Model Context Protocol (MCP) server, and a deeply integrated autonomous AI runtime.

[![GitHub Release](https://img.shields.io/github/v/release/apravint/iram-os?color=7aa2f7&logo=github&label=Release)](https://github.com/apravint/iram-os/releases)
[![Version: v26.04.2](https://img.shields.io/badge/Version-v26.04.2-00f0ff.svg)](https://github.com/apravint/iram-os/releases/tag/v26.04.2)
[![Base: Ubuntu 26.10](https://img.shields.io/badge/Base-Ubuntu%2026.10%20Stonking-E95420.svg?logo=ubuntu&logoColor=white)](https://releases.ubuntu.com)
[![Compositor: Hyprland 0.56](https://img.shields.io/badge/Compositor-Hyprland%200.56-00c853.svg?logo=wayland&logoColor=white)](https://hyprland.org)
[![Themes: 22+ Live Palettes](https://img.shields.io/badge/Themes-22%2B%20Live%20Palettes-ff007f.svg)](#-zero-restart-theming-engine-22-palettes)
[![MCP: Native stdio JSON-RPC](https://img.shields.io/badge/MCP-Native%20stdio%20Server-blueviolet.svg)](https://modelcontextprotocol.io)
[![Audio: PipeWire Studio](https://img.shields.io/badge/Audio-PipeWire%20Studio-brightgreen.svg)](https://pipewire.org)
[![CI Gate: Quality & Syntax](https://github.com/apravint/iram-os/actions/workflows/ci.yml/badge.svg)](https://github.com/apravint/iram-os/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<br/>

### 📸 Desktop Visual Showcase

<p align="center">
  <img src="assets/iram-os-workspaces-tour.gif" alt="IRAM OS Multi-Workspace Desktop Tour & Live Dynamic Themes" width="100%" />
  <br/>
  <em>Live 15-second multi-workspace showcase: Fastfetch System Card (WS 4) ➔ btop Resource Dashboard (WS 5) ➔ CAVA Audio Spectrum (WS 6) ➔ Telemetry HUD (WS 7) ➔ 2x2 Flagship Quad Grid (WS 8) ➔ Neovim Dev Rice (WS 9) ➔ Dynamic Wallpaper & Waybar Live Theme Sync (WS 10).</em>
  <br/>
  <b><a href="assets/iram-os-workspaces-tour.mp4">▶ Download / View Full 1080p MP4 Video (assets/iram-os-workspaces-tour.mp4)</a></b>
</p>

<br/>

<table>
  <tr>
    <td width="50%">
      <img src="assets/screenshots/3d_agent_swarm.png" alt="3D Agent Swarm Graph" width="100%" />
      <p align="center"><b>3D Multi-Agent Swarm Topology (Three.js WebGL)</b><br/><code>iram agent graph</code></p>
    </td>
    <td width="50%">
      <img src="assets/screenshots/3d_cad_inspector.png" alt="3D CAD Mesh Inspector" width="100%" />
      <p align="center"><b>Hardware CAD & Biomolecule Inspector</b><br/><code>iram 3d &lt;model.stl&gt;</code></p>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <img src="assets/screenshots/theme_switcher.png" alt="Zero-Restart Theme Switcher" width="100%" />
      <p align="center"><b>Zero-Restart Theme Switcher (22+ Curated Palettes & Live Preview Grid)</b><br/><code>iram theme</code> or <code>Super + Alt + T</code></p>
    </td>
  </tr>
</table>

</div>

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph UserSpace["User Interaction & AI Layer"]
        CLI["iram CLI Manager<br/>(settings, snapshot, watchdog, update, doctor, theme)"]
        Control["Control Center (Super+I)<br/>iram-settings GUI/TUI Hub"]
        Voice["Voice-to-Action (Super+Shift+M)<br/>iram-voice + PipeWire Push-to-Talk"]
        Studio["Creator Studio (Super+Shift+G)<br/>shorts-creator + video-gen + BookGen"]
        Scratchpad["AI Floating Scratchpad (Super+`)<br/>Alacritty iram-agy-float"]
        Vision["Screen Vision OCR (Super+Shift+V)<br/>grim + slurp + tesseract"]
        Prompt["AI Prompt Bar (Super+Shift+Space)<br/>Wofi + Clipboard Context"]
    end

    subgraph DesktopShell["Wayland Desktop Environment"]
        Hypr["Hyprland 0.56 Compositor<br/>0px Sharp Geometry & Acrylic Blur"]
        Waybar["Waybar HUD<br/>Dynamic Theme Colors + custom/iram-ai Pill"]
        Lock["Dynamic Hyprlock (Super+L)<br/>Themed Lockscreen + Swaybg"]
        Idle["Hypridle Daemon<br/>Dim (5m) -> Lock (10m) -> DPMS (15m)"]
        Clip["cliphist (Super+V)<br/>Wayland Clipboard History Manager"]
        Snapshot["iram snapshot<br/>Atomic Config Archives & 1s Rollback"]
    end

    subgraph NativeMCP["Native stdio MCP Subsystem"]
        MCPServer["mcp/iram-os-mcp (Python 3 stdio)<br/>Zero-config JSON-RPC 2.0 Engine"]
        T1["switch_theme(name)"]
        T2["manage_windows(action, ws)"]
        T3["service_diagnostics(unit, action)"]
        T4["audio_display_control(target, cmd)"]
        T5["system_telemetry()"]
        T6["watchdog_report(lines)"]
        MCPServer --> T1
        MCPServer --> T2
        MCPServer --> T3
        MCPServer --> T4
        MCPServer --> T5
        MCPServer --> T6
    end

    subgraph SystemCore["Kernel, PipeWire & Services"]
        Watchdog["iram-watchdog.service<br/>Autonomous Self-Healing Supervisor"]
        Systemd["systemd User Units<br/>(waybar, swaybg, hypridle, cliphist)"]
        PipeWire["PipeWire Audio Studio<br/>HDMI / DSP Priority Routing"]
        Ollama["Ollama LLM Engine<br/>Local GPU / CPU Inference"]
        Net["linux-dual-wifi<br/>Layer 4 ECMP Multi-WAN Balancer"]
        Watchdog --> Systemd
    end

    UserSpace --> DesktopShell
    UserSpace --> NativeMCP
    DesktopShell --> SystemCore
    NativeMCP --> DesktopShell
    NativeMCP --> SystemCore
```

---

## ⚖️ Why IRAM OS? Comparison Matrix

| Feature | IRAM OS (v26.04.2) | Vanilla Ubuntu 24.04/26.10 | Arch Linux / Hyprland | Omarchy (Upstream) | macOS Sequoia |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Compositor Engine** | Hyprland 0.56 (Sharp Edges) | GNOME Shell (Mutter) | Manual User Config | Hyprland (Rounded) | Quartz Compositor |
| **Out-of-the-Box Zero Config** | ✅ Turnkey (`install.sh` / ISO) | ✅ Turnkey (GNOME) | ❌ Manual Rice (Days) | ⚠️ Distro-specific | ✅ Turnkey |
| **Self-Healing Watchdog** | ✅ `iram-watchdog.service` | ❌ None | ❌ Manual scripts | ❌ None | ⚠️ launchd recovery |
| **Unified Control Center** | ✅ `iram-settings` (`Super + I`) | ⚠️ GNOME Control Center | ❌ None | ❌ Fragmented scripts | ✅ macOS Settings |
| **Atomic 1s Snapshots** | ✅ `iram snapshot` (zstd) | ❌ Manual Timeshift | ❌ Manual btrfs | ❌ None | ⚠️ Time Machine (Slow) |
| **Push-to-Talk Voice-to-Action** | ✅ `iram-voice` (`Super + Shift + M`) | ❌ None | ❌ None | ❌ None | ⚠️ Siri (Cloud) |
| **Native Creator Studio** | ✅ `iram-studio` (`Super + Shift + G`) | ❌ None | ❌ None | ❌ None | ❌ None |
| **Native stdio MCP Server** | ✅ `iram-os-mcp` (Zero pip deps) | ❌ None | ❌ None | ❌ None | ❌ None |
| **AI Scratchpad (`Super + \``)** | ✅ Built-in (`iram-agy-float`) | ❌ None | ❌ Manual bind | ❌ None | ❌ None |
| **Screen Vision OCR (`Super + Shift + V`)** | ✅ Built-in (tesseract + AI) | ❌ None | ❌ Manual script | ❌ None | ⚠️ Apple Intelligence |
| **Zero-Restart Theming** | ✅ 22+ Sovereign Palettes | ❌ Requires Log out | ❌ Script hacking | ⚠️ Limited Palettes | ❌ Light / Dark only |
| **Non-Destructive Overrides** | ✅ `user-overrides.conf` | ❌ Overwritten on upgrades | ❌ Manual backups | ❌ Overwrites config | ❌ Locked down |
| **System Diagnostics Doctor** | ✅ `iram doctor` (Table HUD) | ❌ None | ❌ None | ⚠️ Minimal check | ❌ None |
| **Audio Routing Reliability** | ✅ PipeWire + Auto-HDMI/DSP | ⚠️ Standard Pulse/Pipe | ⚠️ Manual pactl | ⚠️ Standard rules | ✅ CoreAudio |
| **RAM Footprint (Idle)** | **~750 MB** | ~1.8 GB | ~600 MB | ~1.2 GB | ~3.5 GB |

---

## 🛠️ The Unified `iram` CLI Management Utility

All system administration, theming, AI configuration, and diagnostics are controlled via the `iram` executable:

```bash
iram <command> [subcommand] [arguments...]
```

### Core Management Subcommands:

| Command | Action & Behavior |
| :--- | :--- |
| `iram settings` | Master GUI/TUI Control Center (`Super + I` or Waybar OS icon) for Theme Studio, Displays, Audio, AI Hub, Creator Studio, and Snapshots. |
| `iram snapshot [cmd]` | Atomic configuration snapshot management (`create [label]`, `list`, `restore`, `auto`). Saves/restores core desktop configs in 1 second. |
| `iram watchdog [cmd]` | Autonomous self-healing supervisor (`daemon`, `--once`, `status/logs`). Auto-restarts failed desktop services and detects memory pressure. |
| `iram update` | Automatically backs up configs to an atomic snapshot, pulls latest commits from `apravint/iram-os`, runs `install.sh`, reloads systemd user units, restarts desktop daemons, and reloads Hyprland. |
| `iram doctor` | Verifies Wayland session variables, XDG portals, `hyprctl` responsiveness, systemd user services (`waybar`, `swaybg`, `hypridle`, `iram-cliphist`, `iram-watchdog`), PipeWire audio sinks, and `agy`/`ollama`/MCP status, printing an instant PASS/FAIL scorecard table. |
| `iram theme [name]` | Lists all 22 sovereign themes or switches the active theme live with zero compositor restart (`iram theme "Tokyo Storm"`, `iram theme random`, or `iram theme list`). |
| `iram ai-setup` | Auto-detects acceleration hardware (`nvidia-smi` VRAM, `rocm-smi`, or CPU fallback), ensures `ollama` is installed, and pulls the optimal coding model (`qwen2.5-coder:7b` for GPUs $\ge 6\text{GB}$, or `llama3.2:3b` for CPUs/laptops). |
| `iram apps` | Interactive Wofi / terminal installer that clones, sets up, and configures flagship tools (`apravint/video-gen`, `apravint/shorts-creator`, `apravint/BookGeneratorAI`) into `~/Projects/`. |
| `iram mcp-config [--inject]` | Outputs standard MCP configuration JSON or automatically injects the `iram-os-mcp` stdio server entry into `~/.gemini/settings.json`, Antigravity CLI, and Claude configurations. |
| `iram info` | Prints active compositor, Linux kernel, distribution, theme name, and AI agent status HUD. |

---

## 🔌 Native `iram-os-mcp` System Control Server

IRAM OS includes a zero-config, pure Python 3 standard-library Model Context Protocol (MCP) server located at `mcp/iram-os-mcp` (installed to `/usr/local/bin/iram-os-mcp` and `~/.local/bin/iram-os-mcp`). It communicates via standard JSON-RPC 2.0 stdio without requiring external pip packages.

### Exposing 6 Native Tools to AI Coding Agents:

1. **`switch_theme(theme_name)`**: Lists all 22 sovereign palettes or immediately switches Hyprland, Waybar, Wofi, Mako, and Swaybg to the requested palette live.
2. **`manage_windows(action, workspace, window_address)`**: Inspects active windows (`list`), moves windows across workspaces (`movetoworkspace`), toggles floating mode (`togglefloating`), triggers fullscreen (`fullscreen`), focuses windows (`focus`), or closes windows (`close`).
3. **`service_diagnostics(unit_name, action)`**: Reads `systemctl --user status`, inspects `journalctl -u <unit> -n 40` logs, and restarts failed desktop daemons.
4. **`audio_display_control(target, command)`**: Interfaces with PipeWire audio sinks (listing sinks, cycling outputs, toggling mute, adjusting volume) and queries connected display monitors.
5. **`system_telemetry()`**: Returns CPU usage, RAM utilization, GPU VRAM allocation, disk space, and failed systemd units in structured JSON.
6. **`watchdog_report(lines)`**: Inspects the autonomous self-healing supervisor log, recent crash recoveries, and resource pressure warnings.

---

## ⌨️ Master Keyboard Shortcuts

### 🤖 AI Agent & Productivity Hotkeys
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Super + I` | **Unified Control Center** | Master GUI/TUI Control Center (`iram-settings`) for Themes, Displays, Audio & AI |
| `Super + Shift + M` | **Voice-to-Action** | Push-to-talk PipeWire dictation & hands-free desktop AI agent control |
| `Super + Shift + G` | **Creator Studio** | Pipe highlighted text/scripts directly into `shorts-creator`, `video-gen`, or `BookGeneratorAI` |
| `Super + \`` (Grave) | **AI Scratchpad** | Toggle floating Alacritty window running Google Antigravity (`agy`) |
| `Super + Shift + Space` | **AI Prompt Bar** | Prompt via Wofi with automatic Wayland clipboard context injection |
| `Super + Shift + V` | **Screen Vision & OCR** | Snip a screen region with `grim` + `slurp` to copy text or debug errors with AI |
| `Super + V` | **Clipboard History** | Fuzzy search clipboard entries via `cliphist` + `wofi` and copy to clipboard |
| `Super + L` | **Lock Screen** | Lock display immediately using dynamic themed `hyprlock` |
| `Super + Alt + T` / `Super + T` | **Theme Switcher** | Open visual 22-palette theme picker GUI |
| `Super + Shift + W` | **Cycle Wallpaper** | Rotate wallpaper within current theme's curated backgrounds |

### 🪟 Window Navigation & Workspaces
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Super + Space` | **Application Launcher** | Open Wofi application launcher |
| `Super + Return` | **Terminal** | Open fast GPU-accelerated Alacritty terminal |
| `Super + Q` / `Super + W` | **Close Window** | Close active focused window |
| `Super + Alt + V` | **Toggle Floating** | Toggle focused window between dynamic tiling and floating mode |
| `Super + F` | **Fullscreen** | Toggle borderless fullscreen |
| `Super + O` | **Pin Window** | Pin floating window across all workspaces (Picture-in-Picture) |
| `Super + S` | **Scratchpad Workspace** | Toggle drop-down special scratchpad workspace |
| `Super + 1` .. `Super + 0` | **Switch Workspace** | Switch to workspaces 1 through 10 |
| `Super + Shift + 1..0` | **Move Window** | Move active window to workspace 1 through 10 |
| `Super + Left/Right/Up/Down` | **Focus Direction** | Move focus between tiled windows |
| `Super + Escape` | **Power Menu** | Power menu (Lock, Suspend, Logout, Reboot, Shutdown) |

---

## 🎨 Zero-Restart Theming Engine (22 Sovereign Palettes)

Switching themes via `iram theme set <name>` or `Super + Alt + T` live-reloads Hyprland border gradients, Waybar styles, Wofi palettes, Mako notifications, and lockscreen colors simultaneously:

```
Tokyo Night          Tokyo Storm          Cyberpunk Neon       Synthwave '84
Catppuccin Mocha     Catppuccin Latte     Everforest           Rose Pine
Rose Pine Moon       Nord Frost           Dracula              Gruvbox
Kanagawa Wave        One Dark             Monokai Pro          Oxocarbon
Aura Dark            Ayu Mirage           Vantablack           Matte Black
Solarized Dark       Flexoki Light
```

---

## 🚀 Installation & Upgrades

### Fresh Installation

```bash
# Clone the repository
git clone https://github.com/apravint/iram-os.git
cd iram-os

# Execute installer
chmod +x install.sh
./install.sh all
```

### Upgrading an Existing System

Upgrades are 100% non-destructive. Custom keybinds and window rules inside `~/.config/hypr/user-overrides.conf` are strictly preserved:

```bash
iram update
```

### System Health Verification

```bash
iram doctor
```

---

## ⚖️ License & Trademarks

This project is licensed under the **[MIT License](LICENSE)**.

- **IRAM OS**: Independent open-source desktop operating system developed and maintained by Ayyappa Pravin.
- **Ubuntu**: Ubuntu is a registered trademark of Canonical Ltd. IRAM OS is an independent project and is not affiliated with, sponsored by, or endorsed by Canonical Ltd.
- **Hyprland, Waybar, PipeWire**: Trademarks belong to their respective creators.
