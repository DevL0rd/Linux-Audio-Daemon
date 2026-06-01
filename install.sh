#!/bin/bash
set -e

REPO_DIR=$(pwd)
if [ ! -f "$REPO_DIR/daemon.py" ]; then
    echo "Please run this script from the repository directory."
    exit 1
fi

echo "Setting up udev rules for ASUS ROG devices..."
# Grant read access to anyone in the 'users' group (which includes your standard user)
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0b05", ATTRS{idProduct}=="1afa", GROUP="users", MODE="0664"' | sudo tee /etc/udev/rules.d/99-rog-headset.rules > /dev/null

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Setting up systemd user service..."
mkdir -p ~/.config/systemd/user

cat <<EOF > ~/.config/systemd/user/headset-manager.service
[Unit]
Description=Headset Auto Switcher Daemon
After=pipewire.service wireplumber.service

[Service]
Type=simple
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/python3 $REPO_DIR/daemon.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now headset-manager.service

echo ""
echo "Done! The service is now running in the background as your local user."
echo "Because it is linked directly to $REPO_DIR, running 'git pull' in the future"
echo "will instantly update the script (just run 'systemctl --user restart headset-manager' after pulling)."
echo ""
echo "You can view the live logs by running:"
echo "journalctl --user -u headset-manager.service -f"
