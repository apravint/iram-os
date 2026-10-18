#!/usr/bin/env python3
"""
Iram Visual Theme Switcher with Previews
Native Wayland/Hyprland card grid theme selector for Iram.
Supports Curated Modern Suite and Legacy themes with instant preview cards.
"""

import os
import subprocess
import sys
import shutil
import threading
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

GLib.set_prgname("iram-theme-switcher-gui")
GLib.set_application_name("Iram Theme Switcher")

MODERN_THEME_IDS = [
    "ryoku-crimson",
    "cyberpunk-neon",
    "dracula",
    "one-dark",
    "catppuccin-mocha",
    "kanagawa-wave",
    "nord-frost",
    "night-owl",
    "synthwave-84",
    "oxocarbon",
    "vesper",
    "ayu-mirage",
    "material-ocean",
    "aura-dark",
    "rose-pine-moon",
    "monokai-pro",
    "solarized-dark",
    "tokyo-storm"
]

THEMES_DIRS = [
    os.path.expanduser('~/.config/iram/themes'),
    os.path.expanduser('~/.config/omarchy/themes'),
    os.path.expanduser('~/.config/omarchy/themes.bak'),
    '/usr/share/iram/themes',
    '/usr/share/omarchy/themes'
]

STATE_FILE = os.path.expanduser('~/.local/state/iram/current/theme.name')
CACHE_DIR = os.path.expanduser('~/.cache/iram/theme-previews')


def get_current_theme():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    return "cyberpunk-neon"


def find_theme_preview(theme_path):
    # Check for direct preview files
    for name in ['preview.png', 'preview.jpg', 'preview.jpeg', 'preview.webp']:
        p = os.path.join(theme_path, name)
        if os.path.isfile(p):
            return p
    # Check in backgrounds/
    bg_dir = os.path.join(theme_path, 'backgrounds')
    if os.path.isdir(bg_dir):
        for f in sorted(os.listdir(bg_dir)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return os.path.join(bg_dir, f)
    return None


def get_all_themes():
    themes = {}
    for base_dir in THEMES_DIRS:
        if not os.path.isdir(base_dir):
            continue
        for entry in sorted(os.listdir(base_dir)):
            full_path = os.path.join(base_dir, entry)
            if os.path.isdir(full_path) and entry not in themes:
                preview = find_theme_preview(full_path)
                category = "modern" if entry in MODERN_THEME_IDS else "legacy"
                themes[entry] = {
                    'name': entry,
                    'path': full_path,
                    'preview': preview,
                    'category': category
                }
    
    # Sort: Modern suite first in designated order, then legacy alphabetically
    sorted_list = []
    for mod_id in MODERN_THEME_IDS:
        if mod_id in themes:
            sorted_list.append(themes[mod_id])
    
    legacy_list = [t for t in themes.values() if t['category'] == 'legacy']
    legacy_list.sort(key=lambda x: x['name'])
    sorted_list.extend(legacy_list)
    
    return sorted_list


class ThemeCard(Gtk.FlowBoxChild):
    def __init__(self, theme_data, is_active=False):
        super().__init__()
        self.theme_name = theme_data['name']
        self.preview_path = theme_data['preview']
        self.theme_category = theme_data.get('category', 'legacy')
        self.is_active = is_active

        # Card container
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.card.get_style_context().add_class("theme-card")
        if self.is_active:
            self.card.get_style_context().add_class("active-card")
        self.add(self.card)

        # Image thumbnail
        self.img_widget = Gtk.Image()
        self.load_thumbnail()
        self.card.pack_start(self.img_widget, False, False, 0)

        # Bottom label row
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        display_name = self.theme_name.replace('-', ' ').title()
        self.title_label = Gtk.Label(label=display_name)
        self.title_label.get_style_context().add_class("theme-title")
        self.title_label.set_xalign(0)
        self.title_label.set_yalign(0.5)
        label_box.pack_start(self.title_label, True, True, 4)

        if self.theme_category == "modern":
            badge_mod = Gtk.Label(label="MODERN")
            badge_mod.get_style_context().add_class("modern-badge")
            label_box.pack_start(badge_mod, False, False, 2)

        self.badge = Gtk.Label()
        self.badge.get_style_context().add_class("active-badge")
        if self.is_active:
            self.badge.set_text("ACTIVE")
            self.badge.show()
        else:
            self.badge.set_text("")
            self.badge.hide()
        label_box.pack_end(self.badge, False, False, 4)

        self.card.pack_start(label_box, False, False, 2)

    def load_thumbnail(self):
        w, h = 280, 158
        if self.preview_path and os.path.isfile(self.preview_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    self.preview_path, w, h, False
                )
                self.img_widget.set_from_pixbuf(pixbuf)
                return
            except Exception as e:
                print(f"Error loading preview for {self.theme_name}: {e}", file=sys.stderr)

        # Placeholder if no preview found
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, w, h)
        pixbuf.fill(0x313244ff)
        self.img_widget.set_from_pixbuf(pixbuf)

    def set_active_state(self, active):
        self.is_active = active
        if active:
            self.card.get_style_context().add_class("active-card")
            self.badge.set_text("ACTIVE")
            self.badge.show()
        else:
            self.card.get_style_context().remove_class("active-card")
            self.badge.set_text("")
            self.badge.hide()


class ThemeSwitcherApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Iram Theme Switcher")
        self.set_default_size(980, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(16)

        self.category_filter = "modern"

        # Dark theme styling matching modern aesthetic
        css_provider = Gtk.CssProvider()
        css_data = """
        window, window.background, .main-bg {
            background-color: #14161f;
            color: #cdd6f4;
        }
        .header-title {
            font-size: 20px;
            font-weight: 800;
            color: #00f0ff;
        }
        .header-subtitle {
            font-size: 13px;
            color: #a6adc8;
        }
        search-entry, entry {
            background-color: #1e2233;
            color: #cdd6f4;
            border: 1px solid #33394f;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }
        entry:focus {
            border-color: #00f0ff;
        }
        .cat-btn {
            background-color: #1e2233;
            color: #9aa2c2;
            border: 1px solid #33394f;
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 600;
        }
        .cat-btn:hover {
            background-color: #293049;
            color: #ffffff;
        }
        .cat-btn-active {
            background-color: #00f0ff;
            color: #0d0f18;
            border-color: #00f0ff;
            font-weight: 800;
        }
        flowbox {
            background-color: transparent;
        }
        flowboxchild {
            padding: 6px;
            background-color: transparent;
        }
        .theme-card {
            background-color: #1a1c28;
            border: 2px solid #282c3f;
            border-radius: 8px;
            padding: 8px;
            transition: all 150ms ease;
        }
        .theme-card:hover {
            border-color: #00f0ff;
            background-color: #202434;
        }
        .active-card {
            border-color: #05ffa1;
            background-color: #182522;
        }
        .theme-title {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        }
        .modern-badge {
            background-color: rgba(0, 240, 255, 0.15);
            color: #00f0ff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .active-badge {
            background-color: #05ffa1;
            color: #05140d;
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 4px;
        }
        button.suggested-action {
            background-color: #00f0ff;
            color: #08090f;
            font-weight: 800;
            border-radius: 6px;
            padding: 10px 24px;
            font-size: 14px;
        }
        button.suggested-action:hover {
            background-color: #33f3ff;
        }
        button.cancel-btn {
            background-color: #1e2233;
            color: #cdd6f4;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 14px;
        }
        button.cancel-btn:hover {
            background-color: #293049;
        }
        """
        css_provider.load_from_data(css_data.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.get_style_context().add_class("main-bg")
        self.add(main_box)

        # Top Header Bar
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label="🎨 Iram Modern Theme Switcher")
        title_label.get_style_context().add_class("header-title")
        title_label.set_xalign(0)
        title_label.set_yalign(0.5)
        title_box.pack_start(title_label, False, False, 0)

        self.current_theme = get_current_theme()
        self.sub_label = Gtk.Label(label=f"Active theme: {self.current_theme.replace('-', ' ').title()}")
        self.sub_label.get_style_context().add_class("header-subtitle")
        self.sub_label.set_xalign(0)
        self.sub_label.set_yalign(0.5)
        title_box.pack_start(self.sub_label, False, False, 0)
        top_box.pack_start(title_box, False, False, 0)

        # Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("🔍 Search themes...")
        self.search_entry.set_width_chars(25)
        self.search_entry.connect("search-changed", self.on_search_changed)
        top_box.pack_end(self.search_entry, False, False, 0)
        main_box.pack_start(top_box, False, False, 0)

        # Category Filter Pills
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_modern = Gtk.Button(label="✨ Modern Suite (18)")
        self.btn_modern.get_style_context().add_class("cat-btn")
        self.btn_modern.get_style_context().add_class("cat-btn-active")
        self.btn_modern.connect("clicked", lambda b: self.set_category_filter("modern"))
        cat_box.pack_start(self.btn_modern, False, False, 0)

        self.btn_legacy = Gtk.Button(label="📦 Legacy Themes")
        self.btn_legacy.get_style_context().add_class("cat-btn")
        self.btn_legacy.connect("clicked", lambda b: self.set_category_filter("legacy"))
        cat_box.pack_start(self.btn_legacy, False, False, 0)

        self.btn_all = Gtk.Button(label="🌐 All Themes")
        self.btn_all.get_style_context().add_class("cat-btn")
        self.btn_all.connect("clicked", lambda b: self.set_category_filter("all"))
        cat_box.pack_start(self.btn_all, False, False, 0)

        main_box.pack_start(cat_box, False, False, 0)

        # Scrollable Area for Grid
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(3)
        self.flowbox.set_min_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_activate_on_single_click(False)
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_filter_func(self.filter_themes)
        self.flowbox.connect("child-activated", self.on_child_activated)
        self.flowbox.connect("selected-children-changed", self.on_selection_changed)

        scrolled.add(self.flowbox)
        main_box.pack_start(scrolled, True, True, 0)

        # Bottom Bar
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.info_label = Gtk.Label(label="Select a theme and click Apply (or double-click)")
        self.info_label.set_xalign(0)
        self.info_label.set_yalign(0.5)
        bottom_box.pack_start(self.info_label, True, True, 0)

        close_btn = Gtk.Button(label="Close (Esc)")
        close_btn.get_style_context().add_class("cancel-btn")
        close_btn.connect("clicked", lambda b: self.close())
        bottom_box.pack_end(close_btn, False, False, 0)

        self.apply_btn = Gtk.Button(label="⚡ Apply Theme")
        self.apply_btn.get_style_context().add_class("suggested-action")
        self.apply_btn.connect("clicked", self.on_apply_clicked)
        bottom_box.pack_end(self.apply_btn, False, False, 0)

        main_box.pack_start(bottom_box, False, False, 0)

        # Keybindings: Enter to apply, Escape to close
        self.connect("key-press-event", self.on_key_press)

        # Load Themes
        self.cards = {}
        self.selected_theme_name = self.current_theme
        self.load_themes()

    def set_category_filter(self, cat):
        self.category_filter = cat
        for btn, name in [(self.btn_modern, "modern"), (self.btn_legacy, "legacy"), (self.btn_all, "all")]:
            ctx = btn.get_style_context()
            if name == cat:
                ctx.add_class("cat-btn-active")
            else:
                ctx.remove_class("cat-btn-active")
        self.flowbox.invalidate_filter()

    def load_themes(self):
        themes = get_all_themes()
        selected_child = None

        for t in themes:
            is_active = (t['name'] == self.current_theme)
            card = ThemeCard(t, is_active=is_active)
            self.cards[t['name']] = card
            self.flowbox.add(card)
            if is_active:
                selected_child = card

        self.flowbox.show_all()
        if selected_child:
            self.flowbox.select_child(selected_child)

    def filter_themes(self, child):
        if self.category_filter != "all" and child.theme_category != self.category_filter:
            return False
        query = self.search_entry.get_text().strip().lower()
        if not query:
            return True
        return query in child.theme_name.lower()

    def on_search_changed(self, entry):
        self.flowbox.invalidate_filter()

    def on_selection_changed(self, flowbox):
        selected = flowbox.get_selected_children()
        if selected:
            card = selected[0]
            self.selected_theme_name = card.theme_name
            disp_name = card.theme_name.replace('-', ' ').title()
            self.info_label.set_text(f"Selected: {disp_name}  (Press Enter or click Apply)")

    def on_child_activated(self, flowbox, child):
        self.selected_theme_name = child.theme_name
        self.apply_theme(self.selected_theme_name)

    def on_apply_clicked(self, button):
        if self.selected_theme_name:
            self.apply_theme(self.selected_theme_name)

    def apply_theme(self, theme_name):
        if not theme_name:
            return

        disp_name = theme_name.replace('-', ' ').title()
        self.apply_btn.set_sensitive(False)
        self.info_label.set_text(f"⏳ Applying {disp_name}...")

        def worker():
            subprocess.run(['iram', 'theme', 'set', theme_name], check=False)

            def on_done():
                self.apply_btn.set_sensitive(True)
                for name, card in self.cards.items():
                    card.set_active_state(name == theme_name)

                self.current_theme = theme_name
                self.sub_label.set_text(f"Active theme: {disp_name}")
                self.info_label.set_text(f"✅ Applied {disp_name} successfully!")

                osd_bin = shutil.which('iram-osd') or shutil.which('omarchy-osd')
                if osd_bin:
                    try:
                        subprocess.run([
                            osd_bin,
                            '-i', 'preferences-desktop-theme',
                            '-m', f"Theme: {disp_name}"
                        ], check=False)
                    except Exception:
                        pass
                return False

            GLib.idle_add(on_done)

        threading.Thread(target=worker, daemon=True).start()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if self.selected_theme_name:
                self.apply_theme(self.selected_theme_name)
                return True
        return False


def main():
    app = ThemeSwitcherApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
