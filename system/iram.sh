export IRAM_PATH=/usr/share/iram

# Virtual Machine Acceleration & Cursor Compatibility
VIRT=$(systemd-detect-virt 2>/dev/null || echo "none")
if [ "$VIRT" != "none" ]; then
    export WLR_NO_HARDWARE_CURSORS=1
    export LIBVA_DRIVER_NAME=sw
fi

# Source IRAM OS Developer Shell Suite
if [ -f "$HOME/iram-os/config/shell/functions.sh" ]; then
    source "$HOME/iram-os/config/shell/functions.sh"
elif [ -f "/usr/share/iram/config/shell/functions.sh" ]; then
    source "/usr/share/iram/config/shell/functions.sh"
fi
