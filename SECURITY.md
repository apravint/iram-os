# Security Policy

IRAM OS ships an MCP server that lets AI agents act on a desktop, so security reports are taken seriously. The policy boundary lives in [`bin/iram_policy.py`](bin/iram_policy.py) and the permission tiers are described in the [README](README.md#what-makes-it-different).

## Supported versions

Only the latest release and the `main` branch receive fixes.

## Reporting a vulnerability

Please **do not open a public issue** for a vulnerability. Use GitHub's private reporting instead:

1. Go to the [Security tab](https://github.com/apravint/iram-os/security/advisories/new) of this repository.
2. Choose **Report a vulnerability** and describe the problem, affected component, and steps to reproduce.

Useful details: the output of `iram doctor`, the MCP permission tier you were running (`read`, `desktop`, `privileged`), and whether the issue needs local access or a malicious web page or model output.

This is a volunteer-run project, so there is no fixed response SLA. Reports are acknowledged on a best-effort basis, and credit is given in the fix unless you prefer otherwise.

## In scope

- Bypasses of the MCP tier policy or argument validation (for example reaching `exec`, shell injection, path traversal)
- Secrets leaking into logs, `ps` output, or screenshots
- Unsafe archive handling in `iram snapshot restore`
- The Hub or agent daemon accepting browser-forged requests

## Out of scope

- Anything that requires you to run the unrestricted command shown by `iram-ai-cmd`
- The optional FastMCP SSE service, which is documented as unauthenticated and off by default
- Vulnerabilities in upstream projects (Hyprland, Waybar, Ollama, Ubuntu); please report those upstream
