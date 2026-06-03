#!/bin/bash
set -e

echo "Stopping and disabling systemd user service..."
systemctl --user disable --now smart-audio-manager.service 2>/dev/null || true

echo "Removing service file..."
rm -f ~/.config/systemd/user/smart-audio-manager.service
systemctl --user daemon-reload

echo "Removing udev rules (requires sudo access)..."
if [ -f /etc/udev/rules.d/99-rog-headset.rules ]; then
    sudo rm -f /etc/udev/rules.d/99-rog-headset.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

echo "Uninstallation complete!"
