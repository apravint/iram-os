#!/usr/bin/env python3
"""Runs the real theme engine for every theme, with desktop commands stubbed out, and checks legibility."""
import glob
import os
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENGINE = os.path.join(REPO, "bin", "iram-theme-sync-all")
# Stubbed so a test run can never signal or restart the developer's live desktop.
STUBS = ("pkill", "hyprctl", "systemctl", "swaync-client", "swaybg", "makoctl", "notify-send")


def luminance(color):
    channels = []
    for i in (1, 3, 5):
        c = int(color[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def theme_value(colors_file, key):
    with open(colors_file, encoding="utf-8") as f:
        match = re.search(rf'^{key}\s*=\s*"(#[0-9a-fA-F]{{6}})"', f.read(), re.M)
    return match.group(1) if match else None


class ThemeSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.stub_dir = os.path.join(cls.tmp.name, "stubs")
        os.makedirs(cls.stub_dir)
        for name in STUBS:
            path = os.path.join(cls.stub_dir, name)
            with open(path, "w") as f:
                f.write("#!/bin/sh\nexit 0\n")
            os.chmod(path, 0o755)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def sync(self, colors_file):
        home = tempfile.mkdtemp(dir=self.tmp.name)
        theme_dir = os.path.join(home, ".local/state/iram/current/theme")
        os.makedirs(theme_dir)
        shutil.copy(colors_file, theme_dir)
        env = dict(os.environ, HOME=home, PATH=f"{self.stub_dir}:{os.environ['PATH']}")
        env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        subprocess.run(["python3", ENGINE], check=True, env=env, capture_output=True)
        return home

    def test_every_theme_is_legible_on_the_bar_and_launcher(self):
        themes = sorted(glob.glob(os.path.join(REPO, "themes/*/colors.toml")))
        self.assertGreater(len(themes), 0)
        for colors_file in themes:
            name = colors_file.split(os.sep)[-2]
            with self.subTest(theme=name):
                home = self.sync(colors_file)
                with open(f"{home}/.config/waybar/colors.css") as f:
                    css = dict(re.findall(r"@define-color (\w+) (#[0-9a-fA-F]{6});", f.read()))
                bar = theme_value(colors_file, "dark_background") or theme_value(colors_file, "background")
                for key in ("muted_text", "accent_text", "danger_text", "warning_text"):
                    self.assertGreaterEqual(round(contrast(css[key], bar), 2), 4.5, key)
                self.assertGreaterEqual(contrast(css["on_accent"], css["accent"]), 4.5)
                self.assertGreaterEqual(contrast(css["on_danger"], css["danger"]), 4.5)
                with open(f"{home}/.config/wofi/style.css") as f:
                    wofi = f.read()
                self.assertIn(f"color: {css['on_accent']};", wofi)

    def test_declared_mode_matches_the_palette(self):
        for colors_file in glob.glob(os.path.join(REPO, "themes/*/colors.toml")):
            background = theme_value(colors_file, "background")
            with open(colors_file, encoding="utf-8") as f:
                light = re.search(r'^mode\s*=\s*"light"', f.read(), re.M) is not None
            self.assertEqual(luminance(background) > 0.4, light, colors_file)

    def test_shipped_styles_take_every_color_from_the_palette(self):
        with open(os.path.join(REPO, "config/waybar/style.css")) as f:
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{6}\b|rgba\(", f.read()))
        with open(os.path.join(REPO, "config/waybar/colors.css")) as f:
            defined = set(re.findall(r"@define-color (\w+)", f.read()))
        with open(os.path.join(REPO, "config/waybar/style.css")) as f:
            used = set(re.findall(r"@([a-z_]+)\b", f.read())) - {"import", "keyframes"}
        self.assertEqual(used - defined, set())


if __name__ == "__main__":
    unittest.main()
