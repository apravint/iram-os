#!/usr/bin/env python3
"""
IRAM OS end-to-end install test. Needs KVM, qemu-system-x86_64, qemu-img and OVMF.

Boots the ISO in a VM, checks the live session, runs iram-install-disk against a
throwaway qcow2 disk that exists only inside the VM, then boots that disk under
UEFI and BIOS and checks that the installed system is clean.

Usage: vm-install-test.py <iso> --out <results-dir> [--memory 4G]
Writes results.json, a serial log and screenshots. Exits 1 if a required check fails.
The live desktop check is advisory, since it depends on the host's software GL.
"""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

LIVE_PASSWORD = "iram"
USER = "tester"
HOSTNAME = "testbox"
PASSWORD = "Tester-Pass-1"
# systemd tags shells with OSC 3008 sequences, which would pollute captured output.
OSC_SEQUENCE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
SHELL_PROMPT = re.compile(rb"[$#] *$")
OVMF_CODE = ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_CODE.fd")
OVMF_VARS = ("/usr/share/OVMF/OVMF_VARS_4M.fd", "/usr/share/OVMF/OVMF_VARS.fd")


def first_existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    raise SystemExit(f"None of these exist: {paths}")


class Results:
    def __init__(self):
        self.checks = []

    def record(self, stage, name, passed, detail="", required=True):
        self.checks.append({"stage": stage, "check": name, "passed": bool(passed), "required": required, "detail": detail[:600]})
        mark = "PASS" if passed else ("FAIL" if required else "WARN")
        print(f"[{mark}] {stage}: {name}" + (f" -- {detail[:200]}" if detail and not passed else ""), flush=True)

    def failed(self):
        return [c for c in self.checks if c["required"] and not c["passed"]]


class VM:
    """A QEMU guest driven over its serial console."""

    def __init__(self, name, disk, out_dir, memory, uefi_vars=None, iso=None):
        self.name = name
        self.out_dir = out_dir
        self.monitor_path = os.path.join(tempfile.mkdtemp(), "monitor.sock")
        self.log = open(os.path.join(out_dir, f"serial-{name}.log"), "wb")
        self.buffer = bytearray()
        self.lock = threading.Lock()
        self.token = 0
        cmd = [
            "qemu-system-x86_64", "-enable-kvm", "-machine", "q35", "-cpu", "host", "-m", memory, "-smp", "2",
            "-vga", "virtio", "-display", "none", "-serial", "stdio",
            "-monitor", f"unix:{self.monitor_path},server,nowait", "-no-reboot",
            "-drive", f"file={disk},if=virtio,format=qcow2",
        ]
        if uefi_vars:
            cmd += ["-drive", f"if=pflash,format=raw,readonly=on,file={first_existing(OVMF_CODE)}",
                    "-drive", f"if=pflash,format=raw,file={uefi_vars}"]
        if iso:
            cmd += ["-cdrom", iso, "-boot", "d"]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            chunk = self.proc.stdout.read1(65536)
            if not chunk:
                return
            self.log.write(chunk)
            self.log.flush()
            with self.lock:
                self.buffer += chunk

    def send(self, text):
        self.proc.stdin.write(text.encode())
        self.proc.stdin.flush()

    def login(self, user, password, timeout=300):
        """Answers login prompts until a shell is ready. Raises TimeoutError otherwise."""
        deadline = time.time() + timeout
        next_nudge = 0
        with self.lock:
            self.buffer.clear()
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise TimeoutError(f"VM exited with {self.proc.returncode} before login")
            with self.lock:
                tail = bytes(self.buffer[-300:]).rstrip(b"\r\n ") + b" "
            if re.search(rb"login: *$", tail):
                with self.lock:
                    self.buffer.clear()
                self.send(user + "\n")
            elif re.search(rb"[Pp]assword: *$", tail):
                with self.lock:
                    self.buffer.clear()
                self.send(password + "\n")
            elif SHELL_PROMPT.search(tail) and b"@" in tail:
                self.send("export TERM=dumb PS1='$ ' SYSTEMD_PAGER=cat PAGER=cat; stty cols 200\n")
                time.sleep(1)
                return
            elif time.time() > next_nudge:
                self.send("\n")
                next_nudge = time.time() + 5
            time.sleep(0.5)
        raise TimeoutError(f"No shell within {timeout}s as {user}")

    def run(self, command, timeout=60):
        """Returns (exit code, output). The marker is split on the command line, so
        the terminal's echo of the command can never look like its completion."""
        self.token += 1
        marker = f"__IRAM_DONE_{self.token}__"
        split = f"__IRAM_DO''NE_{self.token}__"
        with self.lock:
            self.buffer.clear()
        self.send(f"{command}; echo {split}$?\n")
        pattern = re.compile(re.escape(marker).encode() + rb"(\d+)")
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                data = bytes(self.buffer)
            match = pattern.search(data)
            if match:
                text = OSC_SEQUENCE.sub("", data[:match.start()].decode(errors="replace")).replace("\r", "")
                lines = text.split("\n")[1:]
                return int(match.group(1)), "\n".join(lines).strip()
            if self.proc.poll() is not None:
                return -1, "VM exited"
            time.sleep(0.25)
        return -2, f"Timed out after {timeout}s: " + bytes(self.buffer[-500:]).decode(errors="replace")

    def screenshot(self, name):
        path = os.path.join(self.out_dir, f"{name}.ppm")
        with socket.socket(socket.AF_UNIX) as sock:
            sock.connect(self.monitor_path)
            sock.sendall(f"screendump {path}\n".encode())
            time.sleep(2)
        if shutil.which("convert") and os.path.exists(path):
            subprocess.run(["convert", path, path[:-4] + ".png"], check=False)
            os.unlink(path)

    def stop(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=20)
        self.log.close()


def expect_zero(results, vm, stage, name, command, required=True, timeout=60):
    code, out = vm.run(command, timeout=timeout)
    results.record(stage, name, code == 0, f"exit {code}: {out}", required)
    return out


def expect_nonzero(results, vm, stage, name, command):
    code, out = vm.run(command)
    results.record(stage, name, code > 0, f"exit {code}: {out}")


def test_live(results, vm):
    stage = "live"
    results.record(stage, "hostname is iram", vm.run("hostname")[1].endswith("iram"), vm.run("hostname")[1])
    expect_nonzero(results, vm, stage, "no stray ubuntu user", "getent passwd ubuntu")
    expect_zero(results, vm, stage, "iram user exists", "id iram")
    expect_zero(results, vm, stage, "live session has passwordless sudo", "sudo -n true")
    expect_zero(results, vm, stage, "session config is in home", "test -f ~/.config/hypr/hyprland.conf")
    expect_zero(results, vm, stage, "installer is on PATH", "command -v iram-install-disk")
    expect_zero(results, vm, stage, "boot brand is IRAM", "grep -q IRAM /etc/issue")
    expect_zero(results, vm, stage, "system files are root-owned",
                "test -z \"$(sudo find /usr/share/iram /usr/local/bin /etc/skel /etc/sudoers.d /etc/iram.conf ! -user root | head -n 5)\"")
    code, out = vm.run("sudo -n true 2>&1")
    results.record(stage, "sudo accepts every fragment", code == 0 and not out, out)

    # The desktop starts by autologin, on its own schedule.
    desktop = False
    for _ in range(36):
        if vm.run("pgrep -x Hyprland || pgrep -f start-hyprland")[0] == 0:
            desktop = True
            break
        time.sleep(5)
    results.record(stage, "Hyprland started by autologin", desktop, vm.run("journalctl -b -u greetd --no-pager -n 20")[1])
    time.sleep(25)
    if desktop:
        out = vm.run("XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user list-units --no-pager --plain --no-legend 'waybar*' 'swaync*' 'swaybg*' 'hypridle*' 'hyprland-session*'")[1]
        results.record(stage, "session units running", "waybar.service" in out and "running" in out, out)
        themed = False
        for _ in range(30):
            if vm.run("test -s ~/.local/state/iram/current/theme.name && test -e ~/.local/state/iram/current/background && pgrep -x swaybg")[0] == 0:
                themed = True
                break
            time.sleep(5)
        results.record(stage, "first login gets a theme and wallpaper", themed, vm.run("cat ~/.local/state/iram/first-theme.log; pgrep -a iram; ls ~/.local/state/iram/current")[1])
        time.sleep(5)
    vm.screenshot("live-desktop")
    with open(os.path.join(vm.out_dir, "live-diagnostics.txt"), "w") as f:
        for cmd in ("lsblk -f", "findmnt", "sudo journalctl -b -u greetd --no-pager -n 60", "tail -n 60 /run/user/$(id -u)/hypr/*/hyprland.log", "sudo cat /etc/greetd/config.toml", "cat ~/.local/state/iram/first-theme.log", "XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user --failed --no-pager", "XDG_RUNTIME_DIR=/run/user/$(id -u) journalctl --user -b --no-pager -n 40"):
            f.write(f"$ {cmd}\n{vm.run(cmd, timeout=30)[1]}\n\n")
    return vm.run("cat /etc/machine-id")[1].strip()


def test_install(results, vm):
    stage = "install"
    vm.run(f"printf '%s\\n' '{PASSWORD}' > /tmp/pw")
    expect_nonzero(results, vm, stage, "refuses a wrong erase confirmation",
                   f"sudo iram-install-disk --disk /dev/vda --user {USER} --password-file /tmp/pw --yes-erase-disk /dev/vdb < /dev/null")
    expect_nonzero(results, vm, stage, "refuses the live media",
                   f"sudo iram-install-disk --disk /dev/sr0 --user {USER} --password-file /tmp/pw --yes-erase-disk /dev/sr0")
    expect_zero(results, vm, stage, "virtual disk untouched by refusals", "! lsblk -n /dev/vda | grep -q part")
    code, out = vm.run(f"sudo iram-install-disk --disk /dev/vda --user {USER} --hostname {HOSTNAME} --timezone Asia/Kolkata --password-file /tmp/pw --yes-erase-disk /dev/vda > /tmp/install.log 2>&1", timeout=1500)
    tail = vm.run("tail -n 40 /tmp/install.log")[1]
    with open(os.path.join(vm.out_dir, "install.log"), "w") as f:
        f.write(vm.run("sed 's/.*\\r//' /tmp/install.log | grep -v '^\\[' | tail -n 400", timeout=30)[1])
    results.record(stage, "iram-install-disk succeeds", code == 0, f"exit {code}: {tail}")
    if code != 0:
        return False

    expect_zero(results, vm, stage, "nothing left mounted", "! findmnt /mnt/iram-target")
    # The installer rightly configures no serial console, so the test adds one.
    # This symlink and GRUB's console setting are the only changes to what was installed.
    prepare = (
        "sudo mount /dev/vda3 /mnt && "
        "sudo mkdir -p /mnt/etc/systemd/system/getty.target.wants && "
        "sudo ln -sf /usr/lib/systemd/system/serial-getty@.service /mnt/etc/systemd/system/getty.target.wants/serial-getty@ttyS0.service && "
        "sudo sed -i 's/ ro / ro console=ttyS0,115200 /' /mnt/boot/grub/grub.cfg && "
        "sudo umount /mnt && sync"
    )
    expect_zero(results, vm, stage, "test harness added a serial console", prepare)
    return True


def test_installed(results, vm, stage, live_machine_id):
    expect_zero(results, vm, stage, "password login reached a shell", "id -un")
    results.record(stage, f"hostname is {HOSTNAME}", vm.run("hostname")[1].endswith(HOSTNAME), vm.run("hostname")[1])
    expect_nonzero(results, vm, stage, "passwordless sudo refused", "sudo -n true")
    expect_zero(results, vm, stage, "sudo works with the password", f"printf '%s\\n' '{PASSWORD}' | sudo -S -p '' true")
    expect_nonzero(results, vm, stage, "iram user removed", "getent passwd iram")
    expect_nonzero(results, vm, stage, "no iram home", "test -e /home/iram")
    for path in ("/etc/sudoers.d/iram", "/etc/sudoers.d/casper", "/etc/casper.conf"):
        expect_nonzero(results, vm, stage, f"{path} removed", f"test -e {path}")
    expect_nonzero(results, vm, stage, "casper purged", "dpkg-query -W -f='${Status}' casper | grep -q 'install ok installed'")
    machine_id = vm.run("cat /etc/machine-id")[1].strip()
    results.record(stage, "fresh machine-id", bool(re.fullmatch(r"[0-9a-f]{32}", machine_id)) and machine_id != live_machine_id, f"live {live_machine_id}, installed {machine_id}")
    expect_zero(results, vm, stage, "fstab uses UUIDs", "grep -q '^UUID=.* / ' /etc/fstab && grep -q '^UUID=.*/boot/efi' /etc/fstab")
    expect_zero(results, vm, stage, "root is the installed disk", "findmnt -no SOURCE / | grep -q /dev/vda3")
    expect_zero(results, vm, stage, "EFI partition mounted", "findmnt /boot/efi")
    expect_zero(results, vm, stage, "user has the desktop config", "test -f ~/.config/hypr/hyprland.conf && test -f ~/.config/systemd/user/hyprland-session.target")
    expect_nonzero(results, vm, stage, "MCP config placeholder resolved", "grep -q __PROJECTS_DIR__ ~/.config/mcp/iram_mcp_config.json")
    expect_zero(results, vm, stage, "timezone applied", "readlink /etc/localtime | grep -q Asia/Kolkata")
    expect_zero(results, vm, stage, "login screen running", "systemctl is-active greetd && pgrep -x tuigreet")
    expect_nonzero(results, vm, stage, "autologin removed", "grep -q initial_session /etc/greetd/config.toml")
    code, out = vm.run("systemctl --failed --no-legend --plain --no-pager")
    results.record(stage, "no failed system units", code == 0 and not out, out, required=False)
    with open(os.path.join(vm.out_dir, f"{stage}-diagnostics.txt"), "w") as f:
        for cmd in ("lsblk -f", "systemd-analyze", "cat /etc/os-release", "df -h /", "dpkg-query -l | wc -l"):
            f.write(f"$ {cmd}\n{vm.run(cmd, timeout=30)[1]}\n\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("iso")
    parser.add_argument("--out", required=True)
    parser.add_argument("--memory", default="4G")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    out_dir = os.path.abspath(args.out)
    work = tempfile.mkdtemp(prefix="iram-vm-test-")
    disk = os.path.join(work, "disk.qcow2")
    uefi_vars = os.path.join(work, "OVMF_VARS.fd")
    subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", disk, "30G"], check=True)
    shutil.copy(first_existing(OVMF_VARS), uefi_vars)

    results = Results()
    live_machine_id = ""
    installed = False
    try:
        vm = VM("live", disk, out_dir, args.memory, uefi_vars, os.path.abspath(args.iso))
        try:
            vm.login("iram", LIVE_PASSWORD)
            results.record("live", "serial login", True)
            live_machine_id = test_live(results, vm)
            installed = test_install(results, vm)
        except TimeoutError as e:
            results.record("live", "serial login", False, str(e))
        finally:
            vm.stop()

        if installed:
            for stage, boot_vars in (("installed-uefi", uefi_vars), ("installed-bios", None)):
                vm = VM(stage, disk, out_dir, args.memory, boot_vars)
                try:
                    vm.login(USER, PASSWORD)
                    results.record(stage, "boots to a login", True)
                    test_installed(results, vm, stage, live_machine_id)
                    time.sleep(10)
                    vm.screenshot(stage)
                except TimeoutError as e:
                    results.record(stage, "boots to a login", False, str(e))
                finally:
                    vm.stop()
    finally:
        with open(os.path.join(out_dir, "results.json"), "w") as f:
            json.dump(results.checks, f, indent=2)
        shutil.rmtree(work, ignore_errors=True)

    failed = results.failed()
    print(f"\n{len(results.checks) - len(failed)}/{len(results.checks)} checks passed.")
    for check in failed:
        print(f"FAILED {check['stage']}: {check['check']}: {check['detail']}")
    return 1 if failed or not results.checks else 0


if __name__ == "__main__":
    sys.exit(main())
