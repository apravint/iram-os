export IRAM_PATH=/usr/share/iram

# Source IRAM OS Developer Shell Suite
if [ -f "$HOME/iram-os/config/shell/functions.sh" ]; then
    source "$HOME/iram-os/config/shell/functions.sh"
elif [ -f "/usr/share/iram/config/shell/functions.sh" ]; then
    source "/usr/share/iram/config/shell/functions.sh"
fi
