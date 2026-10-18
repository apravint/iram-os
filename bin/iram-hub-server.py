#!/usr/bin/env python3
"""
IRAM OS Sovereign Command Hub Micro-Server
Provides static WebGL asset serving + Dynamic REST APIs for Desktop Control,
VoiceStudio TTS, Theme Switching, 3D Viewers, and Swarm Orchestration.
"""

import os
import sys
import json
import time
import shutil
import psutil
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("IRAM_HUB_PORT", 8990))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "hub"))

class SovereignHubHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Static assets fallback
        if not path.startswith("/api/"):
            return super().do_GET()

        # Handle API Endpoints
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        response_data = {"ok": False}

        try:
            if path == "/api/status":
                response_data = self.handle_status()
            elif path == "/api/launch":
                app = params.get("app", [""])[0]
                response_data = self.handle_launch(app)
            elif path == "/api/theme":
                name = params.get("name", [""])[0]
                response_data = self.handle_theme(name)
            elif path == "/api/voice":
                text = params.get("text", ["Hello from IRAM OS"])[0]
                voice = params.get("voice", ["jarvis"])[0]
                response_data = self.handle_voice(text, voice)
            elif path == "/api/harness":
                task = params.get("task", ["Audit system integrity"])[0]
                response_data = self.handle_harness(task)
            elif path == "/api/hypr":
                dispatcher = params.get("cmd", [""])[0]
                args = params.get("args", [""])[0]
                response_data = self.handle_hypr(dispatcher, args)
            elif path == "/api/mcp":
                response_data = {
                    "ok": True,
                    "server": "iram-mcp-server",
                    "tools": [
                        "get_windows", "focus_window", "dispatch_hyprland", "get_monitors",
                        "get_system_health", "qdrant_search_code", "run_harness_workflow",
                        "voice_speak", "voice_clone", "voice_design", "list_voices",
                        "open_3d_inspector", "open_agent_swarm_graph", "open_3d_theme_studio"
                    ]
                }
            else:
                response_data = {"ok": False, "error": f"Unknown endpoint: {path}"}
        except Exception as e:
            response_data = {"ok": False, "error": str(e)}

        self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))

    def handle_status(self):
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        
        # Check active window in hyprland
        active_win = "Unknown"
        active_ws = 1
        try:
            out = subprocess.check_output(["hyprctl", "activewindow", "-j"], text=True)
            w_info = json.loads(out)
            active_win = w_info.get("class", "None")
            active_ws = w_info.get("workspace", {}).get("id", 1)
        except Exception:
            pass

        return {
            "ok": True,
            "cpu_percent": cpu_pct,
            "memory": {
                "used_gb": round((mem.total - mem.available) / (1024**3), 1),
                "total_gb": round(mem.total / (1024**3), 1),
                "percent": mem.percent
            },
            "hyprland": {
                "active_window": active_win,
                "workspace": active_ws
            },
            "pipewire": "Active (48kHz PipeWire DSP)",
            "gateway": "FastMCP Active"
        }

    def handle_launch(self, app):
        routes = {
            "iram-3d": ["/home/apravint/.local/bin/iram-3d"],
            "iram-agent-graph": ["/home/apravint/.local/bin/iram-agent-graph"],
            "iram-theme-3d": ["/home/apravint/.local/bin/iram-theme-3d"],
            "iram-video-3d": ["/home/apravint/.local/bin/iram-video-3d"],
            "iram-sidecar": ["/home/apravint/.local/bin/iram-agent-sidecar"],
            "terminal": ["alacritty"]
        }
        if app in routes:
            subprocess.Popen(routes[app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "launched": app}
        return {"ok": False, "error": f"Unknown app target: {app}"}

    def handle_theme(self, name):
        if not name:
            return {"ok": False, "error": "No theme name specified"}
        # Execute theme change
        cmd = ["/home/apravint/.local/bin/iram", "theme", "set", name]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "theme": name, "message": f"Theme set to {name}"}

    def handle_voice(self, text, voice):
        if not text:
            return {"ok": False, "error": "No text provided for speech"}
        cmd = ["/home/apravint/.local/bin/iram", "voice", "speak", text, "--voice", voice]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "voice": voice, "text": text}

    def handle_harness(self, task):
        cmd = ["/home/apravint/.local/bin/iram", "workflow", "run", task]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "task": task, "message": "Harness cyclic loop dispatched"}

    def handle_hypr(self, dispatcher, args):
        cmd = ["hyprctl", "dispatch", dispatcher]
        if args:
            cmd.append(args)
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": res.returncode == 0, "output": res.stdout.strip()}

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), SovereignHubHandler)
    print(f"IRAM Sovereign Hub Backend running at http://127.0.0.1:{PORT}/")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
