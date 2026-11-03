#!/usr/bin/env python3
"""
IRAM OS shared security policy.
One definition of what an agent or a local HTTP client may do, used by
iram-agent, iram-agent-daemon, iram-hub-server.py, iram-mcp-server and iram-os-mcp.
https://github.com/apravint/iram-os
"""

import re
import shlex
from typing import List, Optional, Tuple
from urllib.parse import urlparse

# hyprctl dispatchers that only rearrange the desktop. `exec`, `execr` and
# `global` run arbitrary programs and must never be reachable from an agent.
SAFE_HYPR_DISPATCHERS = frozenset({
    "workspace", "movetoworkspace", "movetoworkspacesilent", "togglespecialworkspace",
    "focuswindow", "focusmonitor", "movefocus", "movewindow", "swapwindow",
    "togglefloating", "setfloating", "settiled", "fullscreen", "pin", "centerwindow",
    "resizeactive", "moveactive", "cyclenext", "togglesplit", "killactive", "closewindow",
    "dpms",
})

READ_ONLY_HYPRCTL = frozenset({
    "activewindow", "activeworkspace", "clients", "workspaces", "monitors",
    "layers", "devices", "binds", "getoption", "version",
})

# `iram` subcommands an unattended agent may run. Excludes update, snapshot
# restore, install and anything that downloads or rewrites the system.
SAFE_IRAM_SUBCOMMANDS = frozenset({
    "theme", "info", "doctor", "audio", "bar", "brightness", "weather", "toggle",
})

SAFE_AGENT_BINARIES = frozenset({"hyprctl", "iram", "notify-send", "pactl", "wpctl"})
SAFE_PACTL_VERBS = frozenset({
    "info", "list", "get-default-sink", "get-sink-volume", "get-sink-mute",
    "set-sink-volume", "set-sink-mute", "set-default-sink",
})
SAFE_WPCTL_VERBS = frozenset({"status", "inspect", "get-volume", "set-volume", "set-mute", "set-default"})

# Quotes are left out: shlex handles them, and without a shell they are inert.
SHELL_METACHARACTERS = re.compile(r"[;&|<>`$\\\n\r]")

UNIT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9@_.:-]{0,127}\.(service|timer|socket|target|path)$")

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

# Password managers and secret prompts. Their contents never reach an agent,
# whether as clipboard text or as pixels.
SENSITIVE_WINDOW_CLASSES = ("keepass", "bitwarden", "1password", "lastpass", "pinentry", "seahorse", "protonpass", "gcr-prompter")

# Common credential shapes, masked before text reaches a model or a log.
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"\b(?:sk|pk|rk)-(?:ant-|proj-|live-|test-)?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{30,}"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"),
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\b(\s*[=:]\s*)\S+"),
)


def redact_secrets(text: str) -> str:
    """Mask credential-shaped substrings, keeping the key name of key=value pairs."""
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 2:
            text = pattern.sub(r"\1\2[REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text


def is_valid_unit(name: str) -> bool:
    return isinstance(name, str) and bool(UNIT_NAME.match(name))


def is_sensitive_window(window_class: str) -> bool:
    return isinstance(window_class, str) and any(s in window_class.lower() for s in SENSITIVE_WINDOW_CLASSES)


def is_safe_dispatcher(dispatcher: str) -> bool:
    return dispatcher in SAFE_HYPR_DISPATCHERS


def parse_agent_command(line: str) -> Tuple[Optional[List[str]], str]:
    """
    Turn one line of model output into an argv list, or explain why not.
    The result is run without a shell, so a line can only ever start one
    allowlisted program with literal arguments.
    """
    if SHELL_METACHARACTERS.search(line):
        return None, "contains shell metacharacters"
    try:
        argv = shlex.split(line)
    except ValueError as exc:
        return None, f"unparsable: {exc}"
    if not argv:
        return None, "empty"

    binary = argv[0]
    if binary not in SAFE_AGENT_BINARIES:
        return None, f"'{binary}' is not an allowlisted binary"

    verb = argv[1] if len(argv) > 1 else ""
    if binary == "hyprctl":
        flagless = [a for a in argv[1:] if not a.startswith("-")]
        verb = flagless[0] if flagless else ""
        if verb == "dispatch":
            target = flagless[1] if len(flagless) > 1 else ""
            if not is_safe_dispatcher(target):
                return None, f"hyprctl dispatcher '{target}' is not allowlisted"
        elif verb not in READ_ONLY_HYPRCTL:
            return None, f"hyprctl '{verb}' is not allowlisted"
    elif binary == "iram":
        if verb not in SAFE_IRAM_SUBCOMMANDS:
            return None, f"iram subcommand '{verb}' is not allowlisted"
    elif binary == "pactl":
        if verb not in SAFE_PACTL_VERBS:
            return None, f"pactl '{verb}' is not allowlisted"
    elif binary == "wpctl":
        if verb not in SAFE_WPCTL_VERBS:
            return None, f"wpctl '{verb}' is not allowlisted"
    return argv, ""


def check_local_request(headers, require_json: bool = False) -> Optional[str]:
    """
    Refuse requests a web page could have forged against a loopback service.
    Binding to 127.0.0.1 does not stop a browser: any site can POST here, and
    DNS rebinding can read the replies. Returns a refusal reason, or None.
    Non-browser clients send none of these headers and pass.
    """
    host = (headers.get("Host") or "").strip()
    hostname = urlparse(f"//{host}").hostname if host else None
    if hostname is not None and hostname not in LOOPBACK_HOSTS:
        return f"Host '{host}' is not loopback"

    fetch_site = (headers.get("Sec-Fetch-Site") or "").strip().lower()
    if fetch_site in ("cross-site", "same-site"):
        return f"Sec-Fetch-Site is {fetch_site}"

    origin = (headers.get("Origin") or "").strip()
    if origin and urlparse(origin).netloc != host:
        return f"Origin '{origin}' does not match Host"

    if require_json:
        # text/plain and form posts skip the CORS preflight; JSON does not.
        content_type = (headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if content_type != "application/json":
            return "Content-Type must be application/json"
    return None
