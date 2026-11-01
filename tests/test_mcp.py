#!/usr/bin/env python3
"""Drives bin/iram-os-mcp over stdio, as a real client does, against a fake hyprctl."""
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
  clients) cat <<'J'
[{"address":"0xa1","mapped":true,"class":"firefox","title":"Docs","workspace":{"name":"1"}},
 {"address":"0xb2","mapped":true,"class":"Alacritty","title":"term one","workspace":{"name":"2"}},
 {"address":"0xc3","mapped":true,"class":"Alacritty","title":"term two","workspace":{"name":"2"}}]
J
  ;;
  activewindow) echo '{"class":"firefox","title":"Docs"}' ;;
  dispatch|keyword) echo ok ;;
esac
"""


class Client:
    def __init__(self, home, env=None):
        environment = dict(os.environ, HOME=home, PATH=f"{home}/bin:{os.environ['PATH']}", **(env or {}))
        environment.pop("IRAM_MCP_MAX_TIER", None) if not env else None
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
        path = f"{self.home}/bin/hyprctl"
        with open(path, "w") as f:
            f.write(FAKE_HYPRCTL)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.client = Client(self.home)

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def hyprctl_log(self):
        try:
            with open(f"{self.home}/hyprctl.log") as f:
                return f.read()
        except OSError:
            return ""

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


if __name__ == "__main__":
    unittest.main()
