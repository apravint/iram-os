#!/usr/bin/env python3
"""Drives bin/iram-os-mcp over stdio, as a real client does, against a fake hyprctl."""
import base64
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SERVER = os.path.join(REPO, "bin", "iram-os-mcp")

FAKE_HYPRCTL = """#!/bin/sh
echo "$*" >> "$HOME/hyprctl.log"
case "$1" in
  clients) [ -f "$HOME/clients.json" ] && exec cat "$HOME/clients.json"; cat <<'J'
[{"address":"0xa1","mapped":true,"class":"firefox","title":"Docs","workspace":{"id":1,"name":"1"},"at":[0,0],"size":[1920,1080]},
 {"address":"0xb2","mapped":true,"class":"Alacritty","title":"term one","workspace":{"id":2,"name":"2"},"at":[1920,0],"size":[960,1080]},
 {"address":"0xc3","mapped":true,"class":"Alacritty","title":"term two","workspace":{"id":2,"name":"2"},"at":[2880,0],"size":[960,1080]},
 {"address":"0xd4","mapped":true,"class":"org.keepassxc.KeePassXC","title":"Vault","workspace":{"id":3,"name":"3"},"at":[1920,0],"size":[800,600]}]
J
  ;;
  monitors) cat "$HOME/monitors.json" ;;
  activewindow) echo '{"class":"firefox","title":"Docs"}' ;;
  dispatch|keyword) echo ok ;;
esac
"""

# Writes the arguments it got to a log, and a fake JPEG to stdout.
FAKE_GRIM = """#!/bin/sh
echo "$*" >> "$HOME/grim.log"
if [ "$2" = jpeg ] && [ -f "$HOME/grim-no-jpeg" ]; then echo "jpeg support disabled" >&2; exit 1; fi
printf 'FAKE%s' "$2"
"""
FAKE_LOGGER = """#!/bin/sh
for a in "$@"; do printf '%s\\n' "$a"; done >> "$HOME/$(basename "$0").log"
"""


def monitors(hdmi_workspace=2):
    return json.dumps([
        {"name": "DP-1", "activeWorkspace": {"id": 1}, "specialWorkspace": {"id": 0}},
        {"name": "HDMI-A-1", "activeWorkspace": {"id": hdmi_workspace}, "specialWorkspace": {"id": 0}},
    ])


def desktop_file(name, exec_line="true", extra=""):
    return f"[Desktop Entry]\nType=Application\nName={name}\nExec={exec_line}\n{extra}"


class Client:
    def __init__(self, home, env=None):
        environment = dict(os.environ, HOME=home, PATH=f"{home}/bin:{os.environ['PATH']}", XDG_DATA_DIRS=f"{home}/share", **(env or {}))
        environment.pop("IRAM_MCP_MAX_TIER", None) if not env else None
        environment.pop("XDG_DATA_HOME", None)
        self.proc = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=environment)
        self.next_id = 0

    def rpc(self, method, params=None):
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def call(self, name, **args):
        return self.rpc("tools/call", {"name": name, "arguments": args})["result"]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        self.proc.stdout.close()


class McpServer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        os.makedirs(f"{self.home}/bin")
        for name, body in (("hyprctl", FAKE_HYPRCTL), ("grim", FAKE_GRIM), ("notify-send", FAKE_LOGGER), ("gio", FAKE_LOGGER)):
            self.write(f"bin/{name}", body, executable=True)
        self.write("monitors.json", monitors())
        self.write(".local/share/applications/firefox.desktop", desktop_file("Firefox"))
        self.write("share/applications/firefox.desktop", desktop_file("System Firefox"))
        self.write("share/applications/org.gnome.Calculator.desktop", desktop_file("Calculator"))
        self.write("share/applications/helper.desktop", desktop_file("Helper", extra="NoDisplay=true\n"))
        self.write("share/applications/missing.desktop", desktop_file("Missing", extra="TryExec=no-such-binary-iram\n"))
        self.write("share/applications/kde/org.kde.konsole.desktop", desktop_file("Konsole"))
        self.client = Client(self.home)

    def write(self, rel, body, executable=False):
        path = f"{self.home}/{rel}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(body)
        if executable:
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def log(self, name):
        try:
            with open(f"{self.home}/{name}.log") as f:
                return f.read()
        except OSError:
            return ""

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def hyprctl_log(self):
        return self.log("hyprctl")

    def test_handshake_negotiates_version(self):
        result = self.client.rpc("initialize", {"protocolVersion": "2024-11-05"})["result"]
        self.assertEqual(result["protocolVersion"], "2024-11-05")
        self.assertEqual(self.client.rpc("initialize", {"protocolVersion": "1999-01-01"})["result"]["protocolVersion"], "2025-06-18")

    def test_notification_gets_no_reply(self):
        self.client.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.client.proc.stdin.flush()
        self.assertEqual(self.client.rpc("ping")["result"], {})

    def test_default_ceiling_hides_privileged_tools(self):
        names = {t["name"] for t in self.client.rpc("tools/list")["result"]["tools"]}
        self.assertIn("system_telemetry", names)
        self.assertIn("manage_windows", names)
        self.assertNotIn("privileged_action", names)
        result = self.client.call("privileged_action", action="fstrim")
        self.assertTrue(result["isError"])
        self.assertIn("ceiling", result["content"][0]["text"])

    def test_read_ceiling_blocks_mutation(self):
        client = Client(self.home, {"IRAM_MCP_MAX_TIER": "read"})
        try:
            names = {t["name"] for t in client.rpc("tools/list")["result"]["tools"]}
            self.assertNotIn("manage_windows", names)
            self.assertTrue(client.call("self_heal")["isError"])
        finally:
            client.close()

    def test_annotations_reflect_tier(self):
        tools = {t["name"]: t for t in self.client.rpc("tools/list")["result"]["tools"]}
        self.assertTrue(tools["crash_report"]["annotations"]["readOnlyHint"])
        self.assertFalse(tools["manage_windows"]["annotations"]["readOnlyHint"])

    def test_unknown_tool_is_protocol_error(self):
        self.assertEqual(self.client.rpc("tools/call", {"name": "nope"})["error"]["code"], -32602)

    def test_failures_are_flagged(self):
        self.assertTrue(self.client.call("manage_windows", action="bogus")["isError"])

    def test_bad_inputs_never_reach_a_command(self):
        for args in (
            {"action": "movetoworkspace", "workspace": "1; rm -rf ~"},
            {"action": "movetoworkspace", "workspace": "1,address:0x1 exec foo"},
        ):
            self.assertTrue(self.client.call("manage_windows", **args)["isError"], args)
        self.assertTrue(self.client.call("service_diagnostics", unit_name="--help", action="status")["isError"])
        self.assertTrue(self.client.call("audio_display_control", target="audio", command="set_volume 100%; id")["isError"])
        self.assertTrue(self.client.call("switch_theme", theme_name="--help")["isError"])
        self.assertTrue(self.client.call("window_rule", effect="float", match="class:x$(id)")["isError"])
        self.assertTrue(self.client.call("window_rule", effect="exec foo", match="class:x")["isError"])
        self.assertNotIn("rm -rf", self.hyprctl_log())

    def test_ambiguous_selector_refuses_instead_of_guessing(self):
        result = self.client.call("manage_windows", action="close", window_address="alacritty")
        self.assertTrue(result["isError"])
        self.assertIn("matched 2", result["content"][0]["text"])
        self.assertNotIn("closewindow", self.hyprctl_log())

    def test_unique_selector_resolves_to_address(self):
        self.assertFalse(self.client.call("manage_windows", action="focus", window_address="firefox").get("isError"))
        self.assertIn("dispatch focuswindow address:0xa1", self.hyprctl_log())

    def test_close_requires_a_target(self):
        self.assertTrue(self.client.call("manage_windows", action="close")["isError"])

    def test_self_heal_refuses_foreign_units(self):
        self.assertTrue(self.client.call("self_heal", unit_name="dbus.service")["isError"])

    def test_runtime_window_rule(self):
        result = self.client.call("window_rule", effect="float", match="class:^(firefox)$")
        self.assertFalse(result.get("isError"), result)
        self.assertIn("windowrule float 1, match:class ^(firefox)$", self.hyprctl_log())

    def test_mutations_are_audited_privately(self):
        self.client.call("workspace_control", action="switch", workspace="2")
        path = f"{self.home}/.local/state/iram-os/mcp-audit.jsonl"
        with open(path) as f:
            entry = json.loads(f.read().splitlines()[-1])
        self.assertEqual(entry["tool"], "workspace_control")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_content_length_framing_is_answered_in_kind(self):
        body = json.dumps({"jsonrpc": "2.0", "id": 77, "method": "ping"})
        self.client.proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
        self.client.proc.stdin.flush()
        self.assertTrue(self.client.proc.stdout.readline().startswith("Content-Length:"))
        self.client.proc.stdout.readline()
        length_body = self.client.proc.stdout.read(len('{"jsonrpc":"2.0","id":77,"result":{}}'))
        self.assertEqual(json.loads(length_body)["id"], 77)

    def test_malformed_json_keeps_the_server_alive(self):
        self.client.proc.stdin.write("{not json\n")
        self.client.proc.stdin.flush()
        self.assertEqual(json.loads(self.client.proc.stdout.readline())["error"]["code"], -32700)
        self.assertEqual(self.client.rpc("ping")["result"], {})

    def audit_entries(self):
        with open(f"{self.home}/.local/state/iram-os/mcp-audit.jsonl") as f:
            return [json.loads(line) for line in f.read().splitlines()]

    # ---- notify ----

    def test_notify_is_labelled_and_plain_text(self):
        result = self.client.call("notify", summary="Build done", body="<a href='x'>click</a> & go", urgency="critical")
        self.assertFalse(result.get("isError"), result)
        argv = self.log("notify-send").splitlines()
        self.assertEqual(argv, ["--app-name=IRAM agent", "--urgency=critical", "--", "Build done", "&lt;a href='x'&gt;click&lt;/a&gt; &amp; go"])
        self.assertEqual(self.audit_entries()[-1]["tool"], "notify")

    def test_notify_text_cannot_become_an_option(self):
        self.assertFalse(self.client.call("notify", summary="--icon=/etc/passwd").get("isError"))
        self.assertEqual(self.log("notify-send").splitlines()[-1], "--icon=/etc/passwd")
        self.assertIn("--", self.log("notify-send").splitlines())

    def test_notify_rejects_bad_input(self):
        for args in ({"summary": ""}, {"summary": "x" * 121}, {"summary": "ok", "body": "x" * 1001}, {"summary": "ok", "urgency": "loud"}):
            self.assertTrue(self.client.call("notify", **args)["isError"], args)
        self.assertEqual(self.log("notify-send"), "")

    def test_notify_strips_control_characters(self):
        self.client.call("notify", summary="a\x1b[31mb\x07")
        self.assertEqual(self.log("notify-send").splitlines()[-1], "a[31mb")

    # ---- list_apps / launch_app ----

    def test_list_apps_follows_xdg_rules(self):
        apps = {a["id"]: a for a in json.loads(self.client.call("list_apps")["content"][0]["text"])["apps"]}
        self.assertEqual(apps["firefox"]["name"], "Firefox", "XDG_DATA_HOME wins over XDG_DATA_DIRS")
        self.assertIn("org.gnome.Calculator", apps)
        self.assertIn("kde-org.kde.konsole", apps, "subdirectories become dash-joined IDs")
        self.assertNotIn("helper", apps, "NoDisplay entries are not listed")
        self.assertNotIn("missing", apps, "entries whose TryExec is absent are not listed")
        found = json.loads(self.client.call("list_apps", query="calc")["content"][0]["text"])["apps"]
        self.assertEqual([a["id"] for a in found], ["org.gnome.Calculator"])

    def test_launch_app_uses_the_resolved_entry(self):
        result = self.client.call("launch_app", desktop_id="org.gnome.Calculator.desktop")
        self.assertFalse(result.get("isError"), result)
        self.assertEqual(self.log("gio").splitlines(), ["launch", f"{self.home}/share/applications/org.gnome.Calculator.desktop"])
        self.client.call("launch_app", desktop_id="firefox")
        self.assertIn(f"{self.home}/.local/share/applications/firefox.desktop", self.log("gio"))

    def test_launch_app_refuses_anything_but_a_listed_id(self):
        for desktop_id in ("helper", "missing", "nope", "../../etc/passwd", "firefox; id", "-firefox", "/usr/share/applications/firefox.desktop", ""):
            self.assertTrue(self.client.call("launch_app", desktop_id=desktop_id)["isError"], desktop_id)
        self.assertEqual(self.log("gio"), "")

    def test_read_ceiling_lists_apps_but_cannot_launch_or_notify(self):
        client = Client(self.home, {"IRAM_MCP_MAX_TIER": "read"})
        try:
            names = {t["name"] for t in client.rpc("tools/list")["result"]["tools"]}
            self.assertIn("list_apps", names)
            self.assertIn("screenshot", names)
            self.assertNotIn("launch_app", names)
            self.assertNotIn("notify", names)
            self.assertTrue(client.call("launch_app", desktop_id="firefox")["isError"])
        finally:
            client.close()
        self.assertEqual(self.log("gio"), "")

    # ---- screenshot ----

    def test_screenshot_returns_an_image_and_is_audited(self):
        result = self.client.call("screenshot")
        self.assertFalse(result.get("isError"), result)
        image, meta = result["content"]
        self.assertEqual(image["type"], "image")
        self.assertEqual(image["mimeType"], "image/jpeg")
        self.assertEqual(base64.b64decode(image["data"]), b"FAKEjpeg")
        self.assertEqual(json.loads(meta["text"])["scale"], 0.5)
        self.assertEqual(self.log("grim").strip(), "-t jpeg -q 75 -s 0.50 -")
        self.assertEqual(self.audit_entries()[-1]["tool"], "screenshot")

    def test_screenshot_falls_back_to_png_without_jpeg_support(self):
        self.write("grim-no-jpeg", "")
        image, meta = self.client.call("screenshot")["content"]
        self.assertEqual(image["mimeType"], "image/png")
        self.assertEqual(base64.b64decode(image["data"]), b"FAKEpng")
        self.assertEqual(json.loads(meta["text"])["format"], "png")
        self.assertEqual(self.log("grim").splitlines(), ["-t jpeg -q 75 -s 0.50 -", "-t png -s 0.50 -"])

    def test_launch_app_accepts_web_app_ids_with_spaces(self):
        self.write(".local/share/applications/Disk Usage.desktop", desktop_file("Disk Usage"))
        self.assertFalse(self.client.call("launch_app", desktop_id="Disk Usage").get("isError"))
        self.assertIn("Disk Usage.desktop", self.log("gio"))

    def test_screenshot_monitor_and_window_regions(self):
        self.client.call("screenshot", target="monitor", monitor="HDMI-A-1", scale=5)
        self.assertIn("-s 1.00 -o HDMI-A-1 -", self.log("grim"))
        self.client.call("screenshot", target="window", window_address="firefox")
        self.assertIn("-g 0,0 1920x1080 -", self.log("grim"))
        self.assertTrue(self.client.call("screenshot", target="monitor", monitor="DP-9")["isError"])
        self.assertTrue(self.client.call("screenshot", target="monitor", monitor="-o x")["isError"])

    def test_screenshot_refuses_while_a_password_manager_is_visible(self):
        self.write("monitors.json", monitors(hdmi_workspace=3))
        for args in ({}, {"target": "monitor", "monitor": "HDMI-A-1"}, {"target": "window", "window_address": "keepass"}):
            result = self.client.call("screenshot", **args)
            self.assertTrue(result["isError"], args)
            self.assertIn("password manager", result["content"][0]["text"])
        self.assertFalse(self.client.call("screenshot", target="monitor", monitor="DP-1").get("isError"))
        self.assertEqual(self.log("grim").count("\n"), 1)

    def test_screenshot_window_refuses_a_prompt_floating_over_it(self):
        self.write("clients.json", json.dumps([
            {"address": "0xb2", "mapped": True, "class": "Alacritty", "title": "one", "workspace": {"id": 2}, "at": [1920, 0], "size": [960, 1080]},
            {"address": "0xc3", "mapped": True, "class": "Alacritty", "title": "two", "workspace": {"id": 2}, "at": [2880, 0], "size": [960, 1080]},
            {"address": "0xe5", "mapped": True, "class": "pinentry-gnome3", "title": "PIN", "workspace": {"id": 2}, "at": [2000, 300], "size": [400, 200]},
        ]))
        self.assertTrue(self.client.call("screenshot", target="window", window_address="0xb2")["isError"])
        self.assertFalse(self.client.call("screenshot", target="window", window_address="0xc3").get("isError"))
        self.assertIn("-g 2880,0 960x1080", self.log("grim"))

    def test_screenshot_refuses_windows_on_hidden_workspaces(self):
        result = self.client.call("screenshot", target="window", window_address="keepass")
        self.assertTrue(result["isError"])
        self.assertIn("not on a visible workspace", result["content"][0]["text"])
        self.assertEqual(self.log("grim"), "")


if __name__ == "__main__":
    unittest.main()
