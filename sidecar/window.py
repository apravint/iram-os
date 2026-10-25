#!/usr/bin/env python3
"""
IRAM OS - Native Wayland Desktop Window for Gemini Sidecar
Uses GTK3 + WebKit2 to provide a dedicated, lightweight, zero-sandbox
floating desktop sidecar window with instant toggling.
"""

import sys
import os
import signal

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('WebKit2', '4.1')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, WebKit2, Gdk, GLib
except Exception as e:
    print(f"Error loading WebKit2/GTK: {e}", file=sys.stderr)
    sys.exit(1)

# Handle SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)

GLib.set_prgname("IramGeminiSidecar")
GLib.set_application_name("IRAM OS Gemini Sidecar")

PORT = int(os.environ.get("IRAM_SIDECAR_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}"

class SidecarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="IRAM OS Gemini Sidecar")
        self.set_default_size(960, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        # WebKit Settings
        settings = WebKit2.Settings()
        settings.set_enable_webgl(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_javascript(True)
        settings.set_enable_page_cache(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_enable_webaudio(True)

        self.webview = WebKit2.WebView.new_with_settings(settings)
        self.webview.load_uri(URL)

        # Keyboard shortcut: Escape to close
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.add(self.webview)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

def main():
    win = SidecarWindow()
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
