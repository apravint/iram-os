#!/usr/bin/env bash
# IRAM OS test suite. Needs no root, no compositor and no network. Usage: tests/run.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$REPO/bin:$PATH"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0 FAIL=0

ok() { PASS=$((PASS + 1)); }
bad() { FAIL=$((FAIL + 1)); echo "FAIL: $*"; }
check() { # description expected-exit command...
    local desc="$1" want="$2"; shift 2
    local got=0
    "$@" >/dev/null 2>&1 || got=$?
    if [ "$got" = "$want" ]; then ok; else bad "$desc (exit $got, wanted $want)"; fi
}
contains() { # description haystack needle
    case "$2" in *"$3"*) ok ;; *) bad "$1: expected '$3' in: ${2:0:300}" ;; esac
}
lacks() {
    case "$2" in *"$3"*) bad "$1: unexpected '$3' in: ${2:0:300}" ;; *) ok ;; esac
}

python3 "$REPO/tests/test_policy.py" -q || bad "test_policy.py"
python3 "$REPO/tests/test_mcp.py" -q || bad "test_mcp.py"
python3 "$REPO/tests/test_theme_sync.py" -q || bad "test_theme_sync.py"

# ---- GPU profiles ---------------------------------------------------------------
fake_gpu() { # root card vendor boot_vga
    mkdir -p "$1/class/drm/$2/device"
    echo "$3" > "$1/class/drm/$2/device/vendor"
    echo "$4" > "$1/class/drm/$2/device/boot_vga"
}
gpu() { IRAM_SYS_ROOT="$1" IRAM_VIRT="$2" IRAM_NVIDIA_LOADED="$3" iram-gpu-env "$4"; }

R="$WORK/amd"; fake_gpu "$R" card0 0x1002 1
OUT="$(gpu "$R" none false --shell)"
contains "AMD gets radeonsi" "$OUT" "LIBVA_DRIVER_NAME=radeonsi"
lacks "AMD gets no NVIDIA vars" "$OUT" "GBM_BACKEND"
lacks "AMD keeps hardware cursors" "$(gpu "$R" none false --hypr)" "no_hardware_cursors"

R="$WORK/nvidia"; fake_gpu "$R" card0 0x10de 1
contains "NVIDIA gets GBM" "$(gpu "$R" none true --shell)" "GBM_BACKEND=nvidia-drm"
contains "NVIDIA gets software cursor" "$(gpu "$R" none true --hypr)" "no_hardware_cursors = true"
lacks "nouveau gets no NVIDIA vars" "$(gpu "$R" none false --shell)" "GBM_BACKEND"

R="$WORK/hybrid"; fake_gpu "$R" card0 0x10de 0; fake_gpu "$R" card1 0x8086 1
OUT="$(gpu "$R" none true --shell)"
contains "Optimus prefers iGPU" "$OUT" "AQ_DRM_DEVICES=/dev/dri/card1:/dev/dri/card0"
lacks "Optimus must not force GBM" "$OUT" "GBM_BACKEND"

R="$WORK/vm"; fake_gpu "$R" card0 0x1af4 1
OUT="$(gpu "$R" kvm false --shell)"
contains "VM gets software cursor" "$OUT" "WLR_NO_HARDWARE_CURSORS=1"
lacks "KVM keeps virgl GL" "$OUT" "LIBGL_ALWAYS_SOFTWARE"
contains "VMware forces software GL" "$(gpu "$R" vmware false --shell)" "LIBGL_ALWAYS_SOFTWARE=1"
contains "VM disables blur" "$(gpu "$R" oracle false --hypr)" "enabled = false"

# ---- Theme engine ---------------------------------------------------------------
THEME_TOTAL=0
for theme in "$REPO"/themes/*/; do
    THEME_TOTAL=$((THEME_TOTAL + 1))
    name="$(basename "$theme")"
    out="$WORK/render/$name"
    mkdir -p "$out"
    cp "$theme/colors.toml" "$out/"
    if ! IRAM_PATH="$REPO" bash "$REPO/bin/iram-theme-set-templates" "$out" 2>"$WORK/err"; then
        bad "theme $name: render failed: $(cat "$WORK/err")"
        continue
    fi
    [ -f "$out/alacritty.toml" ] || bad "theme $name: no alacritty.toml rendered"
    if grep -rlE '\{\{ *[a-z_0-9]+ *\}\}' "$out" >/dev/null 2>&1; then
        bad "theme $name: unresolved tokens in $(grep -rlE '\{\{ *[a-z_0-9]+ *\}\}' "$out" | xargs -n1 basename | tr '\n' ' ')"
    else
        ok
    fi
    while IFS=$'\t' read -r key value; do
        case "$key" in
            mode|theme_type|name) ;;
            *) [[ "$value" =~ ^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$ ]] || [[ "$key" != *background* && "$key" != foreground && "$key" != accent ]] || bad "theme $name: $key=$value is not hex" ;;
        esac
    done < <(iram-theme-color --file "$theme/colors.toml" --all)
done
[ "$THEME_TOTAL" -gt 0 ] && ok || bad "no themes found"

# Toolkit sync: light and dark, against a fake gsettings
TK="$WORK/tk"; mkdir -p "$TK/bin"
printf '#!/bin/sh\necho "$*" >> "%s/gsettings.log"\n' "$TK" > "$TK/bin/gsettings"; chmod +x "$TK/bin/gsettings"
LIGHT="$(grep -lE '^mode *= *"light"' "$REPO"/themes/*/colors.toml | head -n 1)"
if [ -n "$LIGHT" ]; then
    HOME="$TK" PATH="$TK/bin:$PATH" iram-theme-set-toolkits "$LIGHT" || bad "toolkit sync failed for light theme"
    contains "light theme prefers light" "$(cat "$TK/gsettings.log")" "color-scheme prefer-light"
    contains "light GTK ini" "$(cat "$TK/.config/gtk-3.0/settings.ini")" "gtk-application-prefer-dark-theme=0"
fi
: > "$TK/gsettings.log"
echo 'custom_key=keep' >> "$TK/.config/qt6ct/qt6ct.conf"
HOME="$TK" PATH="$TK/bin:$PATH" iram-theme-set-toolkits "$REPO/themes/tokyo-storm/colors.toml" || bad "toolkit sync failed"
contains "dark theme prefers dark" "$(cat "$TK/gsettings.log")" "color-scheme prefer-dark"
contains "qt6ct keeps user keys" "$(cat "$TK/.config/qt6ct/qt6ct.conf")" "custom_key=keep"
[ "$(grep -c '^style=' "$TK/.config/qt6ct/qt6ct.conf")" = 1 ] && ok || bad "qt6ct style key duplicated"
contains "XWayland cursor" "$(cat "$TK/.icons/default/index.theme")" "Inherits="
[ "$(grep -c "^active_colors" "$TK/.config/qt5ct/colors/iram.conf")" = 1 ] && ok || bad "qt5ct scheme malformed"

# ---- Snapshots ------------------------------------------------------------------
H="$WORK/home"; mkdir -p "$H/.config/hypr" "$H/.config/systemd/user" "$H/.config/waybar"
echo original > "$H/.config/hypr/hyprland.conf"
echo unit > "$H/.config/systemd/user/a.service"
snap() { HOME="$H" XDG_DATA_HOME="$H/.local/share" HYPRLAND_INSTANCE_SIGNATURE="" iram-snapshot "$@"; }
check "snapshot create" 0 snap create base
SNAPDIR="$H/.local/share/iram-os/snapshots"
ARCHIVE="$(ls "$SNAPDIR"/*base*.tar.*)"
contains "systemd units are archived" "$(tar -tf "$ARCHIVE")" ".config/systemd/user/a.service"
[ -z "$(find "$SNAPDIR" -name '.creating-*')" ] && ok || bad "temp files left behind"
[ "$(stat -c %a "$ARCHIVE")" = 600 ] && ok || bad "archive not private"
echo changed > "$H/.config/hypr/hyprland.conf"
echo stray > "$H/.config/hypr/added-later.conf"
check "snapshot restore" 0 snap restore base
contains "restore brings content back" "$(cat "$H/.config/hypr/hyprland.conf")" "original"
[ ! -e "$H/.config/hypr/added-later.conf" ] && ok || bad "restore merged instead of replacing"
check "safety snapshot taken" 0 ls "$SNAPDIR"/*pre-restore-safety*.tar.*
[ -z "$(find "$H" -maxdepth 1 -name '.iram-restore-*')" ] && ok || bad "staging dir left behind"
ORIGINAL_LABEL="$(snap list --json | jq -r '.[0].label')"
check "metadata is JSON" 0 test -n "$ORIGINAL_LABEL"
check "hostile label stays valid" 0 snap create 'a"b$(touch /tmp/x);c/../d'
check "metadata survives label" 0 bash -c "HOME='$H' XDG_DATA_HOME='$H/.local/share' iram-snapshot list --json | jq -e 'length > 0'"

# Malicious archives are refused and change nothing
EVIL="$WORK/evil"; mkdir -p "$EVIL/.ssh" "$EVIL/.config/hypr"
echo pwned > "$EVIL/.ssh/authorized_keys"
tar -C "$EVIL" --zstd -cf "$SNAPDIR/iram_snapshot_20000101_000000_evil1.tar.zst" .ssh
check "archive with a path outside the targets is refused" 1 snap restore evil1
[ ! -e "$H/.ssh/authorized_keys" ] && ok || bad "evil archive escaped"
ln -s /etc "$EVIL/.config/hypr/escape"
tar -C "$EVIL" --zstd -cf "$SNAPDIR/iram_snapshot_20000101_000000_evil2.tar.zst" .config/hypr
check "archive with an escaping symlink is refused" 1 snap restore evil2

# ---- User setup: upgrades keep user edits ---------------------------------------
H2="$WORK/home2"; mkdir -p "$H2/.config/waybar" "$H2/.config/hypr"
echo "my old waybar" > "$H2/.config/waybar/config.jsonc"
setup() { HOME="$H2" bash "$REPO/bin/iram-user-setup" --source "$REPO"; }
check "first setup" 0 setup
BACKUP="$(ls -d "$H2"/.config/iram/backups/backup_* | head -n 1)"
contains "pre-existing config is backed up" "$(cat "$BACKUP/waybar/config.jsonc")" "my old waybar"
for inc in monitors.conf webapps.conf theme.conf gpu.conf user-overrides.conf; do
    [ -e "$H2/.config/hypr/$inc" ] && ok || bad "hyprland.conf include missing: $inc"
done
echo "# mine" >> "$H2/.config/hypr/user-overrides.conf"
echo "# mine" >> "$H2/.config/hypr/hyprland.conf"
check "upgrade setup" 0 setup
contains "user-overrides survives upgrade" "$(cat "$H2/.config/hypr/user-overrides.conf")" "# mine"
contains "edited shipped config survives upgrade" "$(cat "$H2/.config/hypr/hyprland.conf")" "# mine"
check "new version offered beside the edit" 0 test -f "$H2/.config/hypr/hyprland.conf.iram-new"
lacks "MCP config has no placeholder" "$(cat "$H2/.config/mcp/iram_mcp_config.json")" "__PROJECTS_DIR__"
check "second run keeps a single rc line" 0 test "$(grep -c shell-init "$H2/.bashrc")" = 1
check "bashrc integration parses" 0 bash -n "$H2/.config/iram/shell-init.sh"

# ---- Disk installer: refuses before touching anything ----------------------------
PLAN="$(iram-install-disk --plan --disk /dev/nvme0n1 --user alice 2>&1)"
contains "nvme partition naming" "$PLAN" "mkfs.ext4 -F -L iram-root /dev/nvme0n1p3"
contains "live sudoers removed" "$PLAN" "rm -f /etc/sudoers.d/iram"
contains "autologin removed" "$PLAN" "system/greetd/config.toml /etc/greetd/config.toml"
if grep -q initial_session "$REPO/system/greetd/config.toml"; then bad "installed greetd config must not autologin"; else ok; fi
check "live greetd config autologins" 0 grep -q initial_session "$REPO/system/greetd/live.toml"
if grep -nE 'sudo cp -a( |$)' "$REPO/install.sh" | grep -v no-preserve=ownership | grep -q .; then bad "sudo cp -a keeps the user as owner"; else ok; fi
contains "live user removed" "$PLAN" "userdel --force --remove iram"
contains "casper purged" "$PLAN" "purge -y casper"
contains "machine-id reset" "$PLAN" "truncate -s 0 /etc/machine-id"
contains "BIOS bootloader" "$PLAN" "--target=i386-pc /dev/nvme0n1"
contains "UEFI bootloader" "$PLAN" "--target=x86_64-efi"
lacks "password stays off argv" "$PLAN" "--password"
contains "sata partition naming" "$(iram-install-disk --plan --disk /dev/sda --user bob 2>&1)" "/dev/sda3"
check "reserved username refused" 1 iram-install-disk --plan --disk /dev/sda --user iram
check "bad username refused" 1 iram-install-disk --plan --disk /dev/sda --user 'a;b'
check "non-device path refused" 1 iram-install-disk --plan --disk /tmp/x --user bob
check "non-root real run refused" 1 iram-install-disk --disk /dev/sda --user bob

# ---- Shipped scripts ----------------------------------------------------------------
# install.sh and the .deb copy bin/ verbatim, so a link out of the repo ships dangling.
for link in "$REPO"/bin/*; do
    [ -L "$link" ] || continue
    case "$(readlink "$link")" in /*|../*) bad "$(basename "$link") links outside bin/: $(readlink "$link")" ;; *) ok ;; esac
done
H3="$WORK/h3"; mkdir -p "$H3"
check "harness2 launcher fails cleanly when absent" 1 env HOME="$H3" IRAM_HARNESS2_BIN= iram-harness2 task
printf '#!/bin/sh\necho "real:$*"\n' > "$WORK/fake-harness2"; chmod +x "$WORK/fake-harness2"
contains "harness2 launcher hands off" "$(HOME="$H3" IRAM_HARNESS2_BIN="$WORK/fake-harness2" iram-harness2 task 2>&1)" "real:task"
check "harness2 launcher never execs itself" 1 env HOME="$H3" IRAM_HARNESS2_BIN="$REPO/bin/iram-harness2" timeout 5 iram-harness2 task

# ---- Battery monitor --------------------------------------------------------------
B="$WORK/sys"; mkdir -p "$B/class/power_supply/BAT0" "$WORK/fake"
printf '#!/bin/sh\necho "$@" >> "%s/calls"\n' "$WORK" > "$WORK/fake/notify-send"; chmod +x "$WORK/fake/notify-send"
cp "$WORK/fake/notify-send" "$WORK/fake/iram-lifecycle-dispatch"
batt() { echo "$1" > "$B/class/power_supply/BAT0/capacity"; echo "$2" > "$B/class/power_supply/BAT0/status"; PATH="$WORK/fake:$PATH" IRAM_SYS_ROOT="$B" IRAM_STATE="$WORK/level" iram-battery-monitor; }
contains "low fires" "$(batt 18 Discharging)" "low 18"
[ -z "$(batt 17 Discharging)" ] && ok || bad "low repeated"
contains "critical fires" "$(batt 9 Discharging)" "critical 9"
contains "hook received capacity" "$(cat "$WORK/calls")" "battery-low 18"
batt 50 Charging >/dev/null
contains "re-arms after charging" "$(batt 18 Discharging)" "low 18"
check "no battery is quiet" 0 env IRAM_SYS_ROOT="$WORK/none" IRAM_STATE="$WORK/l2" iram-battery-monitor

# ---- AI tuning --------------------------------------------------------------------
mem() { printf 'MemTotal: %s kB\n' "$1" > "$WORK/meminfo"; }
A="$WORK/aisys"; mkdir -p "$A/class/drm/card0/device"
echo $((12 * 1024 * 1024 * 1024)) > "$A/class/drm/card0/device/mem_info_vram_total"
mem 16000000
OUT="$(iram-ai-tune --dry-run --sys-root "$A" --meminfo "$WORK/meminfo")"
contains "AMD VRAM detected" "$OUT" '"gpu": "amd"'
contains "tier from VRAM" "$OUT" '"basis": "vram"'
echo $((512 * 1024 * 1024)) > "$A/class/drm/card0/device/mem_info_vram_total"
contains "APU carve-out uses RAM" "$(iram-ai-tune --dry-run --sys-root "$A" --meminfo "$WORK/meminfo")" '"basis": "ram"'

# ---- Offline fallback -------------------------------------------------------------
F="$WORK/ai-bin"; mkdir -p "$F"
printf '#!/bin/sh\nexit 0\n' > "$F/claude"; chmod +x "$F/claude"
contains "forced provider wins" "$(PATH="$F:$PATH" IRAM_AI_PROVIDER=ollama iram-ai-launch --which)" "ollama"

# ---- Static checks ----------------------------------------------------------------
for f in "$REPO"/bin/* "$REPO"/build/*.sh "$REPO"/install.sh "$REPO"/migrations/*.sh; do
    [ -f "$f" ] || continue
    case "$(head -n 1 "$f")" in
        *python*) python3 -c 'import ast,sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$f" || bad "python syntax: $f" ;;
        *sh*) bash -n "$f" || bad "bash syntax: $f" ;;
    esac
done
ok
check "waybar config is JSON" 0 jq empty "$REPO/config/waybar/config.jsonc"
check "swaync config is JSON" 0 jq empty "$REPO/config/swaync/config.json"
check "MCP config is JSON" 0 jq empty "$REPO/config/mcp/iram_mcp_config.json"
check "installer dry-run" 0 env HOME="$WORK/dry" bash "$REPO/install.sh" --dry-run
# ---- Login screen ----------------------------------------------------------------
check "login sudoers is valid" 0 bash -c "! command -v visudo >/dev/null || visudo -cf '$REPO/system/sudoers.d/iram-login-theme'"
LT="$WORK/login"; mkdir -p "$LT/themes" "$LT/sddm"; cp -r "$REPO/themes/tokyo-storm" "$LT/themes/"
sync_login() { IRAM_THEMES_ROOT="$LT/themes" IRAM_SDDM_THEME_DIR="$LT/sddm" iram-sddm-theme-sync "$@"; }
check "login theme sync" 0 sync_login tokyo-storm
contains "login accent from theme" "$(cat "$LT/sddm/theme.conf.user")" "accent=#7aa2f7"
contains "login wallpaper from theme" "$(cat "$LT/sddm/theme.conf.user")" "/tokyo-storm/backgrounds/"
for bad in ../tokyo-storm Tokyo -rf 'a/../b' nosuch ''; do check "login sync refuses theme '$bad'" 1 sync_login "$bad"; done
for bad in ../../etc/shadow 'x/../a.png' .hidden.png a.sh; do check "login sync refuses wallpaper '$bad'" 1 sync_login tokyo-storm "$bad"; done
mkdir -p "$LT/themes/evil/backgrounds"; cp "$REPO/themes/tokyo-storm/colors.toml" "$LT/themes/evil/"
ln -s /etc/hostname "$LT/themes/evil/backgrounds/a.png"
check "login sync refuses a symlink out of the themes" 1 sync_login evil a.png
check "login sync refuses extra arguments" 1 sync_login tokyo-storm a.png extra
PREVIEW_STATUS=0
python3 "$REPO/tests/sddm_preview.py" > "$WORK/sddm-preview.log" 2>&1 || PREVIEW_STATUS=$?
case "$PREVIEW_STATUS" in
    0|77) ok ;;
    *) bad "login screen QML: $(cat "$WORK/sddm-preview.log")" ;;
esac

check "doctor reports failed units" 0 grep -q 'is-failed' "$REPO/bin/iram-doctor"
check "installer starts units inside a session" 0 grep -q 'start --no-block "${ENABLE_UNITS' "$REPO/install.sh"
[ ! -e "$WORK/dry/.config" ] && ok || bad "dry-run wrote to HOME"

# Hyprland config lines must not start what systemd already manages
EXEC_ONCE="$(grep '^exec-once' "$REPO/config/hypr/hyprland.conf")"
for daemon in swaybg 'wl-paste' waybar mako polkit; do
    lacks "exec-once duplicates a unit" "$EXEC_ONCE" "$daemon"
done

# Every unit passes systemd's own verifier, in a HOME with no other units installed.
if command -v systemd-analyze >/dev/null 2>&1; then
    U="$WORK/unit-home/.config/systemd/user"; mkdir -p "$U"
    cp "$REPO"/config/systemd/user/* "$U/"
    VERIFY="$(HOME="$WORK/unit-home" XDG_CONFIG_HOME="$WORK/unit-home/.config" systemd-analyze --user verify "$U"/*.service "$U"/*.timer "$U"/*.socket "$U"/*.target 2>&1 | grep -vE 'is not executable|Command .* not found|WorkingDirectory|Failed to create|Two services allocated|Failed to put bus|failed to load properly' || true)"
    if [ -z "$VERIFY" ]; then ok; else bad "systemd-analyze: $VERIFY"; fi
    grep -q 'After=graphical-session' "$U"/*.timer && bad "a timer orders after graphical-session.target (cycle risk)" || ok
fi

echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]
