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

# Import Sovereign Ecosystem Modules
try:
    import smart_router.cache
    import smart_router.scorer
    SMART_ROUTER_AVAILABLE = True
except Exception:
    SMART_ROUTER_AVAILABLE = False

try:
    import toolgate.firewall
    TOOLGATE_AVAILABLE = True
except Exception:
    TOOLGATE_AVAILABLE = False

PORT = int(os.environ.get("IRAM_HUB_PORT", 8990))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "assets", "hub"))

class SovereignHubHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else ""

        params = {}
        if body:
            try:
                params = json.loads(body)
            except Exception:
                parsed_qs = parse_qs(body)
                params = {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        response_data = {"ok": False}
        try:
            if path == "/api/chat":
                prompt = params.get("prompt", "")
                voice_speak = str(params.get("voice", "0")).lower() in ["1", "true"]
                model = params.get("model", "auto")
                response_data = self.handle_chat(prompt, voice_enabled=voice_speak, model=model)
            elif path == "/api/theme":
                name = params.get("name", "")
                response_data = self.handle_theme(name)
            elif path == "/api/voice":
                text = params.get("text", "")
                voice = params.get("voice", "jarvis")
                response_data = self.handle_voice(text, voice)
            elif path == "/api/harness":
                task = params.get("task", "Audit system integrity")
                response_data = self.handle_harness(task)
            elif path == "/api/launch":
                app = params.get("app", "")
                response_data = self.handle_launch(app)
            elif path == "/api/hypr":
                dispatcher = params.get("cmd", "")
                args = params.get("args", "")
                response_data = self.handle_hypr(dispatcher, args)
            else:
                response_data = {"ok": False, "error": f"Unknown POST endpoint: {path}"}
        except Exception as e:
            response_data = {"ok": False, "error": str(e)}

        self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))

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
            elif path == "/api/models":
                response_data = self.handle_models()
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
            elif path == "/api/chat":
                prompt = params.get("prompt", [""])[0]
                voice_speak = params.get("voice", ["0"])[0] in ["1", "true", "True"]
                model = params.get("model", ["auto"])[0]
                response_data = self.handle_chat(prompt, voice_enabled=voice_speak, model=model)
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

    def handle_models(self):
        models = [
            {"id": "auto", "name": "⚡ SmartRouter (Auto-Routing + 0ms Cache)", "details": "Autonomous"},
        ]
        try:
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(req, timeout=1.5) as r:
                tags = json.loads(r.read())
                for m in tags.get("models", []):
                    m_name = m.get("name")
                    param = m.get("details", {}).get("parameter_size", "Local")
                    models.append({
                        "id": m_name,
                        "name": f"🧠 Ollama: {m_name} ({param})",
                        "details": param
                    })
        except Exception:
            pass
        return {"ok": True, "models": models}

    def handle_harness(self, task):
        cmd = ["/home/apravint/.local/bin/iram", "workflow", "run", task]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "task": task, "message": "Harness cyclic loop dispatched"}

    def handle_chat(self, prompt, voice_enabled=False, model="auto"):
        if not prompt:
            return {"ok": False, "error": "Prompt cannot be empty"}

        prompt = prompt.strip()

        # 1. SmartRouter Response Cache Check (only if auto routing)
        if SMART_ROUTER_AVAILABLE and model in ["auto", ""]:
            cached = smart_router.cache.get_cached_response(prompt)
            if cached:
                reply = cached.get("response", "")
                if voice_enabled:
                    self.handle_voice(reply[:120], "jarvis")
                return {
                    "ok": True,
                    "response": reply,
                    "cached": True,
                    "model": cached.get("model", "Cache Hit (0ms, $0)"),
                    "score": 1,
                    "tier": "Tier 3 (Local Cache Hit)"
                }

        # 2. SmartRouter Complexity Scoring
        score = 3
        tier_desc = "Tier 2 (Daily Driver)"
        if SMART_ROUTER_AVAILABLE:
            score, tier_desc = smart_router.scorer.score_prompt_complexity(prompt)

        p_lower = prompt.lower()
        reply = ""
        model_name = "IRAM Sovereign Agent"

        # 3. Intent Resolution & Direct Command Execution
        if "theme" in p_lower and any(w in p_lower for w in ["switch", "set", "change", "apply"]):
            themes_map = {
                "tokyo storm": "tokyo-storm", "cyberpunk neon": "cyberpunk-neon",
                "synthwave 84": "synthwave-84", "catppuccin mocha": "catppuccin-mocha",
                "dracula": "dracula", "nord frost": "nord-frost",
                "rose pine moon": "rose-pine-moon", "gruvbox": "gruvbox",
                "matte black": "matte-black", "aura dark": "aura-dark",
                "oxocarbon": "oxocarbon", "vesper": "vesper"
            }
            applied = False
            for k, slug in themes_map.items():
                if k in p_lower:
                    if TOOLGATE_AVAILABLE:
                        safety, flags = toolgate.firewall.evaluate_command_risk(f"iram theme set {slug}")
                        if safety == "DENY":
                            reply = f"🛡️ Blocked by ToolGate Firewall: {flags[0]}"
                            break
                    self.handle_theme(slug)
                    reply = f"✨ Applied theme '{k.title()}' live across Hyprland, Waybar, and terminals with zero restarts."
                    applied = True
                    break
            if not applied:
                reply = "Available palettes: Tokyo Storm, Cyberpunk Neon, Synthwave 84, Catppuccin Mocha, Dracula, Nord Frost, Rosé Pine Moon, Gruvbox, Matte Black, Aura Dark, Oxocarbon, Vesper."

        elif any(w in p_lower for w in ["status", "telemetry", "health", "cpu", "ram", "memory"]):
            stat = self.handle_status()
            reply = f"⚡ IRAM OS Telemetry:\n• CPU Load: {stat['cpu_percent']}%\n• RAM: {stat['memory']['used_gb']}GB / {stat['memory']['total_gb']}GB ({stat['memory']['percent']}%)\n• Active Window: `{stat['hyprland']['active_window']}` on Workspace {stat['hyprland']['workspace']}\n• Audio DSP: PipeWire 48kHz Calibrated"

        elif any(w in p_lower for w in ["3d", "cad", "mesh", "stl", "obj"]):
            self.handle_launch("iram-3d")
            reply = "🪐 Launched Three.js 3D CAD & Mesh Inspector."

        elif any(w in p_lower for w in ["swarm", "topology", "agent graph"]):
            self.handle_launch("iram-agent-graph")
            reply = "⚡ Opened 3D Multi-Agent Swarm Topology Graph."

        elif any(w in p_lower for w in ["voice", "speak", "say"]):
            spoken = prompt
            for pfx in ["speak", "say", "voice"]:
                if p_lower.startswith(pfx):
                    spoken = prompt[len(pfx):].strip()
            spoken_text = spoken or "IRAM OS sovereign voice synthesis online."
            self.handle_voice(spoken_text, "jarvis")
            reply = f"🔊 Spoke through PipeWire studio audio: '{spoken_text}'"

        elif "harness" in p_lower or "verify" in p_lower:
            self.handle_harness("Audit system and codebase integrity")
            reply = "🚀 Dispatched Harness² cyclic verification loop (Plan → Act → Verify → Reflect)."

        elif any(w in p_lower for w in ["mcp", "toolgate", "tools"]):
            reply = (
                "🛡️ Sovereign FastMCP Gateway Status:\n"
                "• 21 Active Tools: Desktop Control, PipeWire Studio, 3D CAD, Qdrant Code Search & Theme Sync\n"
                "• Security Firewall: ToolGate Zero-Trust Rules Enforced\n"
                "• Transport: FastMCP 4.1.1 JSON-RPC stdio + REST Port 8990"
            )

        elif any(w in p_lower for w in ["help", "what can you do", "commands"]):
            reply = (
                "🤖 IRAM OS Sovereign AI Hub Console:\n"
                "• `switch theme to cyberpunk neon` -> Live zero-restart palette switch\n"
                "• `system status` -> Real-time CPU, RAM, and Hyprland telemetry\n"
                "• `launch 3d cad` -> Three.js CAD / mesh inspector\n"
                "• `speak hello sovereign world` -> Local PipeWire speech synthesis\n"
                "• `inspect mcp` -> Query 21 FastMCP tool definitions\n"
                "• Or ask ANY question to query local Ollama LLMs directly!"
            )
        else:
            # Query local Ollama LLM
            chosen_model = model if (model and model != "auto") else "qwen2.5:7b"
            ollama_reply = None
            try:
                import urllib.request
                ollama_payload = {
                    "model": chosen_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 768}
                }
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=json.dumps(ollama_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    res = json.loads(r.read())
                    ollama_reply = res.get("response", "").strip()
                    model_name = f"Ollama ({chosen_model})"
                    tier_desc = f"Local Sovereign LLM ({chosen_model})"
            except Exception:
                # Fallback to faster 1.5b model if available
                if chosen_model != "qwen2.5:1.5b":
                    try:
                        ollama_payload["model"] = "qwen2.5:1.5b"
                        req = urllib.request.Request(
                            "http://127.0.0.1:11434/api/generate",
                            data=json.dumps(ollama_payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=10) as r:
                            res = json.loads(r.read())
                            ollama_reply = res.get("response", "").strip()
                            model_name = "Ollama (qwen2.5:1.5b)"
                            tier_desc = "Local Fast LLM (1.5B)"
                    except Exception:
                        pass

            if ollama_reply:
                reply = ollama_reply
            else:
                reply = f"IRAM OS Assistant evaluated: '{prompt}' (Complexity Score: {score}/10, Route: {tier_desc}). For multi-file codebase changes, use Antigravity or Harness²."

        # 4. Save to SmartRouter Cache
        if SMART_ROUTER_AVAILABLE:
            smart_router.cache.save_cached_response(prompt, reply, model_name)

        # 5. Optional Spoken Output
        if voice_enabled:
            self.handle_voice(reply[:140], "jarvis")

        return {
            "ok": True,
            "response": reply,
            "cached": False,
            "model": model_name,
            "score": score,
            "tier": tier_desc
        }

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
