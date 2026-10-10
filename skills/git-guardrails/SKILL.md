---
name: git-guardrails
description: Safety guardrails preventing destructive git commands, accidental loss of uncommitted work, and dangerous force pushes during agent execution.
---

# Git Guardrails Protocol (Matt Pocock Architecture)

A safety gasket preventing AI coding agents from executing destructive git commands that wipe uncommitted human work or destroy commit histories.

---

## 🚫 Strictly Forbidden Git Invocations

An agent must **never** run:
1. `git reset --hard` (unless explicitly instructed with commit hash by the human engineer).
2. `git clean -fd` or `git clean -xdf` (permanently deletes untracked human files).
3. `git push --force` or `git push -f` to protected branches (`main`, `master`, `production`).
4. `git checkout -f` or `git restore .` when uncommitted human modifications exist.
5. `git branch -D` on unmerged branches without confirmation.

---

## 🛡️ Safe Operating Principles

1. **Check Status First**: Run `git status` before executing any staging, committing, or branch switching.
2. **Stash Before Switching**: Use `git stash push -m "agent-wip-..."` to preserve working directory state safely.
3. **Discrete Atomic Commits**: Commit changes with conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
4. **Isolated Worktrees**: When exploring experimental spikes or parallel features, prefer `git worktree add` to avoid altering the active checkout.
