# IRAM OS Agent Guardrails & Invariants

## Invariant Constraints
1. Destructive Commands: NEVER execute recursive file deletion (`rm -rf /`, `rm -rf ~`), partition modification, or system-wide package purges without explicit user confirmation.
2. Git Safety: NEVER force-push (`git push --force`) to `main` branch or destroy uncommitted work in the repository.
3. Compositor Stability: Do NOT terminate the running compositor (`Hyprland`) or graphical session without direct prompt instruction.
4. Syntactic Validation: Always verify commands before dispatching:
   - For `hyprctl`: verify dispatcher names and valid arguments.
   - For `wpctl` / `pactl`: verify sink/source availability first via `wpctl status`.
5. Non-Interference: Preserve existing window geometries and active workspaces unless specifically requested to reposition or switch them.
