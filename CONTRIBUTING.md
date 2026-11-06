# Contributing to IRAM OS

Thanks for helping. Bug reports with `iram doctor` output are the single most useful contribution. Developer notes for the codebase are in [AGENTS.md](AGENTS.md).

## Setup

```bash
git clone https://github.com/apravint/iram-os.git && cd iram-os
./install.sh --dry-run        # prints every change, modifies nothing
```

You only need Python 3.12+ and Bash to run the tests. No root, compositor, or network is required.

## Before opening a pull request

```bash
bash tests/run.sh                                  # full suite (Python unittest + shell checks)
python3 tests/test_ai_core.py -v                   # a single test module
shellcheck -S error install.sh build/*.sh migrations/*.sh tests/run.sh
ruff check --select E9,F63,F7,F82 .                # Python syntax errors and undefined names
```

CI (`.github/workflows/ci.yml`) runs the same checks plus package builds and an installer dry run.

## Guidelines

- Keep pull requests focused: one change, one PR.
- Add or update a test with any behaviour change. Tests that touch the filesystem must use a temp directory and never `$HOME`.
- The MCP server uses only the Python standard library. Do not add pip dependencies to `bin/iram_policy.py` or `bin/iram_mcp_server.py`.
- Anything that widens what an agent can do (a new tool, a new allowed command) needs a test showing which tier gates it and what is refused.
- Shell scripts must pass `shellcheck -S error`.
- Use clear commit messages in the imperative mood ("Fix GPU detection on hybrid laptops").

## Reporting problems

- Bugs and feature requests: use the [issue templates](https://github.com/apravint/iram-os/issues/new/choose).
- Security issues: follow [SECURITY.md](SECURITY.md). Do not file them publicly.

By contributing you agree that your work is released under the [MIT License](LICENSE).
