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

GLib.set_prgname("IramNexus")
GLib.set_application_name("IRAM OS Nexus")

PORT = int(os.environ.get("IRAM_SIDECAR_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}"

class SidecarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="IRAM OS Nexus")
        self.set_default_size(960, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Force GTK to Dark Theme
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)

        # WebKit Settings & Cache Policy
        context = WebKit2.WebContext.get_default()
        context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)

        settings = WebKit2.Settings()
        settings.set_enable_webgl(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_javascript(True)
        settings.set_enable_page_cache(False)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_enable_webaudio(True)

        self.webview = WebKit2.WebView.new_with_context(context)
        self.webview.set_settings(settings)
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
