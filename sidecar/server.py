#!/usr/bin/env python3
"""
IRAM OS - Sovereign Gemini-Grade Desktop Sidecar Server
FastAPI + SSE streaming backend powering an ultra-responsive, beautiful
Gemini chat interface with autonomous computer-use tool calling.
https://github.com/apravint/iram-os
"""

import os
import sys
import json
import re
import time
import base64
import subprocess
import urllib.request
import urllib.error
from typing import AsyncGenerator, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# AI Core Integration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "bin"))
if BIN_DIR not in sys.path:
    sys.path.insert(0, BIN_DIR)

from iram_ai_core import (
    get_gemini_api_key,
    is_gemini_healthy,
    is_ollama_available,
    hindsight_recall,
    hindsight_retain,
    get_default_models
)

app = FastAPI(title="IRAM OS Gemini Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(SCRIPT_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

FORBIDDEN_PATTERNS = [
    r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--force)\s+/\s*$",
    r"mkfs",
    r"dd\s+if=.*of=/dev/(sd[a-z]|nvme[0-9]n[0-9])",
    r":\(\)\s*\{\s*:\|:&\s*\};:",
    r">\s*/dev/sd[a-z]",
]

SYSTEM_PROMPT = """You are the IRAM OS Gemini Assistant running natively on Ubuntu 26.10 with Hyprland 0.56.
You are ultra-fast, helpful, intelligent, and possess direct authority to inspect this computer and control desktop actions.

AVAILABLE SYSTEM TOOLS:
- `iram network [scan|watch|info]` : Wi-Fi radar (scan and identify all devices, MAC vendors, new client alerts).
- `iram quant [all|us|in]` : Algorithmic stock market leader radar (200 SMA regime filter, ATR position sizing).
- `iram theme [list|current|set <name>|next]` : 43 curated themes with zero-restart hot-reloading.
- `iram info` : OS status HUD (kernel, distribution, theme, memory, compositor).
- `ss -tulpn` : Inspect listening network ports, sockets, and active connections.
- `iram audit [path]` : Adversarial code and repository vulnerability auditor.
- `iram craft <app>` : Storytold creative apps (photo, vector, film, sound, cad, word, grid, deck, pdf).
- `iram ocr` : Screen region OCR text extraction to clipboard.
- `iram capture [screenshot|screenrecord|webcam|qr]` : Desktop capture suite.
- `iram toggle-idle` : Stay Awake / Allow Sleep lock inhibitor.
- `iram waybar-autohide [toggle|status]` : Edge-triggered Waybar autohide daemon.
- `hyprctl dispatch <action>` : Workspace and window focus, move, kill.
- `wpctl` / `pactl` : PipeWire volume and audio sink management.
- Linux utilities: `df -h`, `free -h`, `uptime`, `ip a`, `ss -tulpn`, `systemctl`, `journalctl`.

AUTONOMOUS TOOL EXECUTION RULE:
If the user's question asks to inspect system state (disk space, RAM, network devices, stock picks, open ports, playing audio) or execute a desktop action (change theme, adjust volume, stay awake):
You MUST call the tool on your first turn using the exact syntax:
[TOOL: <bash command>]

Examples:
- User: "who is on my wifi?" -> [TOOL: iram network scan]
- User: "what are the best momentum stocks in india and US?" -> [TOOL: iram quant all]
- User: "how much disk space is left?" -> [TOOL: df -h /]
- User: "switch my theme to Dracula" -> [TOOL: iram theme set Dracula]
- User: "are there any open ports?" -> [TOOL: ss -tulpn]
- User: "check for suspicious open listening ports" -> [TOOL: ss -tulpn]
- User: "run security audit on codebase" -> [TOOL: iram audit]
- User: "what audio is playing?" -> [TOOL: playerctl metadata]
- User: "turn volume down to 40%" -> [TOOL: wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.40]

After the tool runs, you will be given the output to provide a friendly, beautifully formatted markdown response with key takeaways.
"""


def get_system_env() -> Dict[str, str]:
    """Builds a comprehensive runtime environment with user binaries and Wayland display."""
    env = os.environ.copy()
    user_bin = os.path.expanduser("~/.local/bin")
    iram_bin = os.path.expanduser("~/iram-os/bin")
    current_path = env.get("PATH", "")
    env["PATH"] = f"{user_bin}:{iram_bin}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:{current_path}"

    runtime_dir = env.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    env["XDG_RUNTIME_DIR"] = runtime_dir

    # Auto-detect Hyprland signature if running under systemd
    if "HYPRLAND_INSTANCE_SIGNATURE" not in env:
        hypr_dir = os.path.join(runtime_dir, "hypr")
        if os.path.isdir(hypr_dir):
            try:
                sigs = [d for d in os.listdir(hypr_dir) if not d.endswith(".lock")]
                if sigs:
                    env["HYPRLAND_INSTANCE_SIGNATURE"] = sigs[0]
            except Exception:
                pass

    if "WAYLAND_DISPLAY" not in env:
        for w in ["wayland-1", "wayland-0"]:
            if os.path.exists(os.path.join(runtime_dir, w)):
                env["WAYLAND_DISPLAY"] = w
                break

    return env


def is_safe_command(cmd: str) -> bool:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cmd.strip(), re.IGNORECASE):
            return False
    return True


def run_tool_command(cmd: str) -> str:
    if not is_safe_command(cmd):
        return "Blocked by IRAM Safety Guardrails: potentially destructive command prevented."
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            env=get_system_env(),
            capture_output=True,
            text=True,
            timeout=30
        )
        out = proc.stdout.strip() if proc.stdout else proc.stderr.strip()
        return out if out else "(Command executed successfully with no output)"
    except subprocess.TimeoutExpired:
        return f"Tool execution timed out after 30s: `{cmd}`"
    except Exception as e:
        return f"Tool execution error: {str(e)}"


def parse_tool_invocation(text: str) -> Optional[str]:
    m = re.search(r'\[TOOL:\s*(.+?)\]', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'\[EXEC:\s*(.+?)\]', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


async def stream_gemini(prompt: str, system_instruction: str = SYSTEM_PROMPT, model: str = "gemini-3.5-flash") -> AsyncGenerator[str, None]:
    key = get_gemini_api_key()
    if not key:
        yield "Error: Google Gemini API key is not configured."
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={key}"
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    try:
                        data_json = json.loads(line_str[5:].strip())
                        candidates = data_json.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                if "text" in p:
                                    yield p["text"]
                    except Exception:
                        continue
    except urllib.error.HTTPError as e:
        # Fallback to flash-lite if standard flash spikes
        if model != "gemini-3.5-flash-lite":
            async for chunk in stream_gemini(prompt, system_instruction, model="gemini-3.5-flash-lite"):
                yield chunk
        else:
            yield f"Gemini API Error ({e.code}): {e.reason}"
    except Exception as e:
        yield f"Connection Error: {str(e)}"


async def stream_ollama(prompt: str, system_instruction: str = SYSTEM_PROMPT, model: str = "qwen2.5:1.5b") -> AsyncGenerator[str, None]:
    url = "http://127.0.0.1:11434/api/generate"
    full_prompt = f"{system_instruction}\n\nTask: {prompt}"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": 384}
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str:
                    try:
                        data_json = json.loads(line_str)
                        chunk = data_json.get("response", "")
                        if chunk:
                            yield chunk
                    except Exception:
                        continue
    except Exception as e:
        yield f"Ollama Error: {str(e)}"


@app.get("/")
async def get_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"status": "IRAM OS Gemini Sidecar running"})


@app.get("/api/health")
async def get_health():
    key_present = bool(get_gemini_api_key())
    gemini_up = key_present and is_gemini_healthy()
    ollama_up = is_ollama_available()

    # Get system RAM
    mem_info = "Unknown"
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    kb = int(line.split()[1])
                    mem_info = f"{kb // 1024} MB available"
                    break
    except Exception:
        pass

    return {
        "gemini": gemini_up,
        "ollama": ollama_up,
        "preferred": "gemini" if gemini_up else "ollama",
        "memory": mem_info,
        "compositor": "Hyprland 0.56.2"
    }


@app.post("/api/screenshot")
async def capture_screenshot():
    """Captures screenshot using grim and returns base64 image data."""
    tmp_path = "/tmp/iram_sidecar_snap.png"
    try:
        subprocess.run(["grim", tmp_path], check=True, timeout=5, env=get_system_env())
        with open(tmp_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        return {"success": True, "image": f"data:image/png;base64,{img_b64}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/theme")
async def get_theme():
    """Returns current active IRAM OS theme name and palette."""
    theme_name = "dracula"
    try:
        proc = subprocess.run(["iram", "theme", "current"], env=get_system_env(), capture_output=True, text=True, timeout=2)
        if proc.stdout.strip():
            theme_name = proc.stdout.strip().lower()
    except Exception:
        pass
    return {"theme": theme_name}


@app.get("/api/system_stats")
async def get_system_stats():
    """Returns live RAM, CPU load, and Wi-Fi SSID."""
    stats = {
        "ram_used_mb": 0,
        "ram_total_mb": 0,
        "ram_pct": 0,
        "load_avg": 0.0,
        "wifi_ssid": "Disconnected",
        "pinned": False
    }
    try:
        with open('/proc/meminfo') as f:
            lines = f.readlines()
        mem = {}
        for l in lines:
            parts = l.split(':')
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].strip().split()[0])
        total_mb = mem.get('MemTotal', 0) // 1024
        avail_mb = mem.get('MemAvailable', 0) // 1024
        used_mb = total_mb - avail_mb
        stats["ram_total_mb"] = total_mb
        stats["ram_used_mb"] = used_mb
        stats["ram_pct"] = round((used_mb / total_mb) * 100, 1) if total_mb else 0
    except Exception:
        pass

    try:
        stats["load_avg"] = round(os.getloadavg()[0], 2)
    except Exception:
        pass

    try:
        proc = subprocess.run(
            'iwgetid -r 2>/dev/null || nmcli -t -f active,ssid dev wifi | grep "^yes" | cut -d: -f2 | head -1',
            shell=True, env=get_system_env(), capture_output=True, text=True, timeout=2
        )
        ssid = proc.stdout.strip().split("\n")[0]
        if ssid:
            stats["wifi_ssid"] = ssid
    except Exception:
        pass

    # Check pinned status
    try:
        proc = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            env=get_system_env(), capture_output=True, text=True, timeout=1
        )
        data = json.loads(proc.stdout)
        stats["pinned"] = bool(data.get("pinned", False))
    except Exception:
        pass

    return stats


@app.post("/api/pin")
async def toggle_pin():
    """Toggles Hyprland pin state on the active window."""
    try:
        subprocess.run(["hyprctl", "dispatch", "pin", "active"], env=get_system_env(), timeout=1)
        # Check new state
        proc = subprocess.run(["hyprctl", "activewindow", "-j"], env=get_system_env(), capture_output=True, text=True, timeout=1)
        data = json.loads(proc.stdout)
        return {"success": True, "pinned": bool(data.get("pinned", False))}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/feedback")
async def record_feedback(request: Request):
    """Records thumbs rating into Hindsight memory."""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        rating = data.get("rating", "up")  # "up" or "down"
        hindsight_retain(
            f"User gave thumbs {rating} to prompt: '{prompt}'",
            category="feedback",
            importance=4 if rating == "up" else 5
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Main chat streaming endpoint with autonomous tool calling.
    Emits SSE events:
    - `event: tool_start` -> {"command": "..."}
    - `event: tool_output` -> {"command": "...", "output": "..."}
    - `event: token` -> {"text": "..."}
    - `event: done` -> {}
    """
    data = await request.json()
    user_prompt = data.get("prompt", "").strip()
    model_pref = data.get("model", "auto")  # "gemini", "ollama", or "auto"
    history = data.get("history", [])

    if not user_prompt:
        return JSONResponse({"error": "Empty prompt"}, status_code=400)

    # Decide provider
    use_gemini = True
    if model_pref == "ollama":
        use_gemini = False
    elif model_pref == "auto":
        use_gemini = bool(get_gemini_api_key())

    # Build conversation context
    history_context = ""
    if history:
        turns = []
        for h in history[-4:]:
            role = "USER" if h.get("role") == "user" else "ASSISTANT"
            turns.append(f"{role}: {h.get('content', '')}")
        history_context = "\n".join(turns) + "\n"

    full_query = f"{history_context}USER: {user_prompt}\nASSISTANT:"

    async def sse_event_stream():
        nonlocal use_gemini
        first_pass_text = ""

        # Step 1: Query LLM to see if it calls a tool
        if use_gemini:
            async for chunk in stream_gemini(full_query):
                first_pass_text += chunk
        else:
            async for chunk in stream_ollama(full_query):
                first_pass_text += chunk

        # Check if a tool was invoked
        tool_cmd = parse_tool_invocation(first_pass_text)

        if tool_cmd:
            t0 = time.time()
            # 1. Inform frontend that a tool has started
            yield f"event: tool_start\ndata: {json.dumps({'command': tool_cmd})}\n\n"

            # 2. Execute tool locally on the machine
            tool_output = run_tool_command(tool_cmd)
            duration_s = round(time.time() - t0, 2)

            # 3. Inform frontend of tool result with execution duration
            yield f"event: tool_output\ndata: {json.dumps({'command': tool_cmd, 'output': tool_output, 'duration': duration_s})}\n\n"

            # 4. Synthesize final natural language answer
            truncated_out = tool_output[:1500] + ("..." if len(tool_output) > 1500 else "")
            summary_prompt = (
                f"The user asked: '{user_prompt}'.\n"
                f"The system tool `{tool_cmd}` was executed on the computer and produced this output:\n"
                f"```\n{truncated_out}\n```\n"
                f"Provide a friendly, beautifully formatted markdown response summarizing the findings directly for the user."
            )

            if use_gemini:
                async for chunk in stream_gemini(summary_prompt, system_instruction="You are the IRAM OS Gemini Assistant. Summarize tool findings concisely and helpfully in markdown."):
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
            else:
                async for chunk in stream_ollama(summary_prompt, system_instruction="You are the IRAM OS Gemini Assistant. Summarize tool findings concisely and helpfully in markdown."):
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

        else:
            # No tool invoked: stream the response directly
            yield f"event: token\ndata: {json.dumps({'text': first_pass_text})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
