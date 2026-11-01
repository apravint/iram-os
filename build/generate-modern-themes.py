#!/usr/bin/env python3
"""
Generate Curated Modern Theme Suite (43 Themes) for IRAM OS / Omarchy:
Incorporates top worldwide favorites & best aesthetic assets from Ryoku (ryoku-dev/ryoku).

Themes:
1. Ryoku Crimson (ryoku-crimson) - Flagship Ryoku Distro Sumi Ink & Blood Crimson
2. Cyberpunk Neon (cyberpunk-neon)
3. Dracula (dracula)
4. One Dark Pro (one-dark) - World #1 Atom / VSCode
5. Catppuccin Mocha (catppuccin-mocha) - World #1 Community Aesthetic
6. Nord Frost (nord-frost) - Arctic Ice Studio Polar Night
7. Kanagawa Wave (kanagawa-wave) - Katsushika Hokusai Great Wave
8. Night Owl (night-owl) - Sarah Drasner's Nocturnal Twilight
9. Synthwave '84 (synthwave-84) - Robb Owen's Retro 80s Cyber Sunset
10. Oxocarbon (oxocarbon) - IBM Monolith Design
11. Vesper (vesper) - Rauno Freiberg Minimal Pitch Black & Amber
12. Ayu Mirage (ayu-mirage) - Modern Slate & Sunlight Amber
13. Material Ocean (material-ocean) - Deep Oceanic Abyss
14. Aura Dark (aura-dark) - Deep Violet & Mint Green
15. Rose Pine Moon (rose-pine-moon) - Soft Slate & Rosé Pine
16. Monokai Pro (monokai-pro) - Charcoal & Iconic Syntax Spectrum
17. Solarized Dark (solarized-dark) - Precision Scientific Contrast
18. Tokyo Night Storm (tokyo-storm) - Downtown Tokyo Midnight Rain
"""

import os
import sys
import math
import shutil
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

THEMES = {
    "ryoku-crimson": {
        "title": "Ryoku Crimson",
        "tagline": "力と美のために · Japanese Sumi Ink & Blood Crimson",
        "colors": {
            "mode": "dark",
            "accent": "#e2342a",
            "selection": "#2a1512",
            "muted": "#54322c",
            "background": "#140b0a",
            "dark_background": "#0f0706",
            "darker_background": "#080403",
            "lighter_background": "#221412",
            "foreground": "#f5e6ca",
            "dark_foreground": "#8c756c",
            "light_foreground": "#fdf6e7",
            "bright_foreground": "#ffffff",
            "red": "#e2342a",
            "yellow": "#f6b26b",
            "orange": "#ff5349",
            "green": "#85dfcf",
            "cyan": "#65dac4",
            "blue": "#8dcdff",
            "magenta": "#ff7597",
            "brown": "#965d34",
            "bright_red": "#ff4d43",
            "bright_yellow": "#ffd494",
            "bright_green": "#a4f0e2",
            "bright_cyan": "#85dfcf",
            "bright_blue": "#a8dcff",
            "bright_magenta": "#ffa3b8",
            "hyprland_active_border": "rgb(e2342a) rgb(ff5349) 45deg"
        },
        "vscode": {"name": "Ryoku Crimson", "extension": "ryoku.ryoku-theme"},
        "neovim": "tokyonight-night",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/cornelius-dammrich-2003-mainshot-crop-hd-04.jpg",
        "style": "ryoku"
    },
    "one-dark": {
        "title": "One Dark Pro",
        "tagline": "World's Most Popular Developer Slate & Iconic Syntax",
        "colors": {
            "mode": "dark",
            "accent": "#61afef",
            "selection": "#3e4451",
            "muted": "#5c6370",
            "background": "#282c34",
            "dark_background": "#21252b",
            "darker_background": "#1b1d23",
            "lighter_background": "#2c313a",
            "foreground": "#abb2bf",
            "dark_foreground": "#5c6370",
            "light_foreground": "#abb2bf",
            "bright_foreground": "#ffffff",
            "red": "#e06c75",
            "yellow": "#e5c07b",
            "orange": "#d19a66",
            "green": "#98c379",
            "cyan": "#56b6c2",
            "blue": "#61afef",
            "magenta": "#c678dd",
            "brown": "#be5046",
            "bright_red": "#f07b84",
            "bright_yellow": "#f0cf8a",
            "bright_green": "#a7d288",
            "bright_cyan": "#65c5d1",
            "bright_blue": "#70beff",
            "bright_magenta": "#d587ec",
            "hyprland_active_border": "rgb(61afef) rgb(c678dd) 45deg"
        },
        "vscode": {"name": "One Dark Pro", "extension": "zhuangtongfa.material-theme"},
        "neovim": "onedark",
        "style": "one_dark"
    },
    "catppuccin-mocha": {
        "title": "Catppuccin Mocha",
        "tagline": "Global Community #1 Soothing Dark Pastel Sanctuary",
        "colors": {
            "mode": "dark",
            "accent": "#b4befe",
            "selection": "#313244",
            "muted": "#585b70",
            "background": "#1e1e2e",
            "dark_background": "#181825",
            "darker_background": "#11111b",
            "lighter_background": "#313244",
            "foreground": "#cdd6f4",
            "dark_foreground": "#6c7086",
            "light_foreground": "#bac2de",
            "bright_foreground": "#ffffff",
            "red": "#f38ba8",
            "yellow": "#f9e2af",
            "orange": "#fab387",
            "green": "#a6e3a1",
            "cyan": "#94e2d5",
            "blue": "#89b4fa",
            "magenta": "#cba6f7",
            "brown": "#eba0ac",
            "bright_red": "#f38ba8",
            "bright_yellow": "#f9e2af",
            "bright_green": "#a6e3a1",
            "bright_cyan": "#89dceb",
            "bright_blue": "#b4befe",
            "bright_magenta": "#f5c2e7",
            "hyprland_active_border": "rgb(b4befe) rgb(cba6f7) 45deg"
        },
        "vscode": {"name": "Catppuccin Mocha", "extension": "catppuccin.catppuccin-vsc"},
        "neovim": "catppuccin-mocha",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/wallhaven-qrop2l.jpg",
        "style": "catppuccin"
    },
    "kanagawa-wave": {
        "title": "Kanagawa Wave",
        "tagline": "Hokusai Great Wave Woodblock, Sumi Ink & Fuji White",
        "colors": {
            "mode": "dark",
            "accent": "#7e9cd8",
            "selection": "#2d4f67",
            "muted": "#54546d",
            "background": "#1f1f28",
            "dark_background": "#16161d",
            "darker_background": "#0f0f14",
            "lighter_background": "#2a2a37",
            "foreground": "#dcd7ba",
            "dark_foreground": "#727169",
            "light_foreground": "#e6c384",
            "bright_foreground": "#ffffff",
            "red": "#e82424",
            "yellow": "#dca561",
            "orange": "#ffa066",
            "green": "#76946a",
            "cyan": "#7aa89f",
            "blue": "#7e9cd8",
            "magenta": "#957fb8",
            "brown": "#938aa9",
            "bright_red": "#ff5d62",
            "bright_yellow": "#e6c384",
            "bright_green": "#98bb6c",
            "bright_cyan": "#8ba4b0",
            "bright_blue": "#957fb8",
            "bright_magenta": "#c34043",
            "hyprland_active_border": "rgb(7e9cd8) rgb(957fb8) 45deg"
        },
        "vscode": {"name": "Kanagawa", "extension": "qufiwefefwoyn.kanagawa"},
        "neovim": "kanagawa-wave",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/wallhaven-jedx95.jpg",
        "style": "kanagawa"
    },
    "nord-frost": {
        "title": "Nord Frost",
        "tagline": "Arctic Ice Studio's North-Bluish Polar Night",
        "colors": {
            "mode": "dark",
            "accent": "#88c0d0",
            "selection": "#3b4252",
            "muted": "#4c566a",
            "background": "#2e3440",
            "dark_background": "#242933",
            "darker_background": "#1e222a",
            "lighter_background": "#3b4252",
            "foreground": "#eceff4",
            "dark_foreground": "#4c566a",
            "light_foreground": "#e5e9f0",
            "bright_foreground": "#8fbcbb",
            "red": "#bf616a",
            "yellow": "#ebcb8b",
            "orange": "#d08770",
            "green": "#a3be8c",
            "cyan": "#88c0d0",
            "blue": "#81a1c1",
            "magenta": "#b48ead",
            "brown": "#5e81ac",
            "bright_red": "#d06f79",
            "bright_yellow": "#f5d99b",
            "bright_green": "#b5d09e",
            "bright_cyan": "#8fbcbb",
            "bright_blue": "#88c0d0",
            "bright_magenta": "#c59ebe",
            "hyprland_active_border": "rgb(88c0d0) rgb(81a1c1) 45deg"
        },
        "vscode": {"name": "Nord", "extension": "arcticicestudio.nord-visual-studio-code"},
        "neovim": "nord",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/wallhaven-ex.png",
        "style": "nord"
    },
    "night-owl": {
        "title": "Night Owl",
        "tagline": "Sarah Drasner's Nocturnal Twilight & Vivid Glow",
        "colors": {
            "mode": "dark",
            "accent": "#7fdbca",
            "selection": "#1b3a4b",
            "muted": "#4b6479",
            "background": "#011627",
            "dark_background": "#01111d",
            "darker_background": "#000a12",
            "lighter_background": "#0b2942",
            "foreground": "#d6deeb",
            "dark_foreground": "#5f7e97",
            "light_foreground": "#ffffff",
            "bright_foreground": "#ffffff",
            "red": "#ef5350",
            "yellow": "#ecc48d",
            "orange": "#f78c6c",
            "green": "#22da6e",
            "cyan": "#7fdbca",
            "blue": "#82aaff",
            "magenta": "#c792ea",
            "brown": "#ff5874",
            "bright_red": "#ff6360",
            "bright_yellow": "#f5d39d",
            "bright_green": "#38ea7e",
            "bright_cyan": "#95ede0",
            "bright_blue": "#99bdff",
            "bright_magenta": "#d4a4f5",
            "hyprland_active_border": "rgb(7fdbca) rgb(ecc48d) 45deg"
        },
        "vscode": {"name": "Night Owl", "extension": "sdras.night-owl"},
        "neovim": "night-owl",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/wallhaven-oglzx7.jpg",
        "style": "night_owl"
    },
    "synthwave-84": {
        "title": "Synthwave '84",
        "tagline": "Robb Owen's Retro 80s Cyber Neon Sunset",
        "colors": {
            "mode": "dark",
            "accent": "#ff7edb",
            "selection": "#372d4b",
            "muted": "#614d79",
            "background": "#262335",
            "dark_background": "#1f1b2b",
            "darker_background": "#171421",
            "lighter_background": "#342e47",
            "foreground": "#f0eff1",
            "dark_foreground": "#847896",
            "light_foreground": "#ffffff",
            "bright_foreground": "#ffffff",
            "red": "#fe4450",
            "yellow": "#fede5d",
            "orange": "#f97e72",
            "green": "#72f1b8",
            "cyan": "#36f9f6",
            "blue": "#03edf9",
            "magenta": "#ff7edb",
            "brown": "#b84dff",
            "bright_red": "#ff5964",
            "bright_yellow": "#ffea75",
            "bright_green": "#8affc8",
            "bright_cyan": "#5efffb",
            "bright_blue": "#36f9f6",
            "bright_magenta": "#ff94e4",
            "hyprland_active_border": "rgb(ff7edb) rgb(36f9f6) 45deg"
        },
        "vscode": {"name": "SynthWave '84", "extension": "robbowen.synthwave-vscode"},
        "neovim": "synthwave84",
        "wallpaper_url": "https://raw.githubusercontent.com/ryoku-dev/ryoku/main/ryoku/assets/wallpapers/wallhaven-6l21lx.png",
        "style": "synthwave"
    },
    "cyberpunk-neon": {
        "title": "Cyberpunk Neon",
        "tagline": "Electric Obsidian & High-Voltage Neon",
        "colors": {
            "mode": "dark",
            "accent": "#00f0ff",
            "selection": "#2a153c",
            "muted": "#625e7a",
            "background": "#0d0f18",
            "dark_background": "#08090f",
            "darker_background": "#05050a",
            "lighter_background": "#181a27",
            "foreground": "#eaeefb",
            "dark_foreground": "#70799c",
            "light_foreground": "#f1f4fc",
            "bright_foreground": "#ffffff",
            "red": "#ff0055",
            "yellow": "#ffe600",
            "orange": "#ff7b00",
            "green": "#05ffa1",
            "cyan": "#00f0ff",
            "blue": "#3a86ff",
            "magenta": "#ff007f",
            "brown": "#9b4dca",
            "bright_red": "#ff3377",
            "bright_yellow": "#fff033",
            "bright_green": "#38ffb4",
            "bright_cyan": "#33f3ff",
            "bright_blue": "#619eff",
            "bright_magenta": "#ff3399",
            "hyprland_active_border": "rgb(00f0ff) rgb(ff007f) 45deg"
        },
        "vscode": {"name": "Cyberpunk", "extension": "endormi.2077-theme"},
        "neovim": "tokyonight-night",
        "style": "cyberpunk"
    },
    "dracula": {
        "title": "Dracula",
        "tagline": "Classic Vampire Midnight & Radiant Pastels",
        "colors": {
            "mode": "dark",
            "accent": "#bd93f9",
            "selection": "#44475a",
            "muted": "#6272a4",
            "background": "#282a36",
            "dark_background": "#21222c",
            "darker_background": "#191a21",
            "lighter_background": "#343746",
            "foreground": "#f8f8f2",
            "dark_foreground": "#6272a4",
            "light_foreground": "#f8f8f2",
            "bright_foreground": "#ffffff",
            "red": "#ff5555",
            "yellow": "#f1fa8c",
            "orange": "#ffb86c",
            "green": "#50fa7b",
            "cyan": "#8be9fd",
            "blue": "#bd93f9",
            "magenta": "#ff79c6",
            "brown": "#d6acff",
            "bright_red": "#ff6e6e",
            "bright_yellow": "#ffffa5",
            "bright_green": "#69ff94",
            "bright_cyan": "#a4ffff",
            "bright_blue": "#d1b2ff",
            "bright_magenta": "#ff92df",
            "hyprland_active_border": "rgb(bd93f9) rgb(ff79c6) 45deg"
        },
        "vscode": {"name": "Dracula Official", "extension": "dracula-theme.theme-dracula"},
        "neovim": "dracula",
        "style": "dracula"
    },
    "oxocarbon": {
        "title": "Oxocarbon",
        "tagline": "High-Tech IBM Design Monolith",
        "colors": {
            "mode": "dark",
            "accent": "#ff7eb6",
            "selection": "#262626",
            "muted": "#525252",
            "background": "#161616",
            "dark_background": "#121212",
            "darker_background": "#0c0c0c",
            "lighter_background": "#262626",
            "foreground": "#f4f4f4",
            "dark_foreground": "#787878",
            "light_foreground": "#f4f4f4",
            "bright_foreground": "#ffffff",
            "red": "#ee5396",
            "yellow": "#ffe97b",
            "orange": "#3ddbd9",
            "green": "#42be65",
            "cyan": "#33b1ff",
            "blue": "#82cfff",
            "magenta": "#be95ff",
            "brown": "#ff7eb6",
            "bright_red": "#ff65a8",
            "bright_yellow": "#fff2a6",
            "bright_green": "#5cd17d",
            "bright_cyan": "#66c5ff",
            "bright_blue": "#a1dbff",
            "bright_magenta": "#d0b3ff",
            "hyprland_active_border": "rgb(ff7eb6) rgb(33b1ff) 45deg"
        },
        "vscode": {"name": "Oxocarbon", "extension": "shaunsingh.oxocarbon"},
        "neovim": "oxocarbon",
        "style": "oxocarbon"
    },
    "vesper": {
        "title": "Vesper",
        "tagline": "Minimalist Pure Pitch Dark & Golden Amber",
        "colors": {
            "mode": "dark",
            "accent": "#ffc799",
            "selection": "#232323",
            "muted": "#505050",
            "background": "#101010",
            "dark_background": "#0a0a0a",
            "darker_background": "#050505",
            "lighter_background": "#1c1c1c",
            "foreground": "#ffffff",
            "dark_foreground": "#808080",
            "light_foreground": "#f0f0f0",
            "bright_foreground": "#ffffff",
            "red": "#f57d7d",
            "yellow": "#ffc799",
            "orange": "#fe8019",
            "green": "#99ffe4",
            "cyan": "#8de8fe",
            "blue": "#6cb6ff",
            "magenta": "#e5a5ff",
            "brown": "#cda07b",
            "bright_red": "#fa9494",
            "bright_yellow": "#ffd7b3",
            "bright_green": "#b3ffea",
            "bright_cyan": "#a8efff",
            "bright_blue": "#8bc5ff",
            "bright_magenta": "#edbaff",
            "hyprland_active_border": "rgb(ffc799) rgb(fe8019) 45deg"
        },
        "vscode": {"name": "Vesper", "extension": "raunofreiberg.vesper"},
        "neovim": "vesper",
        "style": "vesper"
    },
    "ayu-mirage": {
        "title": "Ayu Mirage",
        "tagline": "Modern Balanced Slate, Sunlight Amber & Sky",
        "colors": {
            "mode": "dark",
            "accent": "#ff9940",
            "selection": "#273042",
            "muted": "#5c6773",
            "background": "#1f2430",
            "dark_background": "#171b24",
            "darker_background": "#11141b",
            "lighter_background": "#272d3b",
            "foreground": "#cbccc6",
            "dark_foreground": "#707a8c",
            "light_foreground": "#d9d7ce",
            "bright_foreground": "#ffffff",
            "red": "#f28779",
            "yellow": "#ffcc66",
            "orange": "#ff9940",
            "green": "#bae67e",
            "cyan": "#73d0ff",
            "blue": "#5ccfe6",
            "magenta": "#d4bfff",
            "brown": "#e6b673",
            "bright_red": "#ff9688",
            "bright_yellow": "#ffd77d",
            "bright_green": "#c8f28d",
            "bright_cyan": "#8ae0ff",
            "bright_blue": "#70dcf2",
            "bright_magenta": "#e0ceff",
            "hyprland_active_border": "rgb(ff9940) rgb(73d0ff) 45deg"
        },
        "vscode": {"name": "Ayu Mirage", "extension": "teabyii.ayu"},
        "neovim": "ayu-mirage",
        "style": "ayu_mirage"
    },
    "material-ocean": {
        "title": "Material Ocean",
        "tagline": "Bioluminescent Deep Oceanic Abyss",
        "colors": {
            "mode": "dark",
            "accent": "#80cbc4",
            "selection": "#1f2233",
            "muted": "#464b5d",
            "background": "#0f111a",
            "dark_background": "#090b10",
            "darker_background": "#050608",
            "lighter_background": "#1a1c25",
            "foreground": "#8f93a2",
            "dark_foreground": "#585b70",
            "light_foreground": "#c5c7d0",
            "bright_foreground": "#ffffff",
            "red": "#ff5370",
            "yellow": "#ffcb6b",
            "orange": "#f78c6c",
            "green": "#c3e88d",
            "cyan": "#89ddff",
            "blue": "#82aaff",
            "magenta": "#c792ea",
            "brown": "#916853",
            "bright_red": "#ff6b84",
            "bright_yellow": "#ffd685",
            "bright_green": "#d0f0a0",
            "bright_cyan": "#a4e5ff",
            "bright_blue": "#9bbaff",
            "bright_magenta": "#d4a6ef",
            "hyprland_active_border": "rgb(80cbc4) rgb(82aaff) 45deg"
        },
        "vscode": {"name": "Material Theme Ocean", "extension": "Equinusocio.vsc-material-theme"},
        "neovim": "material",
        "style": "material_ocean"
    },
    "aura-dark": {
        "title": "Aura Dark",
        "tagline": "Sleek Deep Violet & Neon Mint Aura",
        "colors": {
            "mode": "dark",
            "accent": "#a277ff",
            "selection": "#25223c",
            "muted": "#545070",
            "background": "#15141b",
            "dark_background": "#111016",
            "darker_background": "#0c0b10",
            "lighter_background": "#211f2d",
            "foreground": "#edecee",
            "dark_foreground": "#6d6d7c",
            "light_foreground": "#edecee",
            "bright_foreground": "#ffffff",
            "red": "#ff6767",
            "yellow": "#ffca85",
            "orange": "#ff9f66",
            "green": "#61ffca",
            "cyan": "#61ffca",
            "blue": "#82e2ff",
            "magenta": "#a277ff",
            "brown": "#f694ff",
            "bright_red": "#ff8585",
            "bright_yellow": "#ffd79e",
            "bright_green": "#82ffda",
            "bright_cyan": "#82ffda",
            "bright_blue": "#a1eaff",
            "bright_magenta": "#b894ff",
            "hyprland_active_border": "rgb(a277ff) rgb(61ffca) 45deg"
        },
        "vscode": {"name": "Aura Dark", "extension": "daltonmenezes.aura-theme"},
        "neovim": "aura-theme",
        "style": "aura_dark"
    },
    "rose-pine-moon": {
        "title": "Rosé Pine Moon",
        "tagline": "Gentle Midnight Slate, Rosé & Pine",
        "colors": {
            "mode": "dark",
            "accent": "#ea9a97",
            "selection": "#393552",
            "muted": "#56526e",
            "background": "#232136",
            "dark_background": "#1c1a2d",
            "darker_background": "#141320",
            "lighter_background": "#2a273f",
            "foreground": "#e0def4",
            "dark_foreground": "#6e6a86",
            "light_foreground": "#e0def4",
            "bright_foreground": "#f5f3ff",
            "red": "#eb6f92",
            "yellow": "#f6c177",
            "orange": "#ea9a97",
            "green": "#9ccfd8",
            "cyan": "#3e8fb0",
            "blue": "#3e8fb0",
            "magenta": "#c4a7e7",
            "brown": "#908caa",
            "bright_red": "#f083a2",
            "bright_yellow": "#f9cf92",
            "bright_green": "#b2dbe2",
            "bright_cyan": "#569fb9",
            "bright_blue": "#569fb9",
            "bright_magenta": "#d0b7ed",
            "hyprland_active_border": "rgb(ea9a97) rgb(c4a7e7) 45deg"
        },
        "vscode": {"name": "Rosé Pine Moon", "extension": "mvllow.rose-pine"},
        "neovim": "rose-pine",
        "style": "rose_pine_moon"
    },
    "monokai-pro": {
        "title": "Monokai Pro",
        "tagline": "Refined Dark Charcoal & Iconic Syntax Spectrum",
        "colors": {
            "mode": "dark",
            "accent": "#ffd866",
            "selection": "#3a383d",
            "muted": "#5b595c",
            "background": "#222222",
            "dark_background": "#19181a",
            "darker_background": "#131213",
            "lighter_background": "#2d2a2e",
            "foreground": "#fcfcfa",
            "dark_foreground": "#727072",
            "light_foreground": "#fcfcfa",
            "bright_foreground": "#ffffff",
            "red": "#ff6188",
            "yellow": "#ffd866",
            "orange": "#fc9867",
            "green": "#a9dc76",
            "cyan": "#78dce8",
            "blue": "#78dce8",
            "magenta": "#ab9df2",
            "brown": "#938aa9",
            "bright_red": "#ff7b9d",
            "bright_yellow": "#ffe085",
            "bright_green": "#bce393",
            "bright_cyan": "#94e4ee",
            "bright_blue": "#94e4ee",
            "bright_magenta": "#bfb5f5",
            "hyprland_active_border": "rgb(ffd866) rgb(ff6188) 45deg"
        },
        "vscode": {"name": "Monokai Pro", "extension": "monokai.theme-monokai-pro-vscode"},
        "neovim": "monokai-pro",
        "style": "monokai_pro"
    },
    "solarized-dark": {
        "title": "Solarized Dark",
        "tagline": "Ethan Schoonover's Precision Low-Contrast Science",
        "colors": {
            "mode": "dark",
            "accent": "#2aa198",
            "selection": "#073642",
            "muted": "#586e75",
            "background": "#002b36",
            "dark_background": "#00212b",
            "darker_background": "#00171f",
            "lighter_background": "#073642",
            "foreground": "#839496",
            "dark_foreground": "#657b83",
            "light_foreground": "#93a1a1",
            "bright_foreground": "#fdf6e3",
            "red": "#dc322f",
            "yellow": "#b58900",
            "orange": "#cb4b16",
            "green": "#859900",
            "cyan": "#2aa198",
            "blue": "#268bd2",
            "magenta": "#d33682",
            "brown": "#6c71c4",
            "bright_red": "#ef4441",
            "bright_yellow": "#c79a00",
            "bright_green": "#97ac00",
            "bright_cyan": "#3ec2b8",
            "bright_blue": "#3ea0e6",
            "bright_magenta": "#e24995",
            "hyprland_active_border": "rgb(2aa198) rgb(268bd2) 45deg"
        },
        "vscode": {"name": "Solarized Dark", "extension": "ryanolsonx.solarized"},
        "neovim": "solarized",
        "style": "solarized"
    },
    "tokyo-storm": {
        "title": "Tokyo Night Storm",
        "tagline": "Folke's Rainy Midnight Tokyo Neon Storm",
        "colors": {
            "mode": "dark",
            "accent": "#7aa2f7",
            "selection": "#2e3c64",
            "muted": "#444b6a",
            "background": "#24283b",
            "dark_background": "#1f2335",
            "darker_background": "#191c2b",
            "lighter_background": "#292e42",
            "foreground": "#c0caf5",
            "dark_foreground": "#565f89",
            "light_foreground": "#a9b1d6",
            "bright_foreground": "#ffffff",
            "red": "#f7768e",
            "yellow": "#e0af68",
            "orange": "#ff9e64",
            "green": "#9ece6a",
            "cyan": "#7dcfff",
            "blue": "#7aa2f7",
            "magenta": "#bb9af7",
            "brown": "#db4b4b",
            "bright_red": "#ff7a93",
            "bright_yellow": "#ffb070",
            "bright_green": "#b9f27c",
            "bright_cyan": "#8ee2ff",
            "bright_blue": "#8bb1ff",
            "bright_magenta": "#c9abff",
            "hyprland_active_border": "rgb(7aa2f7) rgb(bb9af7) 45deg"
        },
        "vscode": {"name": "Tokyo Night", "extension": "enkia.tokyo-night"},
        "neovim": "tokyonight-storm",
        "style": "tokyo_storm"
    }
}


def hex_to_rgb(hex_code):
    h = hex_code.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def get_wallpaper_for_theme(theme_id, data, width=3840, height=2160):
    """Retrieve or generate 3840x2160 aesthetic wallpaper."""
    url = data.get("wallpaper_url")
    if url:
        cache_fn = f"/tmp/{os.path.basename(url)}"
        if not os.path.exists(cache_fn):
            try:
                urllib.request.urlretrieve(url, cache_fn)
            except Exception as e:
                print(f"    [!] Failed to download {url}: {e}, falling back to generator")
                cache_fn = None
        if cache_fn and os.path.exists(cache_fn):
            try:
                with Image.open(cache_fn) as img:
                    img = img.convert("RGB")
                    # Crop & scale to 3840x2160
                    iw, ih = img.size
                    target_ratio = width / height
                    current_ratio = iw / ih
                    if current_ratio > target_ratio:
                        new_w = int(ih * target_ratio)
                        offset = (iw - new_w) // 2
                        img = img.crop((offset, 0, offset + new_w, ih))
                    else:
                        new_h = int(iw / target_ratio)
                        offset = (ih - new_h) // 2
                        img = img.crop((0, offset, iw, offset + new_h))
                    return img.resize((width, height), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"    [!] Error processing image {cache_fn}: {e}")

    # Procedural generation fallback/custom style
    return generate_procedural_wallpaper(theme_id, data, width, height)


def generate_procedural_wallpaper(theme_id, data, width=3840, height=2160):
    colors = data["colors"]
    bg_rgb = hex_to_rgb(colors["dark_background"])
    darker_rgb = hex_to_rgb(colors["darker_background"])
    acc_rgb = hex_to_rgb(colors["accent"])
    cyan_rgb = hex_to_rgb(colors.get("cyan", colors["accent"]))
    red_rgb = hex_to_rgb(colors.get("red", colors["accent"]))
    mag_rgb = hex_to_rgb(colors.get("magenta", colors["accent"]))
    green_rgb = hex_to_rgb(colors.get("green", colors["accent"]))
    yel_rgb = hex_to_rgb(colors.get("yellow", colors["accent"]))

    y_coords = np.linspace(0, 1, height)[:, None]
    x_coords = np.linspace(0, 1, width)[None, :]
    diag = (x_coords * 0.4 + y_coords * 0.6)
    base_r = (darker_rgb[0] * (1 - diag) + bg_rgb[0] * diag).astype(np.uint8)
    base_g = (darker_rgb[1] * (1 - diag) + bg_rgb[1] * diag).astype(np.uint8)
    base_b = (darker_rgb[2] * (1 - diag) + bg_rgb[2] * diag).astype(np.uint8)

    img = Image.fromarray(np.stack([base_r, base_g, base_b], axis=-1), mode="RGB")
    style = data.get("style", "generic")

    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)

    if style == "cyberpunk":
        horizon_y = int(height * 0.58)
        sun_radius = 420
        sun_center = (width // 2, horizon_y - 80)
        for r in range(sun_radius, 0, -2):
            prog = r / sun_radius
            gdraw.ellipse(
                [sun_center[0] - r, sun_center[1] - r, sun_center[0] + r, sun_center[1] + r],
                fill=(int(mag_rgb[0]*prog + yel_rgb[0]*(1-prog)),
                      int(mag_rgb[1]*prog + yel_rgb[1]*(1-prog)),
                      int(mag_rgb[2]*prog + yel_rgb[2]*(1-prog)), 160)
            )
        for sy in range(sun_center[1] - 40, horizon_y, 24):
            bar_h = int(4 + (sy - (sun_center[1] - 40)) * 0.15)
            gdraw.rectangle([0, sy, width, sy + bar_h], fill=(bg_rgb[0], bg_rgb[1], bg_rgb[2], 255))
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
        grid_lines = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gdraw2 = ImageDraw.Draw(grid_lines)
        vanishing_pt = (width // 2, horizon_y)
        for x in range(-width // 2, width + width // 2, 120):
            gdraw2.line([vanishing_pt, (x, height)], fill=(cyan_rgb[0], cyan_rgb[1], cyan_rgb[2], 75), width=2)
        for i in range(1, 28):
            py = horizon_y + int((height - horizon_y) * (math.pow(i / 27, 2.2)))
            gdraw2.line([(0, py), (width, py)], fill=(mag_rgb[0], mag_rgb[1], mag_rgb[2], int(30 + 180*(i/27))), width=2)
        return Image.alpha_composite(img.convert("RGBA"), grid_lines).convert("RGB")

    elif style == "one_dark":
        # Atom / One Dark Pro geometric matrix & deep cyan-purple aura
        gdraw.ellipse([width*0.3 - 600, height*0.4 - 600, width*0.3 + 600, height*0.4 + 600],
                      fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 95))
        gdraw.ellipse([width*0.7 - 600, height*0.6 - 600, width*0.7 + 600, height*0.6 + 600],
                      fill=(mag_rgb[0], mag_rgb[1], mag_rgb[2], 90))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(140))
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer)
        # Hexagonal / isometric wireframes
        wire = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        wdraw = ImageDraw.Draw(wire)
        cx, cy = width // 2, height // 2
        for r in [350, 520, 720]:
            pts = [(cx + r * math.cos(math.radians(a)), cy + r * 0.6 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
            wdraw.polygon(pts, outline=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 120), width=2)
        return Image.alpha_composite(img, wire).convert("RGB")

    elif style == "ayu_mirage":
        # Amber sun horizon with dusk twilight
        gdraw.ellipse([width*0.5 - 650, height*0.55 - 650, width*0.5 + 650, height*0.55 + 650],
                      fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 110))
        gdraw.ellipse([width*0.5 - 350, height*0.55 - 350, width*0.5 + 350, height*0.55 + 350],
                      fill=(yel_rgb[0], yel_rgb[1], yel_rgb[2], 130))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(130))
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer)
        wire = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        wdraw = ImageDraw.Draw(wire)
        wdraw.line([(0, height * 0.55), (width, height * 0.55)], fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 180), width=3)
        return Image.alpha_composite(img, wire).convert("RGB")

    elif style == "solarized":
        # Precision coordinate grids & solar cyan eclipse
        gdraw.ellipse([width*0.5 - 550, height*0.5 - 550, width*0.5 + 550, height*0.5 + 550],
                      fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 95))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(130))
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer)
        grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gdraw2 = ImageDraw.Draw(grid)
        for x in range(0, width, 120):
            gdraw2.line([(x, 0), (x, height)], fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 25), width=1)
        for y in range(0, height, 120):
            gdraw2.line([(0, y), (width, y)], fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 25), width=1)
        return Image.alpha_composite(img, grid).convert("RGB")

    elif style == "tokyo_storm":
        # Midnight storm clouds & glowing electric neon rain
        gdraw.ellipse([width*0.4 - 600, height*0.35 - 600, width*0.4 + 600, height*0.35 + 600],
                      fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 100))
        gdraw.ellipse([width*0.7 - 600, height*0.65 - 600, width*0.7 + 600, height*0.65 + 600],
                      fill=(mag_rgb[0], mag_rgb[1], mag_rgb[2], 85))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(150))
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer)
        rain = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(rain)
        np.random.seed(99)
        for _ in range(250):
            rx = np.random.randint(0, width)
            ry = np.random.randint(0, height)
            rlen = np.random.randint(30, 90)
            rdraw.line([(rx, ry), (rx - 20, ry + rlen)], fill=(cyan_rgb[0], cyan_rgb[1], cyan_rgb[2], 80), width=2)
        return Image.alpha_composite(img, rain).convert("RGB")

    # Generic atmospheric radiant blooms
    gdraw.ellipse([width*0.3 - 600, height*0.4 - 600, width*0.3 + 600, height*0.4 + 600],
                  fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 90))
    gdraw.ellipse([width*0.7 - 600, height*0.6 - 600, width*0.7 + 600, height*0.6 + 600],
                  fill=(mag_rgb[0], mag_rgb[1], mag_rgb[2], 85))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(140))
    return Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")


def generate_preview_card(theme_id, data, wallpaper_img):
    """Generate high-impact 1800x1012 card for the theme switcher preview."""
    target_w, target_h = 1800, 1012
    card = wallpaper_img.copy().resize((target_w, target_h), Image.Resampling.LANCZOS)
    dark_overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 75))
    card = Image.alpha_composite(card.convert("RGBA"), dark_overlay)

    glass_w, glass_h = 1420, 260
    glass_x = (target_w - glass_w) // 2
    glass_y = target_h - glass_h - 60

    glass_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glass_layer)

    bg_rgb = hex_to_rgb(data["colors"]["dark_background"])
    acc_rgb = hex_to_rgb(data["colors"]["accent"])

    gdraw.rectangle([glass_x, glass_y, glass_x + glass_w, glass_y + glass_h],
                    fill=(bg_rgb[0], bg_rgb[1], bg_rgb[2], 225),
                    outline=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 180),
                    width=3)
    gdraw.line([(glass_x, glass_y), (glass_x + glass_w, glass_y)],
               fill=(acc_rgb[0], acc_rgb[1], acc_rgb[2], 255), width=5)

    card = Image.alpha_composite(card, glass_layer).convert("RGB")
    draw = ImageDraw.Draw(card)

    font_title = None
    font_sub = None
    font_tag = None
    for fn in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"
    ]:
        if os.path.exists(fn):
            try:
                font_title = ImageFont.truetype(fn, 50)
                font_sub = ImageFont.truetype(fn.replace("-Bold", "-Regular").replace("-B", "-R"), 23)
                font_tag = ImageFont.truetype(fn, 20)
                break
            except Exception:
                pass
    if font_title is None:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_tag = font_title

    draw.text((glass_x + 50, glass_y + 35), data["title"], font=font_title, fill=(255, 255, 255))
    draw.text((glass_x + 52, glass_y + 110), data["tagline"], font=font_sub,
              fill=hex_to_rgb(data["colors"]["light_foreground"]))
    draw.text((glass_x + 52, glass_y + 152), "IRAM OS · GLOBAL ELITE SUITE", font=font_tag, fill=acc_rgb)

    colors_to_show = [
        ("ACC", data["colors"]["accent"]),
        ("BG", data["colors"]["background"]),
        ("RED", data["colors"]["red"]),
        ("GRN", data["colors"]["green"]),
        ("YEL", data["colors"]["yellow"]),
        ("BLU", data["colors"]["blue"]),
        ("MAG", data["colors"]["magenta"]),
        ("CYN", data["colors"]["cyan"]),
    ]
    swatch_x_start = glass_x + glass_w - 580
    swatch_y = glass_y + 55
    swatch_size = 52
    swatch_spacing = 68

    for idx, (label, hex_val) in enumerate(colors_to_show):
        sx = swatch_x_start + (idx % 4) * swatch_spacing
        sy = swatch_y + (idx // 4) * (swatch_size + 34)
        c_rgb = hex_to_rgb(hex_val)
        draw.rectangle([sx, sy, sx + swatch_size, sy + swatch_size],
                       fill=c_rgb, outline=(255, 255, 255, 120), width=2)
        draw.text((sx + 6, sy + swatch_size + 6), label, font=font_tag, fill=(200, 200, 200))

    return card


def build_colors_toml(data):
    lines = [f'mode = "{data["colors"]["mode"]}"', ""]
    lines.append(f'accent = "{data["colors"]["accent"]}"')
    lines.append(f'selection = "{data["colors"]["selection"]}"')
    lines.append(f'muted = "{data["colors"]["muted"]}"')
    lines.append("")
    lines.append(f'background = "{data["colors"]["background"]}"')
    lines.append(f'dark_background = "{data["colors"]["dark_background"]}"')
    lines.append(f'darker_background = "{data["colors"]["darker_background"]}"')
    lines.append(f'lighter_background = "{data["colors"]["lighter_background"]}"')
    lines.append("")
    lines.append(f'foreground = "{data["colors"]["foreground"]}"')
    lines.append(f'dark_foreground = "{data["colors"]["dark_foreground"]}"')
    lines.append(f'light_foreground = "{data["colors"]["light_foreground"]}"')
    lines.append(f'bright_foreground = "{data["colors"]["bright_foreground"]}"')
    lines.append("")
    for key in ["red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown"]:
        if key in data["colors"]:
            lines.append(f'{key} = "{data["colors"][key]}"')
    lines.append("")
    for key in ["bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta"]:
        if key in data["colors"]:
            lines.append(f'{key} = "{data["colors"][key]}"')
    lines.append("")
    if "hyprland_active_border" in data["colors"]:
        lines.append(f'hyprland_active_border = "{data["colors"]["hyprland_active_border"]}"')
    return "\n".join(lines) + "\n"


def main():
    dest_dirs = [
        os.path.expanduser("~/.config/omarchy/themes"),
        "/home/apravint/iram-os/themes",
        "/home/apravint/iram-os/config/iram/themes"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)

    print(f"🎨 Generating {len(THEMES)} Modern Curated Themes (incorporating Ryoku & World Favorites)...")
    for theme_id, data in THEMES.items():
        print(f"\n✨ Building: {data['title']} ({theme_id})")

        # 1. Acquire / Render Wallpaper (3840x2160)
        wall_img = get_wallpaper_for_theme(theme_id, data, width=3840, height=2160)

        # 2. Render Preview Card (1800x1012)
        prev_img = generate_preview_card(theme_id, data, wall_img)

        # Temporary local staging
        tmp_dir = f"/tmp/iram_theme_{theme_id}"
        os.makedirs(os.path.join(tmp_dir, "backgrounds"), exist_ok=True)

        wall_path = os.path.join(tmp_dir, "backgrounds", "1-wallpaper.webp")
        wall_img.save(wall_path, "WEBP", quality=90)

        prev_path = os.path.join(tmp_dir, "preview.png")
        prev_img.save(prev_path, "PNG", optimize=True)

        shutil.copyfile(prev_path, os.path.join(tmp_dir, "preview-unlock.png"))
        shutil.copyfile(prev_path, os.path.join(tmp_dir, "unlock.png"))

        with open(os.path.join(tmp_dir, "colors.toml"), "w") as f:
            f.write(build_colors_toml(data))
        with open(os.path.join(tmp_dir, "icons.theme"), "w") as f:
            f.write("Papirus-Dark\n")
        with open(os.path.join(tmp_dir, "chromium.theme"), "w") as f:
            f.write(f'{data["colors"]["accent"]}\n')
        with open(os.path.join(tmp_dir, "vscode.json"), "w") as f:
            v = data.get("vscode", {"name": data["title"], "extension": "theme"})
            f.write(f'{{\n  "name": "{v["name"]}",\n  "extension": "{v["extension"]}"\n}}\n')
        with open(os.path.join(tmp_dir, "neovim.lua"), "w") as f:
            nv = data.get("neovim", "default")
            f.write(f'return {{\n  {{\n    "LazyVim/LazyVim",\n    opts = {{\n      colorscheme = "{nv}",\n    }},\n  }},\n}}\n')

        # Install to all destination dirs
        for base_dest in dest_dirs:
            target_theme_dir = os.path.join(base_dest, theme_id)
            if os.path.islink(target_theme_dir):
                os.unlink(target_theme_dir)
            elif os.path.isdir(target_theme_dir):
                shutil.rmtree(target_theme_dir)
            shutil.copytree(tmp_dir, target_theme_dir)
            print(f"  -> Installed to {target_theme_dir}")

        shutil.rmtree(tmp_dir)

    print(f"\n✅ All {len(THEMES)} modern themes successfully generated and installed!")


if __name__ == "__main__":
    main()
