---
name: iram-os
description: Authoritative guide and system reference for IRAM OS (Ubuntu 26.04 LTS + Hyprland + Waybar + Storytold Craft Suite + Agentic OS). Use to manage, troubleshoot, or configure IRAM OS.
---

# IRAM OS Agentic Operating System

IRAM OS is a high-performance, beautiful, and agentic Linux distribution built on Ubuntu 26.04 LTS and Hyprland, tailored for digital artists, engineers, and AI-assisted pair programming.

## 1. Unified Command Center (`iram`)

All system operations can be controlled via the unified `iram` CLI:

- `iram theme [name]` — Switch or list desktop themes (e.g., `iram theme tokyo-night`, `iram theme ryoku-crimson`)
- `iram craft [app]` — Launch Storytold Craft Suite apps (`photo`, `vector`, `film`, `sound`, `cad`, `word`, `grid`, `deck`, `pdf`, `design`, `effect`)
- `iram ocr` — Instant screen text extraction via Tesseract OCR to clipboard
- `iram display` — Open display and monitor configuration GUI
- `iram capture` — Open screenshot & screen recording menu
- `iram clipboard` — Open clipboard history menu
- `iram agent [prompt]` — Launch IRAM Agentic OS assistant
- `iram sidecar` — Toggle AI Sidecar chat
- `iram info` — Display active system theme, kernel, and compositor status

## 2. Core Shortcuts & Navigation

| Hotkey | Action |
| :--- | :--- |
| `Super + Space` | Application Launcher (`wofi`) |
| `Super + Return` | Open Terminal (`foot` / `alacritty`) |
| `Super + E` | Open File Manager (`dolphin` / `nautilus`) |
| `Super + Q` | Close active window |
| `Super + F` | Toggle window Fullscreen |
| `Super + V` | Toggle window Floating |
| `Super + Ctrl + V` | Clipboard History (`cliphist`) |
| `Super + Ctrl + Print` | Instant Screen OCR text extraction |
| `Super + Ctrl + C` | Screenshot & Screen Recording menu |
| `Super + T` | Theme Switcher menu |
| `Super + Backspace` | Power & Session menu |

## 3. Storytold Craft Suite

IRAM OS includes native launchers and brand icons for the complete open-source Rust creative suite:
- **PhotoCraft** (`craft-photocraft`): Photoshop alternative (PSD, layers, retouching)
- **VectorCraft** (`craft-vectorcraft`): Illustrator alternative (Bezier paths, SVG/AI)
- **FilmCraft** (`craft-filmcraft`): Premiere Pro alternative (Video timeline, color grading)
- **SoundCraft** (`craft-soundcraft`): Avid Pro Tools alternative (Digital audio workstation)
- **LightCraft** (`craft-lightcraft`): Adobe Lightroom alternative (RAW photo processing)
- **CADCraft** (`craft-cadcraft`): AutoCAD alternative (2D/3D CAD modeling)
- **WordCraft** (`craft-wordcraft`): Microsoft Word alternative (Typography & DOCX)
- **GridCraft** (`craft-gridcraft`): Microsoft Excel alternative (High-speed spreadsheets)
- **DeckCraft** (`craft-deckcraft`): PowerPoint alternative (Slide presentations)
- **PdfCraft** (`craft-pdfcraft`): Adobe Acrobat alternative (PDF editor & annotator)
- **ArtCraft Launcher** (`artcraft-launcher`): Hub to manage and launch all Craft apps

## 4. Key Configuration Paths

- Hyprland: `~/.config/hypr/hyprland.conf`
- Waybar: `~/.config/waybar/config` & `~/.config/waybar/style.css`
- Active Theme State: `~/.local/state/iram/current/theme.name`
- Theme Definitions: `~/iram-os/config/iram/themes/`
- User Binaries: `~/.local/bin/` and `~/iram-os/bin/`
