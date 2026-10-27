#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Sovereign Developer Shell Suite & Workflow Accelerators
# Features: Tmux Dev Layouts (tdl/tds/tsl), Git Worktrees (gwa/gwd/gwl),
# Fast Compression, SSH Port Forwarding, and Background Rsync Watchers.
# Inspired by Omarchy 4.5 & Enhanced for IRAM OS
# https://github.com/apravint/iram-os
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. ARCHIVES & COMPRESSION
# ------------------------------------------------------------------------------
compress() {
    if [[ -z "${1:-}" ]]; then
        echo "Usage: compress <file_or_directory>" >&2
        return 1
    fi
    local target="${1%/}"
    tar -czvf "${target}.tar.gz" "$target"
}

decompress() {
    if [[ -z "${1:-}" ]]; then
        echo "Usage: decompress <archive.tar.gz|archive.tgz>" >&2
        return 1
    fi
    tar -xzvf "$1"
}

# ------------------------------------------------------------------------------
# 2. GIT WORKTREE ACCELERATORS (gwa = Git Worktree Add, gwd = Git Worktree Delete)
# ------------------------------------------------------------------------------
gwa() {
    if [[ -z "${1:-}" ]]; then
        echo "Usage: gwa <branch-name>" >&2
        return 1
    fi

    local branch="$1"
    local base
    base="$(basename "$PWD")"
    local wt_path="../${base}--${branch}"

    echo "Creating worktree for branch '$branch' at '$wt_path'..."
    git worktree add -b "$branch" "$wt_path"
    cd "$wt_path"
}

gwd() {
    local cwd
    cwd="$(pwd)"
    local worktree
    worktree="$(basename "$cwd")"

    local root="${worktree%%--*}"
    local branch="${worktree#*--}"

    if [[ "$root" == "$worktree" ]]; then
        echo "Error: Not currently inside a worktree directory (expected <repo>--<branch>)." >&2
        return 1
    fi

    printf "Remove worktree '%s' and delete branch '%s'? [y/N] " "$worktree" "$branch"
    local REPLY
    read -r REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "../$root"
        git worktree remove "$cwd" --force || return 1
        git branch -D "$branch" 2>/dev/null || true
        echo "Worktree and branch '$branch' removed."
    fi
}

gwl() {
    git worktree list
}

# Worktree helper aliases
alias gwt-add=gwa
alias gwt-del=gwd
alias gwt-list=gwl

# ------------------------------------------------------------------------------
# 3. TMUX AI & DEVELOPER LAYOUTS
# ------------------------------------------------------------------------------
tdl() {
    local default_ai="agy"
    if [[ ! -x "$(which agy 2>/dev/null)" ]]; then
        default_ai="bash"
    fi
    local ai="${1:-$default_ai}"
    local ai2="${2:-}"

    if [[ -z "${TMUX:-}" ]]; then
        # If not inside tmux, start a new session running tdl
        tmux new-session -s "dev-$(basename "$PWD")" "bash -c 'source /usr/share/iram/config/shell/functions.sh 2>/dev/null || source $HOME/iram-os/config/shell/functions.sh; tdl $ai $ai2; exec bash'"
        return 0
    fi

    local current_dir="${PWD}"
    local editor_pane="$TMUX_PANE"

    tmux rename-window -t "$editor_pane" "$(basename "$current_dir")"

    # Split bottom 15% for terminal
    tmux split-window -v -p 15 -t "$editor_pane" -c "$current_dir"

    # Split right 35% for AI agent
    local ai_pane
    ai_pane=$(tmux split-window -h -p 35 -t "$editor_pane" -c "$current_dir" -P -F '#{pane_id}')

    if [[ -n "$ai2" ]]; then
        local ai2_pane
        ai2_pane=$(tmux split-window -v -t "$ai_pane" -c "$current_dir" -P -F '#{pane_id}')
        tmux send-keys -t "$ai2_pane" "$ai2" C-m
    fi

    tmux send-keys -t "$ai_pane" "$ai" C-m

    local editor_cmd="${EDITOR:-nvim} ."
    tmux send-keys -t "$editor_pane" "$editor_cmd" C-m
    tmux select-pane -t "$editor_pane"
}

tds() {
    if [[ -z "${TMUX:-}" ]]; then
        tmux new-session -s "dev-$(basename "$PWD")" "bash -c 'source /usr/share/iram/config/shell/functions.sh 2>/dev/null || source $HOME/iram-os/config/shell/functions.sh; tds; exec bash'"
        return 0
    fi

    local current_dir="${PWD}"
    local editor_pane="$TMUX_PANE"

    tmux rename-window -t "$editor_pane" "$(basename "$current_dir")"

    local term_pane diff_pane agent_pane
    term_pane=$(tmux split-window -v -p 50 -t "$editor_pane" -c "$current_dir" -P -F '#{pane_id}')
    diff_pane=$(tmux split-window -h -p 50 -t "$editor_pane" -c "$current_dir" -P -F '#{pane_id}')
    agent_pane=$(tmux split-window -h -p 50 -t "$term_pane" -c "$current_dir" -P -F '#{pane_id}')

    tmux send-keys -t "$editor_pane" "${EDITOR:-nvim} ." C-m
    tmux send-keys -t "$diff_pane" "git status" C-m
    tmux send-keys -t "$agent_pane" "agy" C-m
    tmux select-pane -t "$editor_pane"
}

tsl() {
    local count="${1:-4}"
    local cmd="${2:-agy}"

    if [[ -z "${TMUX:-}" ]]; then
        echo "Error: tsl must be run inside a tmux session." >&2
        return 1
    fi

    local current_dir="${PWD}"
    local root_pane="$TMUX_PANE"
    local -a panes=("$root_pane")

    tmux rename-window -t "$root_pane" "swarm-$(basename "$current_dir")"

    while (( ${#panes[@]} < count )); do
        local split_target="${panes[-1]}"
        local new_pane
        new_pane=$(tmux split-window -h -t "$split_target" -c "$current_dir" -P -F '#{pane_id}')
        panes+=("$new_pane")
        tmux select-layout -t "$root_pane" tiled
    done

    for pane in "${panes[@]}"; do
        tmux send-keys -t "$pane" "$cmd" C-m
    done

    tmux select-pane -t "$root_pane"
}

# ------------------------------------------------------------------------------
# 4. SSH LOCALHOST PORT FORWARDING & RECONNECT
# ------------------------------------------------------------------------------
fip() {
    if [[ $# -lt 2 ]]; then
        echo "Usage: fip <host> <port> [remote_port]" >&2
        return 1
    fi
    local host="$1"
    local port="$2"
    local rport="${3:-$port}"

    echo "Forwarding localhost:$port -> $host:$rport..."
    ssh -f -N -L "${port}:localhost:${rport}" "$host"
    echo "✓ Port forward established: http://localhost:$port"
}

lip() {
    echo "Active SSH port forwards:"
    ps aux | grep -E "[s]sh -f -N -L" | awk '{print $2, $(NF-1), $NF}' || echo "No active port forwards."
}

dip() {
    if [[ -z "${1:-}" ]]; then
        echo "Usage: dip <port>" >&2
        return 1
    fi
    local port="$1"
    local pids
    pids=$(ps aux | grep -E "[s]sh -f -N -L ${port}:" | awk '{print $2}')
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        echo "✓ Forward for port $port closed."
    else
        echo "No forward found for port $port."
    fi
}
